# Personal CRM — Sales Pipeline

##Intern ID: CITS4146

##Organization: Codtech IT Solutions Private Limited

A Flask-based CRM to manage contacts and a visual sales pipeline (deals/stages), with notes and follow-up reminders. Dark-mode UI with a navy + electric-cyan theme.

## Features

- **Contacts**: add, edit, delete, search by name/company/email/tag
- **Pipeline (Kanban)**: drag-and-drop deals between stages — Lead → Contacted → Proposal → Negotiation → Won / Lost
- **Deals**: title, value (₹), stage, expected close date, notes — linked to a contact
- **Activities / Follow-ups**: log notes, calls, emails, meetings; set due dates; mark done; overdue items highlighted
- **Dashboard**: total contacts, open deals, open pipeline value, won value, pipeline-by-stage bar summary, upcoming follow-ups, recent deals

## Setup

```bash
cd personal_crm
pip install -r requirements.txt

# (optional) load sample data
export FLASK_APP=app.py
flask seed

# run the app
python app.py
```

Then open **http://localhost:5000**

> First run without `flask seed` will auto-create an empty `crm.db` SQLite database.

## Project Structure

```
personal_crm/
├── app.py                  # Flask app, models, routes
├── requirements.txt
├── templates/
│   ├── base.html            # Sidebar layout + shared chrome
│   ├── dashboard.html
│   ├── contacts.html
│   ├── contact_form.html
│   ├── contact_detail.html
│   ├── deals.html            # Kanban board
│   └── deal_form.html
└── static/
    └── css/style.css         # Dark theme
```

## Customizing

- **Pipeline stages**: edit the `STAGES` list and `STAGE_COLORS` dict at the top of `app.py`.
- **Currency**: replace `₹` in the templates if you want a different currency symbol.
- **Theme colors**: tweak the CSS variables at the top of `static/css/style.css` (`--accent`, `--bg`, `--gold`, etc).

## Notes

- Database is SQLite (`crm.db`), created automatically on first run.
- This uses Flask's built-in dev server — for production, run behind Gunicorn/Waitress with `app.config['SECRET_KEY']` set via environment variable.
