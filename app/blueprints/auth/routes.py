from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, Profile
from app.forms import RegisterForm, LoginForm, ForgotForm, ResetForm
from app.mailer import send_verification, confirm_token, send_reset
from datetime import datetime

bp = Blueprint("auth", __name__, template_folder='../../templates/auth')

@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegisterForm()
    if form.validate_on_submit():
        # Check if email is already registered
        if db.session.execute(db.select(User).filter_by(email=form.email.data.lower())).scalar():
            flash("Email already registered.", "error")
            return render_template("auth/register.html", form=form)

        # Check if username is already taken
        if db.session.execute(db.select(User).filter_by(username=form.username.data)).scalar():
            flash("Username already taken. Please choose another.", "error")
            return render_template("auth/register.html", form=form)

        # Create new user
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.lower()
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        # Create empty profile for the user
        db.session.add(Profile(user_id=user.id))
        db.session.commit()

        # send_verification(user.email)  # Uncomment if email verification enabled
        flash("Welcome! Please verify your email.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).filter_by(email=form.email.data.lower())).scalar()
        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password.", "error")
        else:
            login_user(user, remember=form.remember.data)
            flash(f"Welcome, {(user.profile.first_name or 'Friend')}!", "success")
            return redirect(url_for("home"))
    return render_template("auth/login.html", form=form)

@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))

@bp.route("/verify/<token>")
def verify_email(token):
    try:
        email = confirm_token(token, "email-confirm")
    except Exception:
        flash("Invalid or expired verification link.", "error")
        return redirect(url_for("home"))
    user = db.session.execute(db.select(User).filter_by(email=email)).scalar()
    if not user:
        flash("Account not found.", "error")
        return redirect(url_for("home"))
    if user.email_verified_at:
        flash("Email already verified.", "success")
    else:
        user.email_verified_at = datetime.utcnow()
        db.session.commit()
        flash("Email verified. You're all set!", "success")
    return redirect(url_for("auth.login"))

@bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    form = ForgotForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).filter_by(email=form.email.data.lower())).scalar()
        if user:
            # send_reset(user.email)
            pass
        flash("If the email exists, a reset link has been sent.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot.html", form=form)

@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    form = ResetForm()
    if form.validate_on_submit():
        try:
            email = confirm_token(token, "password-reset")
        except Exception:
            flash("Invalid or expired reset link.", "error")
            return redirect(url_for("auth.forgot"))
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar()
        if not user:
            flash("Account not found.", "error")
            return redirect(url_for("auth.forgot"))
        user.set_password(form.password.data)
        db.session.commit()
        flash("Password updated. You can log in now.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset.html", form=form)
