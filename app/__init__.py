from flask import Flask
from datetime import datetime
import pytz
app = Flask(__name__)
from flask_login import LoginManager

login_manager = LoginManager()
app.config["SECRET_KEY"] = "your-secret-key"
import os

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///bank_queue.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
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

    # convert UTC → IST
    if value.tzinfo is None:
        value = pytz.utc.localize(value)

    return value.astimezone(IST).strftime("%d-%b %I:%M %p")
if __name__ == "__main__":
    app.run(debug=True)