# Personal CRM — Sales Pipeline

**Organization**: Codtech IT Solutions Private Limited  
**Intern ID**: CITS4146  

A Flask-based CRM to manage contacts and a visual sales pipeline (deals/stages), with notes and follow-up reminders. Dark-mode UI with a navy + electric-cyan theme.

---

## ⚠️ Why GitHub Pages Shows the README Text

**GitHub Pages only hosts static websites (HTML/CSS/JS)**. It cannot execute Python backend code (`app.py`), connect to SQLite databases, or process Flask routes. When enabled on a repository, GitHub Pages simply converts `readme.md` into a static webpage.

To make the **UI and Backend work live on the web**, you must deploy this application to a cloud provider that supports Python web servers (such as **Render.com**, **PythonAnywhere.com**, or **Railway.app**).

---

## Features

- **Contacts**: Add, edit, delete, search by name/company/email/tag.
- **Pipeline (Kanban)**: Drag-and-drop deals between stages — *Lead → Contacted → Proposal → Negotiation → Won / Lost*.
- **Deals**: Title, value (₹), stage, expected close date, notes — linked to a contact.
- **Activities / Follow-ups**: Log notes, calls, emails, meetings; set due dates; mark done; overdue items highlighted.
- **Dashboard**: Total contacts, open deals, open pipeline value, won value, pipeline-by-stage bar summary, upcoming follow-ups, recent deals.

---

## Local Setup

```bash
# 1. Clone repository & enter directory
git clone https://github.com/Nandha0142/Personal-CRM-System.git
cd Personal-CRM-System

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Load sample data
export FLASK_APP=app.py
flask seed

# 4. Run the development app
python app.py
```

Then open **http://localhost:5000** in your browser.

---

## Free Live Deployment Guide (Render.com)

To host your CRM live on the internet with full UI and Backend functionality:

1. Sign up at [Render.com](https://render.com) (Free Tier available).
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository (`Nandha0142/Personal-CRM-System`).
4. Configure the service settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Click **Create Web Service**.

Your CRM will automatically build and go live with a custom HTTPS URL (e.g. `https://personal-crm-system.onrender.com`) where both UI and Backend work natively!

---

## Project Structure

```
Personal-CRM-System/
├── app.py                  # Flask app, SQLAlchemy models, routes
├── requirements.txt        # Flask, Flask-SQLAlchemy, Gunicorn
├── Procfile                # Production server process definition
├── templates/
│   ├── base.html           # Sidebar layout + shared chrome
│   ├── dashboard.html      # Overview KPIs & pipeline stats
│   ├── contacts.html       # Contacts directory & search
│   ├── contact_form.html   # Create/edit contact form
│   ├── contact_detail.html # Contact profile & activity timeline
│   ├── deals.html          # Drag-and-Drop Kanban board
│   └── deal_form.html      # Create/edit deal form
└── static/
    └── css/
        └── style.css       # Dark mode theme styles
```
