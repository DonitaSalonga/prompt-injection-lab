# Prompt Injection Lab

An educational web application for learning about prompt injection attacks in a safe, fully simulated environment. No real LLM or API keys required.

> ⚠️ **Educational demo only.** Do not use techniques shown here to attack real systems.

---

## Live Demo

🔗 [https://promptinjectionlab.vercel.app](https://promptinjectionlab.vercel.app)

---

## What It Does

The lab simulates a ShopSmart customer support chatbot and lets you toggle between two modes:

| Mode | Behaviour |
|---|---|
| **Vulnerable** | If the Untrusted Content contains a `LAB_OVERRIDE: OUTPUT=…` line, that value overrides the assistant's output — simulating an **indirect prompt injection**. Direct injection attempts in the user message field also succeed. |
| **Defended** | Both `LAB_OVERRIDE` markers and 20+ direct injection patterns are detected and blocked. The assistant stays in its ShopSmart role and refuses to comply. |

---

## Attack Vectors Covered

The lab detects and demonstrates the following prompt injection categories:

1. Classic direct override (`ignore previous instructions`)
2. Roleplay / persona adoption (`act as`, `you are now`)
3. Hypothetical / fictional framing (`for a story`, `imagine you were`)
4. Sympathy / emotional manipulation (`I lost my job`, `my child is sick`)
5. Technical / pseudo-code overrides (`[SYSTEM]`, `<prompt>`, `discount_allowance =`)
6. Translation / encoding attacks (multilingual ignore commands, base64-like strings)
7. Context switching (`let's play a game`, `new scenario:`)
8. Authority / social engineering (`I work at ShopSmart`, `management has approved`)
9. Gaslighting / confusion (`you already said`, `remember when you agreed`)
10. Direct discount / auth injection (`100% discount`, `apply promo code`)

---

## Project Structure

```
prompt-injection-lab/
├── api/
│   └── index.py         # Vercel serverless entry point (Flask app)
├── templates/
│   └── index.html       # Full UI (Tailwind Play CDN)
├── static/
│   ├── css/styles.css
│   └── js/app.js
├── app.py               # Original Flask app (kept for local use)
├── requirements.txt     # Python dependencies
├── vercel.json          # Vercel deployment configuration
├── render.yaml          # Render deployment configuration (legacy)
└── README.md
```

---

## Running Locally

### Windows (Command Prompt / PowerShell)

```bash
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

## Deploying to Vercel (Current)

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

### Step 2 — Import on Vercel

1. Go to [https://vercel.com](https://vercel.com) → Sign up with GitHub
2. Click **Add New Project** → Import your repository
3. On the config screen:
   - Framework Preset → **Other**
   - Build Command → **leave empty**
   - Output Directory → **leave empty**
4. Click **Deploy**

Vercel will build and give you a public URL like `https://your-app.vercel.app`.

### Vercel Configuration (`vercel.json`)

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

> ✅ No environment variables or API keys needed. Auto-deploys on every push to `main`.

---

## Deploying to Render (Legacy)

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

### Step 2 — Create a Web Service on Render

- Go to [https://render.com](https://render.com) → New → Web Service
- Connect your GitHub repository
- Set the following:

| Field | Value |
|---|---|
| Environment | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |
| Instance Type | Free |

> ⚠️ **Free tier note:** Render free services spin down after ~15 minutes of inactivity. The first request after a spin-down may take 30–60 seconds to respond. This is normal.

---

## How the Simulation Works

The server performs fully deterministic, safe processing — no external network calls of any kind:

- **No real LLM.** No API keys. No external requests.
- **Indirect injection detection:** regex scan for `LAB_OVERRIDE:\s*OUTPUT\s*=\s*(.+)` inside the untrusted ticket content.
- **Direct injection detection:** 20+ regex patterns covering roleplay, authority claims, emotional manipulation, technical overrides, and more.
- **Defended mode:** detects both attack types and returns a randomised rejection response (10 variants).
- **Vulnerable mode:** executes the injection and returns a fake discount authorisation notice.
- **Dynamic responses:** the assistant reflects any edits made to the customer ticket (name, order ID, status, etc.).
- **Maximum input length:** 5,000 characters per field.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3 + Flask |
| Frontend | Tailwind CSS (Play CDN), Vanilla JS |
| Fonts | DM Sans + JetBrains Mono (Google Fonts) |
| Deploy (current) | Vercel (serverless, auto-deploy from GitHub) |
| Deploy (legacy) | Gunicorn + Render |

---

## Author

**Donita Salonga**  
IT Security Student · AWS Community Member
