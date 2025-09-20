import os
import base64
import uuid
from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from app.models import User, Post, Blog, PostLike, BlogLike, UserPDF, Profile
from app.extensions import db
from flask_login import current_user, login_required
from app.forms import ProfileForm


bp = Blueprint("users", __name__, template_folder='../../templates/users')


@bp.route("/<int:user_id>")
def profile(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    tab = request.args.get('tab', 'posts')
    page = request.args.get('page', 1, type=int)

    if tab == 'blogs':
        items = Blog.query.filter_by(user_id=user.id)\
            .order_by(Blog.created_at.desc())\
            .paginate(page=page, per_page=5)
    elif tab == 'pdfs':
        items = UserPDF.query.filter_by(user_id=user.id)\
            .order_by(UserPDF.uploaded_at.desc())\
            .paginate(page=page, per_page=5)
    else:  # posts
        items = Post.query.filter_by(user_id=user.id)\
            .order_by(Post.created_at.desc())\
            .paginate(page=page, per_page=5)

    total_likes = (
        db.session.query(PostLike).join(Post).filter(Post.user_id == user.id).count() +
        db.session.query(BlogLike).join(Blog).filter(Blog.user_id == user.id).count()
    )
    follower_count = user.followers.count()
    following_count = user.following.count()

    return render_template(
        'users/profile.html',
        user=user,
        tab=tab,
        items=items,
        total_likes=total_likes,
        follower_count=follower_count,
        following_count=following_count
    )


@bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user.profile)

    if form.validate_on_submit():
        profile = current_user.profile
        if not profile:
            profile = Profile(user_id=current_user.id)

        form.populate_obj(profile)

        # Handle Base64 profile photo data
        photo_data = request.form.get('photo')
        if photo_data and photo_data.startswith('data:image'):
            photo_filename = f"profile_{uuid.uuid4().hex}.jpg"
            photo_path = os.path.join('app', 'static', 'pro_pics', photo_filename)

            # Remove header: "data:image/jpeg;base64,"
            photo_base64 = photo_data.split(',', 1)[1]
            with open(photo_path, 'wb') as f:
                f.write(base64.b64decode(photo_base64))

            profile.photo_url = url_for('static', filename=f'pro_pics/{photo_filename}')

        # Handle Base64 cover image data
        cover_data = request.form.get('cover')
        if cover_data and cover_data.startswith('data:image'):
            cover_filename = f"cover_{uuid.uuid4().hex}.jpg"
            cover_path = os.path.join('app', 'static', 'cover_pics', cover_filename)

            cover_base64 = cover_data.split(',', 1)[1]
            with open(cover_path, 'wb') as f:
                f.write(base64.b64decode(cover_base64))

            profile.cover_url = url_for('static', filename=f'cover_pics/{cover_filename}')

        db.session.add(profile)
        db.session.commit()

        flash('Your profile has been updated successfully.', 'success')
        return redirect(url_for('users.profile', user_id=current_user.id))

    return render_template('users/edit_profile.html', form=form)


@bp.route("/<int:user_id>/follow", methods=["POST"])
@login_required
def follow(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
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
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    current_user.unfollow(user)
    db.session.commit()
    flash(f"You unfollowed {user.profile.first_name or user.email}", "success")
    return redirect(url_for("users.profile", user_id=user_id))