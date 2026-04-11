from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  


    tokens_created = db.relationship(
        "Token",
        foreign_keys="Token.user_id",
        backref="user",
        lazy=True
    )

    tokens_assigned = db.relationship(
        "Token",
        foreign_keys="Token.assigned_employee_id",
        backref="employee",
        lazy=True
    )


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Token(db.Model):
    __tablename__ = "token"

    id = db.Column(db.Integer, primary_key=True)
    token_number = db.Column(db.String(10), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)

    status = db.Column(
        db.String(20),
        default="waiting"
    )  

   
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    assigned_employee_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

  
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    served_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)