import difflib
import os
import json
import requests
from dotenv import load_dotenv
import subprocess
from fuzzywuzzy import fuzz

# Load image data from fetched_content.json
with open("pipeline_1_product_to_stories/fetched_content.json", "r") as f:
    fetched_data = json.load(f)

# Extract image list safely
images = fetched_data.get("images", [])

# Print available captions for debugging
for image in images:
    if not isinstance(image, dict):
        print(f"⚠️ Skipping non-dict image entry: {image}")
        continue
    caption = image.get("caption", "")
    print(f"🔍 Available image caption: {caption}")

load_dotenv()

def convert_markdown_to_adf(markdown_text):
    result = subprocess.run(
        ['node', 'utils/markdown_to_adf.js'],
        input=markdown_text.encode('utf-8'),
        capture_output=True,
        check=True
    )
    return json.loads(result.stdout)

JIRA_URL = os.getenv("CONFLUENCE_BASE_URL").replace("/wiki", "")  # optional cleanup
JIRA_EMAIL = os.getenv("CONFLUENCE_EMAIL")
JIRA_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
PROJECT_KEY = "SCRUM"
ISSUE_TYPE = "Story"

HEADERS = {
    "Content-Type": "application/json"
}

auth = (JIRA_EMAIL, JIRA_API_TOKEN)

def format_adf_description(text):
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": line}]
            } for line in text.strip().split("\n")
        ]
    }

def create_issue(summary, description, labels):
    url = f"{JIRA_URL}/rest/api/3/issue"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    # The confluence_url will be injected in main() via a closure or partial, so here just accept an extra kwarg
    # We'll add a confluence_url field to the payload if provided
    import inspect
    frame = inspect.currentframe().f_back
    story = frame.f_locals.get("story", {})

    # Fetch available fields for the issue creation screen
    print("🔎 Fetching createmeta for available fields...")
    createmeta_url = f"{JIRA_URL}/rest/api/3/issue/createmeta?projectKeys={PROJECT_KEY}&issuetypeNames=Story&expand=projects.issuetypes.fields"
    resp = requests.get(createmeta_url, auth=(JIRA_EMAIL, JIRA_API_TOKEN))
    if resp.status_code != 200:
        print(f"❌ Failed to fetch createmeta: {resp.status_code} {resp.text}")
        fields_meta = {}
    else:
        fields_meta = resp.json()["projects"][0]["issuetypes"][0]["fields"]
        print("📋 Available fields for issue creation:")
        for field_id, field_info in fields_meta.items():
            print(f" - {field_id}: {field_info.get('name')}")

    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "issuetype": {"name": ISSUE_TYPE},
            "labels": labels,
            "description": convert_markdown_to_adf(description),
        }
    }
    # Conditionally add Confluence content field if available
    if "customfield_10244" in fields_meta:
        payload["fields"]["customfield_10244"] = story.get("confluence_url", "")
        print("🔗 Added Confluence URL to 'customfield_10244'")
    else:
        print("⚠️ customfield_10244 not available on the Create screen; skipping.")

    print(f"DEBUG SUMMARY: {summary}")
    print(f"DEBUG LABELS: {labels}")
    print(f"DEBUG DESCRIPTION: {description[:100]}...")  # Show only the first 100 characters
    print(f"🔗 Confluence source: {story.get('confluence_url', '') if story else 'N/A'}")
    response = requests.post(url, json=payload, headers=headers, auth=auth)
    if response.status_code >= 400:
        print("❌ Jira Error Response:", response.text)
    response.raise_for_status()
    return response.json()["key"]

