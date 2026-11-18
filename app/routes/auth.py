from flask import render_template, request, redirect, session, flash, url_for
from app.forms import RegisterForm
from app.models import *
from flask import flash,redirect, url_for
from app.models import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import logout_user, login_required
from email_validator import validate_email, EmailNotValidError
import re
from app import limiter


def auth(app):
    with app.app_context():

        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(username="admin", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)

        emp = User.query.filter_by(username="emp").first()
        if not emp:
            emp = User(username="emp", role="employee")
            
            emp.set_password("emp123")
            db.session.add(emp)

        db.session.commit()


    @app.route("/")
    def home_page():
        return render_template("index.html")
    
    @app.route("/register", methods=["GET", "POST"])
    def register():

        form = RegisterForm()

        if form.validate_on_submit():

            username=form.username.data.strip()
            email=form.email.data.strip()
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Username already exists!", "danger")
                return render_template("register.html", form=form)
            user = User(
                username=username,
                
                role="user"
            )

            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        
        return render_template("register.html", form=form)

    
    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit("5 per minute", methods=["POST"])
    def login():
        if request.method == "POST":

            username = request.form.get("username")
            password = request.form.get("password")
            role = request.form.get("role")
          
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                if user.role != role:
                    flash("Role mismatch", "danger")
                    return redirect(url_for("login"))

                session["user_id"] = user.id
                session["role"] = user.role
                session["username"] = user.username

                flash("Login successful!", "success")

                
                if role == "admin":
                    return redirect(url_for("admin_dashboard"))

                elif role == "employee":
                    return redirect(url_for("employee_dashboard"))

                else:
                    return redirect(url_for("user_dashboard"))

            flash("Invalid credentials", "danger")
            return redirect(url_for("login"))


        return render_template("login.html")
    
    @app.route("/logout")

    def logout():
        session.clear()
        flash("You have been logged out successfully", "success")
        return redirect(url_for("login"))

    @app.route("/display")
    def lobby_display():
        active_serving = Token.query.filter_by(status="serving").all()
        upcoming_tokens = Token.query.filter_by(status="waiting")\
                                     .order_by(Token.created_at.asc())\
                                     .limit(6).all()
        # Waiting count by service
        services = ["Deposit", "Withdrawal", "Account Help", "Jewel Loan", "Account Opening"]
        queue_counts = {
            s: Token.query.filter_by(service_type=s, status="waiting").count()
            for s in services
        }
        return render_template(
            "display.html",
            active_serving=active_serving,
            upcoming_tokens=upcoming_tokens,
            queue_counts=queue_counts
        )
