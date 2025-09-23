import os
import base64
import uuid
from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from app.models import User, Post, Blog, UserPDF, Profile
from app.extensions import db
from flask_login import current_user, login_required
from app.forms import ProfileForm

bp = Blueprint("users", __name__, template_folder='../../templates/users')


@bp.route("/user/<int:user_id>")
def profile(user_id):
    user = User.query.get_or_404(user_id)

    total_likes = sum([p.likes.count() for p in user.posts]) + sum([b.likes.count() for b in user.blogs])
    followers_count = user.followers.count()
    following_count = user.following.count()

    posts = user.posts.order_by(Post.created_at.desc()).all()
    blogs = user.blogs.order_by(Blog.created_at.desc()).all()
    pdfs = UserPDF.query.filter_by(user_id=user.id).order_by(UserPDF.uploaded_at.desc()).all()

    return render_template(
        "users/profile.html",
        user=user,
        total_likes=total_likes,
        followers_count=followers_count,
        following_count=following_count,
        posts=posts,
        blogs=blogs,
        pdfs=pdfs
    )


@bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    # Ensure profile exists
    profile = current_user.profile
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()

    form = ProfileForm(obj=profile)

    if form.validate_on_submit():
        form.populate_obj(profile)

        # Profile photo
        photo_data = request.form.get('photo')
        if photo_data and photo_data.startswith('data:image'):
            filename = f"profile_{uuid.uuid4().hex}.jpg"
            path = os.path.join('app', 'static', 'pro_pics', filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                f.write(base64.b64decode(photo_data.split(',', 1)[1]))
            profile.photo_url = url_for('static', filename=f'pro_pics/{filename}')

        # Cover image
        cover_data = request.form.get('cover')
        if cover_data and cover_data.startswith('data:image'):
            filename = f"cover_{uuid.uuid4().hex}.jpg"
            path = os.path.join('app', 'static', 'cover_pics', filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                f.write(base64.b64decode(cover_data.split(',', 1)[1]))
            profile.cover_url = url_for('static', filename=f'cover_pics/{filename}')

        db.session.commit()
        flash('Your profile has been updated successfully.', 'success')
        return redirect(url_for('users.profile', user_id=current_user.id))

    return render_template('users/edit_profile.html', form=form)


@bp.route("/<int:user_id>/follow", methods=["POST"])
@login_required
def follow(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash("You cannot follow yourself.", "error")
    else:
        current_user.follow(user)
        db.session.commit()
        flash(f"You are now following {user.profile.first_name or user.email}", "success")
    return redirect(url_for("users.profile", user_id=user_id))


@bp.route("/<int:user_id>/unfollow", methods=["POST"])
@login_required
def unfollow(user_id):
    user = User.query.get_or_404(user_id)
    current_user.unfollow(user)
    db.session.commit()
    flash(f"You unfollowed {user.profile.first_name or user.email}", "success")
    return redirect(url_for("users.profile", user_id=user_id))