def attach_files(issue_key, attachment_urls):
    for url in attachment_urls:
        img_data = requests.get(url).content
        filename = url.split("/")[-1]
        files = {
            "file": (filename, img_data, "application/octet-stream")
        }
        attach_headers = {
            "X-Atlassian-Token": "no-check"
        }
        response = requests.post(
            f"{JIRA_URL}/rest/api/3/issue/{issue_key}/attachments",
            headers={**HEADERS, **attach_headers},
            auth=auth,
            files=files
        )
        response.raise_for_status()

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    stories_path = os.path.join(project_root, "pipeline_1_product_to_stories", "generated_stories.json")

    with open(stories_path, "r") as f:
        data = json.load(f)
        stories = data.get("stories", [])
        if not stories:
            raise ValueError("No stories found in generated_stories.json")

    for story in stories:
        summary = story.get("title", "Untitled Story")
        labels = story.get("platforms", [])
        description_parts = [story.get("description", "")]
        if "business_rules" in story:
            description_parts.append("### Business Rules\n" + "\n".join(f"- {r}" for r in story["business_rules"]))
        if "acceptance_criteria" in story:
            description_parts.append("### Acceptance Criteria\n" + "\n".join(f"- {c}" for c in story["acceptance_criteria"]))
        description = "\n\n---\n\n".join(description_parts)

        # Print the Confluence URL before sending the request
        print(f"🔗 Confluence source: {story.get('confluence_url', 'N/A')}")

        issue_key = create_issue(summary, description, labels)

        # Match and attach images based on caption similarity to summary
        # Build basic auth string for Jira
        import base64
        auth_string = base64.b64encode(
            f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode("utf-8")
        ).decode("utf-8")
        jira_url = JIRA_URL
        image_attached = False

        uploaded_filenames = set()

        best_match = None
        best_score = 0
        for image in images:
            if not isinstance(image, dict):
                print(f"⚠️ Skipping non-dict image entry: {image}")
                continue
            caption = image.get("caption", "")
            print(f"🔍 Available image caption: {caption}")
            if not caption:
                print(f"⚠️ Skipping image without caption: {image.get('filename', 'unknown')}")
                continue
            score = fuzz.partial_ratio(summary.lower(), caption.lower())
            print(f"📊 Fuzzy match score between summary '{summary}' and caption '{caption}': {score}")
            if score > best_score:
                best_score = score
                best_match = image

            if best_match and best_score >= 90:
                print(f"✅ Matched image '{best_match.get('filename')}' to story '{summary}' with score {best_score}")
                image = best_match

                if image['filename'] in uploaded_filenames:
                    print(f"⚠️ Skipping duplicate upload of image: {image['filename']}")
                    continue

                img_url = image.get("imgur_url", "")
                filename = image.get("filename", "")
                if img_url and filename:
                    try:
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                        }
                        response = requests.get(img_url, headers=headers, stream=True)
                        response.raise_for_status()
                        print(f"📥 Downloaded {filename} from {img_url}")
                        with open(filename, "wb") as img_file:
                            for chunk in response.iter_content(chunk_size=8192):
                                img_file.write(chunk)
                        with open(filename, "rb") as img_file:
                            files = {"file": (filename, img_file, "application/octet-stream")}
                            headers = {
                                "Authorization": f"Basic {auth_string}",
                                "X-Atlassian-Token": "no-check"
                            }
                            attach_url = f"{jira_url}/rest/api/3/issue/{issue_key}/attachments"
                            attach_response = requests.post(attach_url, headers=headers, files=files)
                            print(f"📎 Jira response status for attachment: {attach_response.status_code}")
                            print(f"📎 Jira response body: {attach_response.text}")
                            if attach_response.status_code == 200:
                                print(f"✅ Successfully attached image: {filename}")
                                image_attached = True
                                uploaded_filenames.add(image['filename'])
                            if attach_response.status_code != 200:
                                print(f"❌ Failed to attach image {filename}: {attach_response.status_code}")
                    except Exception as e:
                        print(f"⚠️ Error attaching image {filename}: {e}")
                    finally:
                        if os.path.exists(filename):
                            os.remove(filename)
            else:
                print(f"⚠️ No matching image found for story summary: '{summary}', best score was {best_score}")

        if not image_attached:
            print(f"⚠️ No matching image found for story summary: '{summary}'")

        if "attachments" in story and story["attachments"]:
            attach_files(issue_key, story["attachments"])

        print(f"✅ Created story {issue_key}")

if __name__ == "__main__":
    main()
