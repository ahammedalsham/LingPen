from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Post, PostLike, PostComment
from app.forms import PostForm, CommentForm

bp = Blueprint("posts", __name__, template_folder='../../templates/posts')

@bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=10)
    return render_template("posts/index.html", posts=posts)

@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(user_id=current_user.id, body=form.body.data)
        db.session.add(post)
        db.session.commit()
        flash("Post created.", "success")
        return redirect(url_for("posts.index"))
    return render_template("posts/create.html", form=form)


@bp.route("/posts/<int:post_id>")
def detail(post_id):
    post = Post.query.get_or_404(post_id)

    # Load only top-level comments (replies handled in template/JS)
    comments = (
        PostComment.query.filter_by(post_id=post.id, parent_id=None)
        .order_by(PostComment.created_at.desc())
        .all()
    )

    form = CommentForm()
    return render_template("posts/detail.html", post=post, form=form, comments=comments)

# ✅ GET all comments (AJAX)
@bp.route("/<int:post_id>/comments")
def get_comments(post_id):
    post = Post.query.get_or_404(post_id)

    def serialize(c):
        return {
            "id": c.id,
            "body": c.body,
            "user": c.user.profile.first_name or c.user.email,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M"),
            "replies": [serialize(r) for r in sorted(c.replies, key=lambda r: r.created_at)]
        }

    comments = (
        PostComment.query.filter_by(post_id=post.id, parent_id=None)
        .order_by(PostComment.created_at.desc())
        .all()
    )

    return jsonify([serialize(c) for c in comments])


# ✅ POST a new comment
@bp.route("/<int:post_id>/comment", methods=["POST"])
@login_required
def comment(post_id):
    post = Post.query.get_or_404(post_id)

    if request.is_json:
        data = request.get_json()
        body = data.get("body", "").strip()
        parent_id = data.get("parent_id")
    else:
        body = (request.form.get("body") or "").strip()
        parent_id = request.form.get("parent_id")

    if not body:
        if request.is_json:
            return jsonify({"error": "Comment cannot be empty"}), 400
        flash("Comment cannot be empty", "danger")
        return redirect(url_for("posts.detail", post_id=post.id))

    # Convert parent_id safely
    parent_id = int(parent_id) if parent_id and str(parent_id).isdigit() else None

    comment = PostComment(
        user_id=current_user.id,
        post_id=post.id,
        body=body,
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
    return redirect(url_for("posts.detail", post_id=post.id))


@bp.route("/<int:post_id>/like", methods=["POST","GET"])
@login_required
def like(post_id):
    post = Post.query.get_or_404(post_id)
    existing = PostLike.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Like removed.", "success")
    else:
        like = PostLike(user_id=current_user.id, post_id=post.id)
        db.session.add(like)
        db.session.commit()
        flash("Liked.", "success")
    return redirect(url_for("posts.detail", post_id=post.id))

@bp.route("/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit(post_id):
    post = Post.query.get_or_404(post_id)
    if not (current_user.id == post.user_id or getattr(current_user, "is_admin", False)):
        abort(403)
    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.commit()
        flash("Post updated.", "success")
        return redirect(url_for("posts.detail", post_id=post.id))
    return render_template("posts/edit.html", form=form, post=post)

@bp.route("/<int:post_id>/delete", methods=["POST"])
@login_required
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    if not (current_user.id == post.user_id or getattr(current_user, "is_admin", False)):
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "success")
    return redirect(url_for("posts.index"))