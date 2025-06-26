import json
import codecs
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = OpenAI()

# Load the fetched Confluence content
with open("pipeline_1_product_to_stories/fetched_content.json", "r") as file:
    fetched_data = json.load(file)

# Build the prompt
title = fetched_data.get("title", "")
content_html = fetched_data.get("content", "")
images = fetched_data.get("images", [])

image_info = "\n".join(
    [f"- {img['caption']}: {img['imgur_url']}" for img in images]
)

prompt = (
    f"You are a senior product owner. Based on the following product description and image references, "
    f"generate a list of Agile user stories in JSON format with title, description, platforms, and acceptance criteria.\n\n"
    f"Title: {title}\n\n"
    f"Description:\n{content_html}\n\n"
    f"Design Assets:\n{image_info}\n\n"
    "Output JSON format:\n"
    "[\n"
    "  {\n"
    "    \"title\": \"...\",\n"
    "    \"description\": \"...\",\n"
    "    \"platforms\": [\"Web\", \"iOS\", \"Android\"],\n"
    "    \"acceptance_criteria\": [\"...\", \"...\"]\n"
    "  },\n"
    "  ...\n"
    "]"
)


# Send request to OpenAI
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are an expert at writing Agile user stories."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3
)

# Parse and save output
story_output = response.choices[0].message.content
print("DEBUG OpenAI Output:\n", repr(story_output))
import re
story_output_clean = re.sub(r"^```json\s*|\s*```$", "", story_output.strip(), flags=re.MULTILINE)
stories = json.loads(story_output_clean)

output_path = os.path.join(os.path.dirname(__file__), "generated_stories.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({"stories": stories}, f, indent=2, ensure_ascii=False)

print("✅ Stories generated and saved to generated_stories.json")
