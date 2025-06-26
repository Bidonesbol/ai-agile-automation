import subprocess
import os
import sys

def run_script(path, description):
    print(f"\n🚀 Running: {description}")
    result = subprocess.run([sys.executable, path], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"⚠️ Errors from {description}:\n{result.stderr}")

def main():
    print("🔄 Starting full end-to-end pipeline...\n")

    confluence_url = input("🔗 Enter the full Confluence page URL: ")
    os.environ["CONFLUENCE_URL"] = confluence_url

    # Step 1: Fetch from Confluence
    run_script(
        "pipeline_1_product_to_stories/confluence_fetcher.py",
        "Fetch content from Confluence"
    )

    # Step 2: Generate Stories using AI
    run_script(
        "pipeline_1_product_to_stories/generate_stories_from_confluence.py",
        "Generate stories from fetched content"
    )

    # Step 3: Upload Stories to Jira and Attach Images
    run_script(
        "pipeline_2_stories_to_jira/upload_stories_to_jira.py",
        "Upload stories to Jira and attach matching images"
    )

    print("\n✅ All steps completed.")

if __name__ == "__main__":
    main()