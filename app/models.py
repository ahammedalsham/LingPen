from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .extensions import db, login_manager


# Followers association table
followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id"), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    email_verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("Profile", uselist=False, back_populates="user")

    def set_password(self, pw: str):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw: str) -> bool:
        return check_password_hash(self.password_hash, pw)
    
     # Follower relationships
    following = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic"
    )

    def follow(self, user):
        if not self.is_following(user):
            self.following.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        return self.following.filter(followers.c.followed_id == user.id).count() > 0
    
    post_comments = db.relationship("PostComment", back_populates="user", lazy="dynamic")
    blog_comments = db.relationship("BlogComment", back_populates="user", lazy="dynamic")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    dob = db.Column(db.Date)
    photo_url = db.Column(db.String(255))
    cover_url = db.Column(db.String(255))
    about = db.Column(db.Text)
    primary_language = db.Column(db.String(80))
    interests = db.Column(db.String(255))
    proficiency_level = db.Column(db.String(50))
    
    user = db.relationship("User", back_populates="profile")





# Posts & comments
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("posts", lazy="dynamic"))
    likes = db.relationship("PostLike", back_populates="post", cascade='all, delete-orphan', lazy="dynamic")
    comments = db.relationship("PostComment", back_populates="post", cascade='all, delete-orphan', lazy="dynamic")

class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("post_likes", lazy="dynamic"))
    post = db.relationship("Post", back_populates="likes")

class PostComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("post_comment.id"), nullable=True)

    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User",back_populates="post_comments")
    post = db.relationship("Post", back_populates="comments")

    replies = db.relationship(
        "PostComment",
        backref=db.backref("parent", remote_side=[id]),
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

# Blogs, likes, comments, bookmarks

# Association table for bookmarks
blog_bookmarks = db.Table(
    "blog_bookmarks",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("blog_id", db.Integer, db.ForeignKey("blog.id"), primary_key=True),
    db.Column("created_at", db.DateTime, default=datetime.utcnow)
)


class Blog(db.Model):
    __tablename__ = "blog"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    # Content
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(500))
    cover_image = db.Column(db.String(255))
    tags = db.Column(db.String(255))  # Comma-separated tags
    category = db.Column(db.String(100))  # e.g., Linguistics, Syntax, etc.
    reading_time = db.Column(db.Integer)  # in minutes

    # Metadata
    is_featured = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship("User", backref=db.backref("blogs", lazy="dynamic"))
    likes = db.relationship("BlogLike", back_populates="blog", cascade="all, delete-orphan", lazy="dynamic")
    comments = db.relationship("BlogComment", back_populates="blog", cascade="all, delete-orphan", lazy="dynamic")
    bookmarked_by = db.relationship("User", secondary=blog_bookmarks,
                                    backref=db.backref("saved_blogs", lazy="dynamic"))

    # Utility methods
    def set_excerpt(self, char_limit=200):
        """Generate an excerpt from the blog body"""
        self.excerpt = (self.body[:char_limit] + "...") if len(self.body) > char_limit else self.body

    def set_reading_time(self):
        """Estimate reading time (200 words/minute)"""
        word_count = len(self.body.split())
        self.reading_time = max(1, word_count // 200)

    def like_count(self):
        return self.likes.count()

    def comment_count(self):
        return self.comments.count()


class BlogLike(db.Model):
    __tablename__ = "blog_like"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    blog_id = db.Column(db.Integer, db.ForeignKey("blog.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("blog_likes", lazy="dynamic"))
    blog = db.relationship("Blog", back_populates="likes")


class BlogComment(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    blog_id = db.Column(db.Integer, db.ForeignKey("blog.id"), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("blog_comment.id"), nullable=True)

    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User", back_populates='blog_comments')
    blog = db.relationship("Blog", back_populates="comments")

    replies = db.relationship(
        "BlogComment",
        backref=db.backref("parent", remote_side=[id]),
        lazy="dynamic",
        cascade="all, delete-orphan"
    )


# Events & registrations
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    image = db.Column(db.String(255))
    is_online = db.Column(db.Boolean, default=False)
    capacity = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    registrations = db.relationship("EventRegistration", backref="event", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def spots_left(self):
        taken = self.registrations.count()
        return max(self.capacity - taken, 0)

class EventRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'event_id', name='uq_event_user'),)

# Courses & registrations
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_live = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    registrations = db.relationship("CourseRegistration", backref="course", lazy="dynamic", cascade="all, delete-orphan")

class CourseRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='uq_course_user'),)

# PDFs
class AdminPDF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserPDF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="pdfs")


# app/models.py





   
