from flask import render_template, request, redirect, session, flash, url_for
from app.forms import RegisterForm
from app.models import User
from flask import flash,redirect, url_for
from app.models import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import logout_user, login_required


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

            # check duplicate user
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash("Username already exists!", "danger")
                return redirect(url_for("register"))

            # create user
            user = User(
                username=form.username.data,
                role="user"   
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))

        return render_template("register.html", form=form)
    
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":

            username = request.form.get("username")
            password = request.form.get("password")
            role = request.form.get("role")
            print(username, password, role)
            
          
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                if user.role != role:
                    flash("Role mismatch", "danger")
                    return redirect(url_for("login"))

                # STORE SESSION
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
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out successfully", "success")
        return redirect(url_for("login"))
