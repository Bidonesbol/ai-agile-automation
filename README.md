# AI-Powered Agile QA Automation Pipeline

A fully automated pipeline that transforms raw Confluence design documentation into structured Jira stories — complete with AI-generated summaries, acceptance criteria, business rules, and direct upload to Jira. Matching design images are also attached automatically.

---

## 🔍 Key Features

- **AI-Powered Story Generation**  
  Automatically extracts and summarizes Confluence documentation using GPT-based models to generate Agile stories with structured fields like summary, description, labels, and business rules.

- **Design Image Matching**  
  Screenshots or wireframes are matched to stories based on fuzzy similarity and captions, then attached to the respective Jira issues.

- **Confluence Traceability**  
  A custom field (“Confluence Content”) is populated in Jira with the full source input, ensuring traceability and validation compliance.

- **Full Jira Integration**  
  End-to-end integration with Jira’s API — stories are created, fields mapped, and media attached automatically.

- **Modular, Locally Executable Pipeline**  
  Developed for local testing and ready for cloud deployment. Easily portable, clean Python scripts, API-key controlled.

---

## 🚀 Workflow

1. **User Inputs Confluence Page URL**  
2. **Pipeline Fetches and Parses Content**  
3. **AI Generates Structured Jira Stories**  
4. **Stories Uploaded to Jira**  
5. **Images Matched and Attached (if available)**

A single script can trigger the full end-to-end pipeline.

---

## 💡 Why This Matters

This project automates one of the most time-consuming and error-prone steps in Agile delivery: turning unstructured feature documentation into fully structured Jira stories.

By combining Confluence content parsing, AI-driven story generation, and direct Jira API integration, the system ensures rapid, consistent, and traceable story creation — reducing manual effort while improving consistency and speed in Agile planning.

It supports faster iteration cycles, improves story quality from day one, and minimizes delays between design handoff and QA automation readiness. The architecture is modular and ready for both local and cloud execution, making it easy to scale across teams or adapt to custom workflows.

---

## 🧱 Tech Stack

- **Python 3.9+**
- **OpenAI GPT-4o**
- **Jira Cloud REST API**
- **Confluence API**
- **Flask (for future web interface)**
- **FuzzyWuzzy (image caption scoring)**

---

## 📁 Project Structure

```
pipeline_1_fetch_confluence/         # Script to fetch and clean Confluence content
pipeline_2_stories_to_jira/         # Story generation + Jira upload
  ├── upload_stories_to_jira.py
pipeline_3_run_full_pipeline/       # End-to-end orchestrator
  ├── run_full_pipeline.py
utils/                              # Shared tools and helpers
  ├── confluence_fetcher.py
  ├── ai_prompting.py
  ├── jira_api_helpers.py
images/                             # Uploaded and matched screenshots
env/                                # Local virtualenv
README.md
```

---

## 📌 Setup Instructions

1. Clone the repo:
   ```bash
   git clone https://github.com/Bidonesbol/ai-agile-automation.git
   cd ai-agile-automation
   ```

2. Set up your Python virtual environment:
   ```bash
   python3 -m venv env
   source env/bin/activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file with:
   ```
   OPENAI_API_KEY=
   CONFLUENCE_BASE_URL=
   CONFLUENCE_EMAIL=
   CONFLUENCE_API_TOKEN=
   JIRA_URL=
   JIRA_EMAIL=
   JIRA_API_TOKEN=
   PROJECT_KEY=
   ```

4. Run the full pipeline:
   ```bash
   python pipeline_3_run_full_pipeline/run_full_pipeline.py
   ```

---

## 🔭 Roadmap

- 🌐 Add public web UI with authentication and real-time log feedback
- ☁️ Cloud deployment via Render, Replit, or Railway

---

## 📣 Contributions

Currently maintained as a closed prototype, but contributions via issues or forks are welcome.
