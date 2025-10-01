import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Blog, BlogLike, BlogComment
from app.forms import BlogForm, CommentForm

bp = Blueprint("blogs", __name__, template_folder='../../templates/blogs')


# -----------------------------
# INDEX (with filters & featured)
# -----------------------------
@bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category")
    search = request.args.get("q")

    query = Blog.query.order_by(Blog.created_at.desc())

    if category:
        query = query.filter(Blog.category == category)
    if search:
        query = query.filter(
            Blog.title.ilike(f"%{search}%") |
            Blog.body.ilike(f"%{search}%") |
            Blog.tags.ilike(f"%{search}%")
        )

    featured = Blog.query.filter_by(is_featured=True).order_by(Blog.created_at.desc()).limit(3).all()
    blogs = query.paginate(page=page, per_page=10)

    return render_template("blogs/index.html", blogs=blogs, featured=featured, category=category, search=search)


# -----------------------------
# CREATE BLOG
# -----------------------------
@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = BlogForm()

    # REMOVE the manual body data assignment.
    # If the rich text editor's hidden input is named 'body',
    # Flask-WTF will automatically populate form.body.data on POST.
    #
    # if request.method == "POST":
    #     body_html = request.form.get("body")
    #     if body_html is not None:
    #         form.body.data = body_html
    
    if form.validate_on_submit():
        blog = Blog(
            user_id=current_user.id,
            title=form.title.data,
            body=form.body.data,
            tags=form.tags.data,
            category=form.category.data,
            is_featured=form.is_featured.data,
        )
        
        # ... rest of your code ...
        
        # Auto excerpt & reading time
        blog.set_excerpt()
        blog.set_reading_time()

        # Save cover image if uploaded
        # Inside create() and edit()

        if form.cover_image.data:
            filename = secure_filename(form.cover_image.data.filename)
            unique_name = f"{uuid.uuid4().hex}_{filename}"

            # Save inside static/cover_image/
            upload_dir = os.path.join(current_app.root_path, "static", "cover_image")
            os.makedirs(upload_dir, exist_ok=True)

            upload_path = os.path.join(upload_dir, unique_name)
            form.cover_image.data.save(upload_path)

            # Store relative path for url_for('static', filename=...)
            blog.cover_image = f"cover_image/{unique_name}"


        db.session.add(blog)
        db.session.commit()
        flash("Blog published.", "success")
        return redirect(url_for("blogs.detail", blog_id=blog.id))

    return render_template("blogs/create.html", form=form, blog=None)

# -----------------------------
# BLOG DETAIL
# -----------------------------
@bp.route("/<int:blog_id>")
def detail(blog_id):
    blog = Blog.query.get_or_404(blog_id)

    # Count view
    blog.views = (blog.views or 0) + 1
    db.session.commit()

    form = CommentForm()
    comments = BlogComment.query.filter_by(blog_id=blog.id, parent_id=None) \
        .order_by(BlogComment.created_at.desc()).all()

    # Related posts by category
    related = Blog.query.filter(
        Blog.category == blog.category,
        Blog.id != blog.id
    ).order_by(Blog.created_at.desc()).limit(3).all()

    return render_template("blogs/detail.html", blog=blog, form=form, comments=comments, related_posts=related)


# -----------------------------
# COMMENTS (AJAX)
# -----------------------------
@bp.route("/<int:blog_id>/comments")
def get_comments(blog_id):
    blog = Blog.query.get_or_404(blog_id)

    def serialize(c):
        return {
            "id": c.id,
            "body": c.body,
            "user": c.user.profile.first_name or c.user.email,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M"),
            "replies": [serialize(r) for r in c.replies.order_by(BlogComment.created_at.asc())]
        }

    comments = BlogComment.query.filter_by(blog_id=blog.id, parent_id=None) \
        .order_by(BlogComment.created_at.desc()).all()
    return jsonify([serialize(c) for c in comments])


@bp.route("/<int:blog_id>/comment", methods=["POST"])
@login_required
def comment(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    body = request.form.get("body") or (request.json and request.json.get("body"))
    parent_id = request.form.get("parent_id") or (request.json and request.json.get("parent_id"))

    if not body or not body.strip():
        flash("Comment cannot be empty", "danger")
        return redirect(url_for("blogs.detail", blog_id=blog.id))

    try:
        parent_id = int(parent_id) if parent_id else None
    except (ValueError, TypeError):
        parent_id = None

    comment = BlogComment(user_id=current_user.id, blog_id=blog.id, body=body.strip(), parent_id=parent_id)
    db.session.add(comment)
    db.session.commit()

    if request.is_json:
        return jsonify({
            "id": comment.id,
            "body": comment.body,
            "user": current_user.profile.first_name or current_user.email,
            "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
            "replies": []
        })

    flash("Comment added.", "success")
    return redirect(url_for("blogs.detail", blog_id=blog.id))


# -----------------------------
# LIKE / UNLIKE
# -----------------------------
@bp.route("/<int:blog_id>/like", methods=["POST"])
@login_required
def like(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    existing = BlogLike.query.filter_by(user_id=current_user.id, blog_id=blog.id).first()
    if existing:
        db.session.delete(existing)
        flash("Like removed.", "info")
    else:
        like = BlogLike(user_id=current_user.id, blog_id=blog.id)
        db.session.add(like)
        flash("Liked.", "success")
    db.session.commit()
    return redirect(url_for("blogs.detail", blog_id=blog.id))


# -----------------------------
# BOOKMARK / SAVE
# -----------------------------
@bp.route("/<int:blog_id>/bookmark", methods=["POST"])
@login_required
def bookmark(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if current_user in blog.bookmarked_by:
        blog.bookmarked_by.remove(current_user)
        flash("Removed from saved blogs.", "info")
    else:
        blog.bookmarked_by.append(current_user)
        flash("Blog saved to your library.", "success")
    db.session.commit()
    return redirect(url_for("blogs.detail", blog_id=blog.id))


# -----------------------------
# EDIT & DELETE
# -----------------------------
@bp.route("/<int:blog_id>/edit", methods=["GET", "POST"])
@login_required
def edit(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if not (current_user.id == blog.user_id or getattr(current_user, "is_admin", False)):
        abort(403)

    form = BlogForm(obj=blog)
    if form.validate_on_submit():
        blog.title = form.title.data
        blog.body = form.body.data
        blog.tags = form.tags.data
        blog.category = form.category.data
        blog.is_featured = form.is_featured.data
        blog.set_excerpt()
        blog.set_reading_time()

       # Inside create() and edit()

        if form.cover_image.data:
            filename = secure_filename(form.cover_image.data.filename)
            unique_name = f"{uuid.uuid4().hex}_{filename}"

            # Save inside static/cover_image/
            upload_dir = os.path.join(current_app.root_path, "static", "cover_image")
            os.makedirs(upload_dir, exist_ok=True)

            upload_path = os.path.join(upload_dir, unique_name)
            form.cover_image.data.save(upload_path)

            # Store relative path for url_for('static', filename=...)
            blog.cover_image = f"cover_image/{unique_name}"


        db.session.commit()
        flash("Blog updated.", "success")
        return redirect(url_for("blogs.detail", blog_id=blog.id))

    return render_template("blogs/edit.html", form=form, blog=blog)


@bp.route("/<int:blog_id>/delete", methods=["POST"])
@login_required
def delete(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if not (current_user.id == blog.user_id or getattr(current_user, "is_admin", False)):
        abort(403)
    db.session.delete(blog)
    db.session.commit()
    flash("Blog deleted.", "success")
    return redirect(url_for("blogs.index"))