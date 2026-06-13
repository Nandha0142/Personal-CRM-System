import os
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'crm.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

STAGES = ["Lead", "Contacted", "Proposal", "Negotiation", "Won", "Lost"]
STAGE_COLORS = {
    "Lead": "#64748b",
    "Contacted": "#2dd4bf",
    "Proposal": "#38bdf8",
    "Negotiation": "#f59e0b",
    "Won": "#22c55e",
    "Lost": "#ef4444",
}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    tags = db.Column(db.String(200))  # comma separated
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    deals = db.relationship('Deal', backref='contact', lazy=True, cascade="all, delete-orphan")
    activities = db.relationship('Activity', backref='contact', lazy=True, cascade="all, delete-orphan",
                                   order_by="desc(Activity.created_at)")

    @property
    def open_deal_value(self):
        return sum(d.value for d in self.deals if d.stage not in ("Won", "Lost"))

    @property
    def tag_list(self):
        return [t.strip() for t in (self.tags or "").split(",") if t.strip()]


class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    value = db.Column(db.Float, default=0)
    stage = db.Column(db.String(30), default="Lead")
    expected_close = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    type = db.Column(db.String(30), default="note")  # note, call, email, meeting, follow-up
    body = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=True)  # for follow-up reminders
    done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route('/')
def dashboard():
    contacts = Contact.query.all()
    deals = Deal.query.all()

    total_pipeline = sum(d.value for d in deals if d.stage not in ("Won", "Lost"))
    won_value = sum(d.value for d in deals if d.stage == "Won")

    stage_summary = []
    for s in STAGES:
        stage_deals = [d for d in deals if d.stage == s]
        stage_summary.append({
            "name": s,
            "count": len(stage_deals),
            "value": sum(d.value for d in stage_deals),
            "color": STAGE_COLORS[s],
        })

    today = date.today()
    upcoming = (Activity.query
                .filter(Activity.due_date.isnot(None), Activity.done.is_(False))
                .order_by(Activity.due_date.asc())
                .limit(8).all())

    overdue_count = sum(1 for a in upcoming if a.due_date and a.due_date < today)

    recent_deals = Deal.query.order_by(Deal.created_at.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        total_contacts=len(contacts),
        total_pipeline=total_pipeline,
        won_value=won_value,
        open_deals=sum(1 for d in deals if d.stage not in ("Won", "Lost")),
        stage_summary=stage_summary,
        upcoming=upcoming,
        today=today,
        overdue_count=overdue_count,
        recent_deals=recent_deals,
        stage_colors=STAGE_COLORS,
    )


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------
@app.route('/contacts')
def contacts():
    q = request.args.get('q', '').strip()
    query = Contact.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Contact.name.ilike(like),
                                     Contact.company.ilike(like),
                                     Contact.email.ilike(like),
                                     Contact.tags.ilike(like)))
    all_contacts = query.order_by(Contact.name.asc()).all()
    return render_template('contacts.html', contacts=all_contacts, q=q)


