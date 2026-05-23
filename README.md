# ReviewAI — AI-Powered Code Review Assistant

Automatically analyze GitHub Pull Requests using Google Gemini 1.5 Flash. Detects bugs, security vulnerabilities, performance issues, and code smells — and posts comments directly on your PR.

## Tech Stack
- **Frontend**: HTML, CSS, Vanilla JS
- **Backend**: FastAPI (Python)
- **AI**: Google Gemini 1.5 Flash
- **Auth**: GitHub OAuth
- **DB**: SQLite (SQLAlchemy async)
- **Deploy**: Google Cloud Run

## Setup

### 1. Clone & configure
```bash
git clone https://github.com/vansh7266/code-review-ai.git
cd code-review-ai
cp .env.example .env   # fill in your keys
```

### 2. Install & run locally
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --port 8000 --reload
```
Open: http://localhost:8000

### 3. Deploy to Cloud Run
```bash
gcloud run deploy code-review-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GITHUB_CLIENT_ID=xxx,GITHUB_CLIENT_SECRET=xxx,GEMINI_API_KEY=xxx,SECRET_KEY=xxx,GITHUB_REDIRECT_URI=https://YOUR_CLOUD_RUN_URL/auth/callback
```

## How it works
1. Login with GitHub OAuth
2. Paste any GitHub PR URL
3. Gemini AI analyzes the diff
4. Results appear in dashboard + posted as PR comment on GitHub
