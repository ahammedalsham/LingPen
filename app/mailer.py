from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for, render_template
from flask_mail import Message
from .extensions import mail

def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

def generate_token(email, salt):
    s = _serializer()
    return s.dumps(email, salt=salt)

def confirm_token(token, salt, max_age=86400):
    s = _serializer()
    return s.loads(token, salt=salt, max_age=max_age)

# ----------------------
# AUTH EMAILS
# ----------------------

def send_verification(email):
    token = generate_token(email, "email-confirm")
    link = url_for("auth.verify_email", token=token, _external=True)
    msg = Message("Verify your LingPen email", recipients=[email])
    msg.body = render_template("emails/verify.txt", link=link)
    msg.html = render_template("emails/verify.html", link=link)
    mail.send(msg)

def send_reset(email):
    token = generate_token(email, "password-reset")
    link = url_for("auth.reset_password", token=token, _external=True)
    msg = Message("Reset your LingPen password", recipients=[email])
    msg.body = render_template("emails/reset.txt", link=link)
    msg.html = render_template("emails/reset.html", link=link)
    mail.send(msg)

# ----------------------
# EVENT & COURSE EMAILS
# ----------------------

def send_event_registration(user, event):
    """Send confirmation email after user registers for an event"""
    msg = Message(f"Registered for {event.title}", recipients=[user.email])
    msg.body = render_template("emails/event_registration.txt", user=user, event=event)
    msg.html = render_template("emails/event_registration.html", user=user, event=event)
    mail.send(msg)

def send_event_reminder(user, event):
    """Send reminder before the event starts"""
    msg = Message(f"Reminder: {event.title}", recipients=[user.email])
    msg.body = render_template("emails/event_reminder.txt", user=user, event=event)
    msg.html = render_template("emails/event_reminder.html", user=user, event=event)
    mail.send(msg)

def send_course_enrollment(user, course):
    """Send confirmation email after enrolling in a course"""
    msg = Message(f"Enrolled in {course.title}", recipients=[user.email])
    msg.body = render_template("emails/course_enrollment.txt", user=user, course=course)
    msg.html = render_template("emails/course_enrollment.html", user=user, course=course)
    mail.send(msg)
