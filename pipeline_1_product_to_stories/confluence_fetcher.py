import os
import requests
import shutil
import subprocess
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

def upload_to_imgur(image_path):
    client_id = os.getenv("IMGUR_CLIENT_ID")
    headers = {"Authorization": f"Client-ID {client_id}"}

    with open(image_path, "rb") as f:
        response = requests.post(
            "https://api.imgur.com/3/image",
            headers=headers,
            files={"image": f}
        )

    if response.status_code != 200:
        raise Exception(f"Imgur upload failed: {response.status_code} - {response.text}")

    return response.json()["data"]["link"]

def fetch_confluence_page():
    import re
    confluence_url = os.getenv("CONFLUENCE_URL")
    if not confluence_url:
        raise ValueError("❌ CONFLUENCE_URL not found. Please provide it as an environment variable.")
    match = re.search(r'/pages/(\d+)', confluence_url)
    if not match:
        raise ValueError("❌ Unable to extract page ID from the provided URL.")
    confluence_page_id = match.group(1)
    page_url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{confluence_page_id}?expand=body.storage,version"
    attachments_url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{confluence_page_id}/child/attachment"
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

            # Upload to Imgur
            imgur_url = upload_to_imgur(image_path)

            # Clean up local file
            os.remove(image_path)

            image_metadata.append({
                "filename": filename,
                "imgur_url": imgur_url
            })

    from bs4 import BeautifulSoup

    # Map filenames to captions from the Confluence HTML
    soup = BeautifulSoup(content, "html.parser")
    caption_map = {}

    # Case A: Captions inside <ac:image>
    for img_tag in soup.find_all("ac:image"):
        ri = img_tag.find("ri:attachment")
        if not ri:
            continue
        filename = ri.get("ri:filename")
        cap_tag = img_tag.find("ac:caption")
        if cap_tag:
            caption_map[filename] = cap_tag.get_text(strip=True)

    # Case B: Paragraph before <ac:image> (fallback)
    for p in soup.find_all("p"):
        next_sib = p.find_next_sibling()
        if next_sib and next_sib.name == "ac:image":
            ri = next_sib.find("ri:attachment")
            if ri:
                fn = ri.get("ri:filename")
                text = p.get_text(strip=True)
                if text:
                    caption_map.setdefault(fn, text)

    # Update image_metadata to include captions
    updated_image_metadata = []
    for img_meta in image_metadata:
        filename = img_meta["filename"]
        caption = caption_map.get(filename, "")
        updated_image_metadata.append({
            "filename": filename,
            "imgur_url": img_meta["imgur_url"],
            "caption": caption
        })

    return {
        "title": title,
        "version": version,
        "content": content,
        "images": updated_image_metadata
    }

import json

if __name__ == "__main__":
    data = fetch_confluence_page()
    print(f"\nTitle: {data['title']}")
    print(f"Version: {data['version']}")
    print("Images uploaded to Imgur:")
    for img in data['images']:
        print(f"  {img['filename']} → {img['imgur_url']}")

    output_path = os.path.join("pipeline_1_product_to_stories", "fetched_content.json")
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nContent Preview:\n{data['content'][:1000]}")
    print(f"\n✅ Saved structured content to {output_path}")