@app.route('/contacts/new', methods=['GET', 'POST'])
def new_contact():
    if request.method == 'POST':
        c = Contact(
            name=request.form['name'].strip(),
            company=request.form.get('company', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            tags=request.form.get('tags', '').strip(),
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(c)
        db.session.commit()
        flash(f'Added contact "{c.name}"', 'success')
        return redirect(url_for('contact_detail', contact_id=c.id))
    return render_template('contact_form.html', contact=None)


@app.route('/contacts/<int:contact_id>')
def contact_detail(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    return render_template('contact_detail.html', contact=contact, stages=STAGES,
                            stage_colors=STAGE_COLORS, today=date.today())


@app.route('/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
def edit_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if request.method == 'POST':
        contact.name = request.form['name'].strip()
        contact.company = request.form.get('company', '').strip()
        contact.email = request.form.get('email', '').strip()
        contact.phone = request.form.get('phone', '').strip()
        contact.tags = request.form.get('tags', '').strip()
        contact.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash(f'Updated "{contact.name}"', 'success')
        return redirect(url_for('contact_detail', contact_id=contact.id))
    return render_template('contact_form.html', contact=contact)


@app.route('/contacts/<int:contact_id>/delete', methods=['POST'])
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    name = contact.name
    db.session.delete(contact)
    db.session.commit()
    flash(f'Deleted "{name}"', 'success')
    return redirect(url_for('contacts'))


# ---------------------------------------------------------------------------
# Activities (notes / follow-ups)
# ---------------------------------------------------------------------------
@app.route('/contacts/<int:contact_id>/activities/new', methods=['POST'])
def new_activity(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    due = request.form.get('due_date')
    a = Activity(
        contact_id=contact.id,
        type=request.form.get('type', 'note'),
        body=request.form.get('body', '').strip(),
        due_date=datetime.strptime(due, '%Y-%m-%d').date() if due else None,
    )
    db.session.add(a)
    db.session.commit()
    flash('Activity added', 'success')
    return redirect(url_for('contact_detail', contact_id=contact.id))


@app.route('/activities/<int:activity_id>/toggle', methods=['POST'])
def toggle_activity(activity_id):
    a = Activity.query.get_or_404(activity_id)
    a.done = not a.done
    db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/activities/<int:activity_id>/delete', methods=['POST'])
def delete_activity(activity_id):
    a = Activity.query.get_or_404(activity_id)
    contact_id = a.contact_id
    db.session.delete(a)
    db.session.commit()
    return redirect(request.referrer or url_for('contact_detail', contact_id=contact_id))


# ---------------------------------------------------------------------------
# Deals / Pipeline
# ---------------------------------------------------------------------------
@app.route('/deals')
def deals():
    board = {s: Deal.query.filter_by(stage=s).order_by(Deal.created_at.desc()).all() for s in STAGES}
    totals = {s: sum(d.value for d in board[s]) for s in STAGES}
    return render_template('deals.html', board=board, stages=STAGES,
                            stage_colors=STAGE_COLORS, totals=totals)


@app.route('/deals/new', methods=['GET', 'POST'])
def new_deal():
    contacts_list = Contact.query.order_by(Contact.name.asc()).all()
    if request.method == 'POST':
        close = request.form.get('expected_close')
        d = Deal(
            title=request.form['title'].strip(),
            value=float(request.form.get('value') or 0),
            stage=request.form.get('stage', 'Lead'),
            contact_id=int(request.form['contact_id']),
            expected_close=datetime.strptime(close, '%Y-%m-%d').date() if close else None,
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(d)
        db.session.commit()
        flash(f'Deal "{d.title}" created', 'success')
        return redirect(url_for('deals'))
    preselect = request.args.get('contact_id', type=int)
    return render_template('deal_form.html', deal=None, contacts=contacts_list,
                            stages=STAGES, preselect=preselect)


@app.route('/deals/<int:deal_id>/edit', methods=['GET', 'POST'])
def edit_deal(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    contacts_list = Contact.query.order_by(Contact.name.asc()).all()
    if request.method == 'POST':
        close = request.form.get('expected_close')
        deal.title = request.form['title'].strip()
        deal.value = float(request.form.get('value') or 0)
        deal.stage = request.form.get('stage', 'Lead')
        deal.contact_id = int(request.form['contact_id'])
        deal.expected_close = datetime.strptime(close, '%Y-%m-%d').date() if close else None
        deal.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash(f'Deal "{deal.title}" updated', 'success')
        return redirect(url_for('deals'))
    return render_template('deal_form.html', deal=deal, contacts=contacts_list,
                            stages=STAGES, preselect=None)


@app.route('/deals/<int:deal_id>/delete', methods=['POST'])
def delete_deal(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    db.session.delete(deal)
    db.session.commit()
    flash('Deal deleted', 'success')
    return redirect(url_for('deals'))


@app.route('/deals/<int:deal_id>/move', methods=['POST'])
def move_deal(deal_id):
    """AJAX endpoint used by the drag-and-drop kanban board."""
    deal = Deal.query.get_or_404(deal_id)
    new_stage = request.json.get('stage')
    if new_stage not in STAGES:
        return jsonify({"ok": False, "error": "invalid stage"}), 400
    deal.stage = new_stage
    db.session.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Seed data helper (run once)
# ---------------------------------------------------------------------------
@app.cli.command('seed')
def seed():
    """Populate the DB with sample data: flask seed"""
    db.drop_all()
    db.create_all()

    c1 = Contact(name="Ananya Rao", company="Rao Dental Clinic", email="ananya@raodental.com",
                  phone="+91 98765 43210", tags="clinic, dental, hot-lead",
                  notes="Interested in AI receptionist for appointment booking.")
    c2 = Contact(name="Vikram Shah", company="Shah & Co Restaurants", email="vikram@shahgroup.in",
                  phone="+91 99887 66554", tags="restaurant, website",
                  notes="Wants a dark-mode website with online ordering.")
    c3 = Contact(name="Priya Menon", company="Menon Skin Clinic", email="priya@menonskin.com",
                  phone="+91 91234 56780", tags="clinic, follow-up")
    c4 = Contact(name="Rahul Iyer", company="Iyer Consulting", email="rahul@iyerconsult.com",
                  phone="+91 90909 80808", tags="referral")

    db.session.add_all([c1, c2, c3, c4])
    db.session.commit()

    deals_data = [
        Deal(title="AI Receptionist - Setup", value=15000, stage="Proposal",
             contact_id=c1.id, expected_close=date(2026, 6, 30),
             notes="Sent proposal with WhatsApp integration plan."),
        Deal(title="Restaurant Website Build", value=12000, stage="Negotiation",
             contact_id=c2.id, expected_close=date(2026, 6, 25),
             notes="Negotiating final price, wants Three.js animations."),
        Deal(title="AI Receptionist - Trial", value=5000, stage="Lead",
             contact_id=c3.id, expected_close=date(2026, 7, 15)),
        Deal(title="Portfolio + Branding Package", value=8000, stage="Won",
             contact_id=c4.id, expected_close=date(2026, 5, 30),
             notes="Completed and delivered."),
        Deal(title="Chatbot for FAQ", value=4000, stage="Lost",
             contact_id=c3.id, notes="Budget too low."),
    ]
    db.session.add_all(deals_data)
    db.session.commit()

    activities = [
        Activity(contact_id=c1.id, type="call", body="Discuss pricing tiers",
                 due_date=date(2026, 6, 16)),
        Activity(contact_id=c2.id, type="follow-up", body="Send revised mockup",
                 due_date=date(2026, 6, 14)),
        Activity(contact_id=c3.id, type="email", body="Send case studies for clinics",
                 due_date=date(2026, 6, 20)),
        Activity(contact_id=c1.id, type="note", body="Met at local business meetup, very interested."),
    ]
    db.session.add_all(activities)
    db.session.commit()
    print("Database seeded with sample data.")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
