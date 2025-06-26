import os
import requests
import shutil
import subprocess
from dotenv import load_dotenv

load_dotenv()

CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_PAGE_ID = os.getenv("CONFLUENCE_PAGE_ID")

def fetch_confluence_page():
    page_url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{CONFLUENCE_PAGE_ID}?expand=body.storage,version"
    attachments_url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{CONFLUENCE_PAGE_ID}/child/attachment"
    auth = (CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)

    # Fetch page content
    page_response = requests.get(page_url, auth=auth)
    if page_response.status_code != 200:
        raise Exception(f"Failed to fetch page: {page_response.status_code} - {page_response.text}")
    page_data = page_response.json()

    title = page_data["title"].replace("/", "_")
    version = page_data["version"]["number"]
    content = page_data["body"]["storage"]["value"]

    # Prepare image folder
    image_folder = os.path.join("pipeline_1_product_to_stories", "public_images", title)
    os.makedirs(image_folder, exist_ok=True)

    # Fetch attachments and filter images
    attachments_response = requests.get(attachments_url, auth=auth)
    if attachments_response.status_code != 200:
        raise Exception(f"Failed to fetch attachments: {attachments_response.status_code} - {attachments_response.text}")
    attachments = attachments_response.json().get("results", [])

    image_metadata = []
    for att in attachments:
        if att["metadata"]["mediaType"].startswith("image/"):
            filename = att["title"]
            download_link = CONFLUENCE_BASE_URL + att["_links"]["download"]
            image_path = os.path.join(image_folder, filename)

            with requests.get(download_link, auth=auth, stream=True) as r:
                if r.status_code == 200:
                    with open(image_path, "wb") as f:
                        shutil.copyfileobj(r.raw, f)

            image_metadata.append({
                "filename": filename,
                "local_path": image_path,
                "download_url": download_link
            })

    return {
        "title": title,
        "version": version,
        "content": content,
        "images": image_metadata
    }

if __name__ == "__main__":
    data = fetch_confluence_page()
    print(f"\nTitle: {data['title']}")
    print(f"Version: {data['version']}")
    print(f"Images downloaded: {[img['filename'] for img in data['images']]}")
    print(f"\nContent Preview:\n{data['content'][:1000]}")

    # Set image folder path
    image_folder = os.path.join("pipeline_1_product_to_stories", "public_images")

    def auto_commit_and_push(image_folder_path):
        try:
            subprocess.run(["git", "add", image_folder_path], check=True)

            # Only commit if there are changes
            status_output = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if status_output.stdout.strip():
                subprocess.run(["git", "commit", "-m", "Auto-add Confluence images"], check=True)
                subprocess.run(["git", "push"], check=True)
            else:
                print("✅ No changes to commit.")
        except subprocess.CalledProcessError as e:
            print("❌ Git command failed:", e)

    auto_commit_and_push(image_folder)

    DELETE_AFTER_PUSH = True
    if DELETE_AFTER_PUSH:
        shutil.rmtree(image_folder)