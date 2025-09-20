import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///lingpen.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "25"))
    MAIL_USE_TLS = bool(int(os.getenv("MAIL_USE_TLS", "0")))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    SECURITY_EMAIL_SENDER = os.getenv("SECURITY_EMAIL_SENDER", "noreply@lingpen.local")
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
    MAIL_SUPPRESS_SEND = bool(int(os.getenv("MAIL_SUPPRESS_SEND", "1")))
