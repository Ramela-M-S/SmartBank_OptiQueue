from flask import Flask, request, jsonify, flash, redirect
from datetime import datetime
import pytz
import os
from flask import render_template
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

socketio = SocketIO(cors_allowed_origins="*")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300 per day", "60 per hour"],
    storage_uri="memory://"
)

app = Flask(__name__)
socketio.init_app(app)
limiter.init_app(app)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "bank-queue-system-secure-key-2026")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///bank_queue.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

@app.after_request
def set_security_headers(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

@app.errorhandler(429)
def ratelimit_handler(e):
    if request.path == "/login":
        flash("Too many login attempts. Please wait 1 minute before trying again.", "danger")
        return render_template("login.html"), 429

    if request.is_json or request.path.startswith("/user/get-token"):
        return jsonify({"error": "Rate limit exceeded. Please wait a minute before requesting another token."}), 429

    flash("Too many requests. Please slow down and try again.", "danger")
    return redirect("/")

    
# Flask-Login & Database Setup
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)   
login_manager.login_view = "login" 

from app.models import db   
db.init_app(app)

from app.models import User 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from app.routes import auth, admin, employee, user

auth.auth(app)
admin.admin(app)
employee.employee(app)
user.user(app)

with app.app_context():
    db.create_all()

IST = pytz.timezone("Asia/Kolkata")

@app.template_filter("ist_time")
def ist_time(value):
    if not value:
        return "-"
    if value.tzinfo is None:
        value = pytz.utc.localize(value)
    return value.astimezone(IST).strftime("%d-%b %I:%M %p")

if __name__ == "__main__":
    app.run(debug=True)