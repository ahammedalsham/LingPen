from flask import Flask, render_template
from .config import Config
from .extensions import db, migrate, login_manager, mail
from .models import User, Post, Blog

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Blueprints
    from .blueprints.general.routes import bp as general_bp
    from .blueprints.auth.routes import bp as auth_bp
    from .blueprints.users.routes import bp as users_bp
    from .blueprints.posts.routes import bp as posts_bp
    from .blueprints.blogs.routes import bp as blogs_bp
    from .blueprints.events.routes import bp as events_bp
    from .blueprints.courses.routes import bp as courses_bp
    from .blueprints.library.routes import bp as library_bp

    app.register_blueprint(general_bp, url_prefix="/general")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(posts_bp, url_prefix="/posts")
    app.register_blueprint(blogs_bp, url_prefix="/blogs")
    app.register_blueprint(events_bp, url_prefix="/events")
    app.register_blueprint(courses_bp, url_prefix="/courses")
    app.register_blueprint(library_bp, url_prefix="/library")




   

    @app.route("/")
    def home():
        users = User.query.order_by(User.id.desc()).limit(12).all()
        posts = Post.query.order_by(Post.created_at.desc()).limit(6).all()
        blogs = Blog.query.order_by(Blog.created_at.desc()).limit(6).all()  # latest 12 users
        return render_template("home.html", users=users, posts=posts, blogs=blogs)
    



    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if s is None:
            return ""
        return s.replace("\n", "<br>")

    return app
