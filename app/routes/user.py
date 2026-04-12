from flask import render_template, session, redirect, request, jsonify, redirect
from app.models import db, Token
from datetime import date

def generate_service_token(service_type):

    today = date.today()

    count = Token.query.filter(
        Token.service_type == service_type
    ).count()

    return count + 1

def user(app):
    @app.route("/user/dashboard")
    def user_dashboard():

      
        if session.get("role") != "user":
            return redirect("/login")

        return render_template("dashboard_user.html", username=session.get("username"))
    
    @app.route("/user/get-token", methods=["POST"])
    def get_token():

        if session.get("role") != "user":
            return jsonify({"error": "Unauthorized"}), 403

        service = request.form.get("service")

        SERVICE_TIME = {
            "Deposit": 4,
            "Withdrawal": 2,
            "Account Help": 6,
            "Jewel Loan": 8,
            "Account Opening": 5
        }

        
        token_number = str(generate_service_token(service))

        

        # save token
        token = Token(
            token_number=token_number,
            service_type=service,
            status="waiting",
            user_id=session["user_id"]
        )

        db.session.add(token)
        db.session.commit()


        people_ahead = Token.query.filter_by(
            service_type=service,
            status="waiting"
        ).count() - 1

        people_ahead = max(0, people_ahead)

        avg_time = SERVICE_TIME.get(service, 4)
        wait_time = people_ahead * avg_time

        return jsonify({
            "token": token_number,
            "people_ahead": people_ahead,
            "wait_time": wait_time,
            "service": service
        })