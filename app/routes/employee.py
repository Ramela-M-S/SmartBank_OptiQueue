from datetime import timedelta
from datetime import datetime
from app.models import Token,db
from flask import render_template,session, redirect, flash
from app import socketio
from app.decorators import role_required


def employee(app):
    @app.route("/employee")
    @role_required("employee")
    def employee_dashboard():
        flash("Welcome Staff!", "success")
        services = db.session.query(Token.service_type).distinct().all()
        return render_template("employee_services.html", services=services)
        
    @app.route("/employee/service/<service>")
    @role_required("employee")
    def service_dashboard(service):
        queue = Token.query.filter(
            Token.service_type == service,
            Token.status.in_(["waiting", "serving"])
        ).order_by(Token.created_at.asc()).all()

        return render_template(
            "dashboard_employee.html",
            queue=queue,
            service=service
        )

    @app.route("/employee/call-next/<service>", methods=["POST"])
    @role_required("employee")
    def call_next(service):
        employee_id = session.get("user_id")
        starvation_threshold = datetime.utcnow() - timedelta(minutes=15)

        currently_serving = Token.query.filter_by(
            assigned_employee_id=employee_id,
            status="serving"
        ).first()
        
        if currently_serving:
            flash(f"Please complete token {currently_serving.token_number} before calling next.", "warning")
            return {"message": f"Please complete token {currently_serving.token_number} before calling next"}, 400

        # Prioritize regular tickets waiting past starvation threshold
        next_token = Token.query.filter(
            Token.status == "waiting",
            Token.service_type == service,
            Token.priority == 2,
            Token.created_at <= starvation_threshold
        ).order_by(Token.created_at.asc()).first()

        # Otherwise serve by priority tier followed by FIFO
        if not next_token:
            next_token = Token.query.filter(
                Token.status == "waiting",
                Token.service_type == service
            ).order_by(
                Token.priority.asc(),
                Token.created_at.asc()
            ).first()

        if not next_token:
            flash("No waiting tokens for this service.", "info")
            return {"message": "No waiting tokens"}, 404

        next_token.status = "serving"
        next_token.assigned_employee_id = employee_id
        next_token.served_at = datetime.utcnow()
        db.session.commit()

        socketio.emit("token_called", {
            "token": next_token.token_number,
            "service": service,
            "user_id": next_token.user_id,
            "counter": f"Counter {employee_id}"
        })
        flash(f"Serving Token {next_token.token_number}", "success")
        return {"token": next_token.token_number}
    
    @app.route("/employee/mark-done/<service>", methods=["POST"])
    @role_required("employee")
    def mark_done(service):
        employee_id = session.get("user_id")

        current = Token.query.filter_by(
            status="serving",
            service_type=service,
            assigned_employee_id=employee_id
        ).first()

        if not current:
            current = Token.query.filter_by(
                status="serving",
                service_type=service
            ).first()

        if not current:
            flash("No active token being served to mark as done.", "warning")
            return {"message": "No active token being served"}, 400

        current.status = "completed"
        current.completed_at = datetime.utcnow()
        db.session.commit()

        socketio.emit("token_completed", {
            "token": current.token_number,
            "service": service
        })
        flash(f"Token {current.token_number} marked as completed.", "success")
        return {"message": "Token completed"}