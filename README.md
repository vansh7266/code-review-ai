# AI-Powered Code Review Assistant

A modern, high-fidelity developer utility to automatically scan git changesets, audit them for bugs, performance leaks, and security flaws using **Google Gemini 1.5 Flash**, and write comments directly back onto GitHub Pull Requests.

---

## 🚀 Tech Stack

- **Frontend**: HTML5, Vanilla JavaScript, and beautiful responsive Vanilla CSS utilizing cyber-dark glassmorphism design layouts.
- **Backend**: FastAPI (Python 3.8+) utilizing high-performance asynchronous router handling.
- **Database**: SQLite backed by **SQLAlchemy 2.0** declarations and native asynchronous driver connections (`aiosqlite`).
- **AI Engine**: Google Gemini 1.5 Flash API via standard Generative AI frameworks.
- **Authentication**: GitHub OAuth flow.

---

## 📂 Project Structure

```text
code-review-ai/
├── backend/
│   ├── main.py                  # Bootstraps FastAPI, mounts static directory, starts DB lifespan
│   ├── routes/
│   │   ├── auth.py              # Redirect logins, callbacks, and tokens
│   │   ├── review.py            # Triggers PR analyze tasks & returns SQLite items
│   │   └── dashboard.py         # Historical listings and stats counter APIs
│   ├── services/
│   │   ├── github_service.py    # Integrates HTTPX to grab PR diffs & post inline comments
│   │   ├── gemini_service.py    # Runs diff audits with Gemini 1.5 Flash
│   │   └── db_service.py        # Abstract database CRUD helpers
│   ├── models.py                # Declarative SQLAlchemy models (users, reviews, comments)
│   ├── database.py              # Async SQLite initialization and get_db dependency injection
│   └── config.py                # Environment parser using python-dotenv
├── frontend/
│   ├── index.html               # Sleek beta program registration landing page
│   ├── dashboard.html           # Live analysis dashboard and counters tracking
│   ├── review.html              # Custom annotations viewer and file inspector panels
│   ├── css/
│   │   └── style.css            # Stylesheets with HSL color tokens and custom animations
│   └── js/
│       ├── main.js              # GitHub OAuth redirect simulation, loaders state controls
│       ├── dashboard.js         # Contacts stats metrics counters & history lists
│       └── review.js            # Groups inline suggestions by file panels
├── .env                         # Secret environment keys config
├── requirements.txt             # Python requirements manifest
└── README.md                    # Setup and operational handbook (This file)
```

---

## 🛠️ Installation & Setup

### 1. Prerequisite Installations
Ensure you have Python 3.8+ installed on your workspace shell.

### 2. Configure Local Secrets
Open the root [.env](file:///Users/vanshgupta/Desktop/code-review-ai/.env) file and replace the placeholders with your active credentials:
- Set `GEMINI_API_KEY` to your official Google AI Studio key.
- Set `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` after registering an OAuth Application on your GitHub developer settings panel.

### 3. Setup Virtual Environment
Run the commands below from your shell inside the project folder:
```bash
# Initialize a new virtual environment
python3 -m venv venv

# Activate the workspace environment shell
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🟢 Launching the Application

Start the async server locally using Uvicorn:
```bash
python3 -m uvicorn backend.main:app --port 8000 --reload
```

Once running, navigate to:
- **Landing Page**: [http://localhost:8000/](http://localhost:8000/)
- **Dashboard**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **Interactive Review Report**: [http://localhost:8000/review?id=1](http://localhost:8000/review?id=1)
- **API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

*Note: Database tables are initialized automatically on server launch.*
