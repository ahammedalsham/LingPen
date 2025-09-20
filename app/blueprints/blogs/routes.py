from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Blog, BlogLike, BlogComment
from app.forms import BlogForm, CommentForm

bp = Blueprint("blogs", __name__, template_folder='../../templates/blogs')

@bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    blogs = Blog.query.order_by(Blog.created_at.desc()).paginate(page=page, per_page=10)
    return render_template("blogs/index.html", blogs=blogs)

@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = BlogForm()
    if form.validate_on_submit():
        blog = Blog(user_id=current_user.id, title=form.title.data, body=form.body.data)
        db.session.add(blog)
        db.session.commit()
        flash("Blog published.", "success")
        return redirect(url_for("blogs.index"))
    return render_template("blogs/create.html", form=form)

@bp.route("/<int:blog_id>")
def detail(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    form = CommentForm()
    # show only top-level comments (parent_id=None)
    comments = BlogComment.query.filter_by(blog_id=blog.id, parent_id=None) \
        .order_by(BlogComment.created_at.desc()).all()
    return render_template("blogs/detail.html", blog=blog, form=form, comments=comments)


# ✅ GET all comments (for AJAX/Alpine.js)
@bp.route("/<int:blog_id>/comments")
def get_comments(blog_id):
    blog = Blog.query.get_or_404(blog_id)

    comments = (
        BlogComment.query.filter_by(blog_id=blog.id, parent_id=None)
        .order_by(BlogComment.created_at.desc())
        .all()
    )

    def serialize(c):
        return {
            "id": c.id,
            "body": c.body,
            "user": c.user.profile.first_name or c.user.email,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M"),
            "replies": [serialize(r) for r in c.replies.order_by(BlogComment.created_at.asc())]
        }

    return jsonify([serialize(c) for c in comments])


# ✅ POST a new comment (AJAX + normal form support)
@bp.route("/<int:blog_id>/comment", methods=["POST"])
@login_required
def comment(blog_id):
    blog = Blog.query.get_or_404(blog_id)

    if request.is_json:
        data = request.get_json()
        body = data.get("body")
        parent_id = data.get("parent_id")
    else:
        body = request.form.get("body")
        parent_id = request.form.get("parent_id")

    if not body or not body.strip():
        if request.is_json:
            return jsonify({"error": "Comment cannot be empty"}), 400
        flash("Comment cannot be empty", "danger")
        return redirect(url_for("blogs.detail", blog_id=blog.id))

    # ✅ ensure parent_id is an int or None
    try:
        parent_id = int(parent_id) if parent_id else None
    except (ValueError, TypeError):
        parent_id = None

    comment = BlogComment(
        user_id=current_user.id,
        blog_id=blog.id,
        body=body.strip(),
        parent_id=parent_id,
    )
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


@bp.route("/<int:blog_id>/like", methods=["POST", "GET"])
@login_required
def like(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    existing = BlogLike.query.filter_by(user_id=current_user.id, blog_id=blog.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Like removed.", "success")
    else:
        like = BlogLike(user_id=current_user.id, blog_id=blog.id)
        db.session.add(like)
        db.session.commit()
        flash("Liked.", "success")
    return redirect(url_for("blogs.detail", blog_id=blog.id))

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