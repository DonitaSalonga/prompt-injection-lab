# Prompt Injection Lab

An educational web application for learning about **prompt injection attacks** in a safe, simulated environment. No real LLM or API keys are required.

> ⚠️ **Educational demo only. Do not use techniques shown here to attack real systems.**

---

## What It Does

The lab lets you toggle between two modes:

| Mode | Behaviour |
|-----------|-----------|
| **Vulnerable** | If the Untrusted Content contains a `LAB_OVERRIDE: OUTPUT=…` line, that value overrides the assistant's output – simulating an indirect prompt injection. |
| **Defended** | The `LAB_OVERRIDE` marker is detected and stripped. The assistant summarises only the safe content. |

---

## Project Structure

```
prompt-injection-lab/
├── app.py               # Flask backend (toy assistant logic)
├── requirements.txt
├── README.md
├── templates/
│   └── index.html       # Full UI (Tailwind Play CDN)
└── static/
    ├── css/styles.css
    └── js/app.js
```

---

## Running Locally

### Windows (Command Prompt / PowerShell)

```bat
:: 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

:: PowerShell note: if you get an execution-policy error, run first:
:: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

:: 2. Install dependencies
pip install -r requirements.txt

:: 3. Start the server
python app.py

:: 4. Open in browser
::    http://127.0.0.1:5000
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:5000
```

---

## Deploying to Render

1. **Push to GitHub**

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/<you>/<repo>.git
   git push -u origin main
   ```

2. **Create a Web Service on Render**
   - Go to [https://render.com](https://render.com) → **New → Web Service**
   - Connect your GitHub repository
   - Set the following:

   | Field | Value |
   |-------|-------|
   | Environment | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `gunicorn app:app` |
   | Instance Type | Free |

3. **Deploy** – Render will build and give you a public URL like `https://your-app.onrender.com`.

> **Free tier note:** Render free services spin down after ~15 minutes of inactivity. The first request after a spin-down may take 30–60 seconds to respond while the instance restarts. This is normal.

---

## How the Toy Logic Works

The server (`app.py`) performs fully deterministic, safe processing:

- **No real LLM calls.** No API keys. No external network requests.
- Injection detection: regex scan for lines matching `LAB_OVERRIDE:\s*OUTPUT\s*=\s*(.+)`.
- Defended summary: strips override lines, joins first ~200 characters of meaningful text.
- All user input is HTML-escaped before being returned to the client.
- Maximum input length: 5,000 characters per field.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 + Flask |
| Frontend | Tailwind CSS (Play CDN), Vanilla JS |
| Fonts | DM Sans + JetBrains Mono (Google Fonts) |
| Deploy | Gunicorn + Render |