# InterviewMate AI — Compact College Mini Project

This starter website uses **Python Flask, HTML, CSS, JavaScript and SQLite**.

## Included features
- Resume upload: PDF/DOCX text extraction (text-based PDF and valid DOCX files)
- Optional job description and a keyword-overlap resume match estimate
- Technical, HR, Aptitude and Coding interviews
- MCQ quiz mode or Written/Voice mode
- Easy/Medium/Hard selection
- One question per screen, Previous/Next navigation
- Browser speech-to-text and question read-aloud when supported
- Answer scoring, feedback, correct MCQ option, suggested improvement
- Technical, communication and text-structure confidence indicators
- Areas to review and a simple practice/career roadmap
- Interview history, recent score trend and saved results in SQLite
- Optional OpenAI API integration for AI-generated questions and written-answer feedback
- If no API key exists, the app works with a built-in question bank and demo feedback

## Run it on Windows
1. Extract `AI_Interview_Compact.zip`.
2. Open the extracted `AI_Interview_Compact` folder in VS Code.
3. Select **Terminal → New Terminal**.
4. Recommended: create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

5. Install packages:

   ```powershell
   python -m pip install -r requirements.txt
   ```

6. Start the website:

   ```powershell
   python app.py
   ```

7. Open `http://127.0.0.1:5000` in Chrome. Keep the terminal open while using the site.

## Optional: enable real AI
Without an API key, built-in questions and demo feedback are used.
To enable AI question generation and written-answer feedback, create an API key with your chosen model provider and set it as an environment variable in the VS Code terminal **before** starting the app. For example, in PowerShell:

```powershell
$env:OPENAI_API_KEY="your-api-key-here"
python app.py
```

Optional model variable:

```powershell
$env:OPENAI_MODEL="gpt-4o-mini"
```

Do not share your API key or commit it to a public repository. With the AI option enabled, resume text/job description used during question generation and written answers sent for evaluation are sent to the configured AI provider. Obtain consent before using someone else's resume.

## Notes and limits
- Resume match score is a simple keyword overlap estimate, not a hiring decision.
- If using a scanned image-only PDF, text extraction may not work.
- Speech recognition varies by browser and may require microphone permission. Typing is always available.
- The confidence number is a text-structure estimate; the app does not measure real emotions or true confidence.
- The API-based question/evaluation feature is optional and depends on valid API credentials, model access and internet.
- Uploaded resumes are parsed in memory and not stored as uploaded files. Interview answers and scores are saved locally in `interview_history.db`.
- For a public deployment, add authentication, stronger privacy controls, rate limiting and production server settings.
