from flask import Flask
from datetime import datetime
import pytz
app = Flask(__name__)

app.config["SECRET_KEY"] = "your-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bank_queue.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

from app.models import db   
db.init_app(app)


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