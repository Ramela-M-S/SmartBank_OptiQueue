from app.models import Token,db
from flask import render_template,session, redirect


def employee(app):
    

    @app.route("/employee")
    def employee_dashboard():
        if session.get("role") != "employee":
            return redirect("/login")
        services = db.session.query(Token.service_type).distinct().all()

        return render_template("employee_services.html", services=services)
        
    @app.route("/employee/service/<service>")
    def service_dashboard(service):

        queue = Token.query.filter_by(service_type=service)\
                            .order_by(Token.created_at.asc())\
                            .all()

        return render_template("dashboard_employee.html",
                            queue=queue,
                            service=service)

    @app.route("/employee/call-next/<service>", methods=["POST"])
    def call_next(service):

        employee_id = session.get("user_id")

        next_token = Token.query.filter_by(
            status="waiting",
            service_type=service
        ).order_by(Token.created_at.asc()).first()

        if not next_token:
            return {"message": "No waiting tokens"}

        next_token.status = "serving"
        next_token.assigned_employee_id = employee_id

        db.session.commit()

        return {"token": next_token.token_number}
    
    @app.route("/employee/mark-done/<service>", methods=["POST"])
    def mark_done(service):

        current = Token.query.filter_by(
            status="serving",
            service_type=service
        ).first()

        if not current:
            return {"message": "No active token"}

        db.session.delete(current)
        db.session.commit()

        return {"message": "Token completed"}