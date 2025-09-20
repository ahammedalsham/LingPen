from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from datetime import datetime
from app.extensions import db
from app.models import Event, EventRegistration
from app.forms import EventForm
from app.decorators import admin_required
from app.mailer import send_event_registration

bp = Blueprint("events", __name__, template_folder='../../templates/events')

@bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    events = Event.query.order_by(Event.date.asc()).paginate(page=page, per_page=9)
    return render_template("events/index.html", events=events, now=datetime.utcnow())

@bp.route("/<int:event_id>")
def detail(event_id):
    event = Event.query.get_or_404(event_id)
    user_is_registered = False
    if current_user.is_authenticated:
        user_is_registered = EventRegistration.query.filter_by(user_id=current_user.id, event_id=event.id).first() is not None
    return render_template("events/detail.html", event=event, user_is_registered=user_is_registered)

@bp.route("/create", methods=["GET","POST"])
@login_required
@admin_required
def create():
    form = EventForm()
    if form.validate_on_submit():
        ev = Event(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            date=form.date.data,
            image=form.image.data.strip() if form.image.data else None,
            is_online=form.is_online.data,
            capacity=form.capacity.data
        )
        db.session.add(ev)
        db.session.commit()
        flash('Event created.', 'success')
        return redirect(url_for('events.detail', event_id=ev.id))
    return render_template("events/create.html", form=form)

@bp.route("/<int:event_id>/edit", methods=["GET","POST"])
@login_required
@admin_required
def edit(event_id):
    form = EventForm()
    event = Event.query.get_or_404(event_id)
    if request.method == "GET":
        form = EventForm(obj=event)
    if form.validate_on_submit():
        event.title = form.title.data.strip()
        event.description = form.description.data.strip()
        event.date = form.date.data
        event.image = form.image.data.strip() if form.image.data else None
        event.is_online = form.is_online.data
        event.capacity = form.capacity.data
        db.session.commit()
        flash('Event updated.', 'success')
        return redirect(url_for('events.detail', event_id=event.id))
    return render_template("events/edit.html", form=form, event=event)

@bp.route("/<int:event_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted.', 'info')
    return redirect(url_for('events.index'))

@bp.route("/<int:event_id>/register", methods=["POST"])
@login_required
def register(event_id):
    event = Event.query.get_or_404(event_id)
    if event.spots_left <= 0:
        flash('This event is full.', 'warning')
        return redirect(url_for('events.detail', event_id=event.id))
    existing = EventRegistration.query.filter_by(user_id=current_user.id, event_id=event.id).first()
    if existing:
        flash('You are already registered for this event.', 'info')
        return redirect(url_for('events.detail', event_id=event.id))
    reg = EventRegistration(user_id=current_user.id, event_id=event.id)
    db.session.add(reg)
    db.session.commit()
    #send_event_registration(current_user, event)
    flash('Registered successfully 🎉', 'success')
    return redirect(url_for('events.detail', event_id=event.id))
