from flask import render_template, session, redirect, flash
from app.models import db, Token
from sqlalchemy import func
from datetime import datetime, date
from app.decorators import role_required

    
def admin(app):
    @app.route("/admin")
    @role_required("admin")
    def admin_dashboard():
        flash("Welcome Admin!", "success")
        tokens = Token.query.order_by(Token.created_at.desc()).all()

        today = date.today()

        total_tokens = Token.query.count()

        active_queue = Token.query.filter(
            Token.status.in_(["waiting", "serving"])
        ).count()

        waiting_tokens = Token.query.filter(Token.status == "waiting").all()

        avg_wait_time = 0
        if waiting_tokens:
            total_wait = sum(
                [(datetime.utcnow() - t.created_at).total_seconds()
                 for t in waiting_tokens]
            )
            avg_wait_time = round(total_wait / len(waiting_tokens) / 60, 2)  # in minutes

        withdraw = Token.query.filter_by(service_type="Withdraw").count()
        deposit = Token.query.filter_by(service_type="Deposit").count()
        account = Token.query.filter_by(service_type="Account Help").count()
        loan = Token.query.filter_by(service_type="Jewel Loan").count()

        recent = Token.query.order_by(Token.created_at.desc()).limit(10).all()

        return render_template(
            "dashboard_admin.html",
            total_tokens=total_tokens,
            active_tokens=active_queue,
            avg_wait_time=avg_wait_time,
            withdraw=withdraw,
            deposit=deposit,
            account=account,
            loan=loan,
            recent=recent
        )