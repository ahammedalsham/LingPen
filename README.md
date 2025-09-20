# LingPen Sprint 3 - Full Project

This project includes Sprint 1-3: Authentication, Profiles, Posts, Blogs, Events, Courses.

Quickstart:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
export FLASK_APP=manage.py
flask db init && flask db migrate -m "init" && flask db upgrade
python manage.py
```
