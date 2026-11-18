from flask import render_template, session, redirect, request, jsonify
from app.models import db, Token, DailySequence
from datetime import date, datetime
from app import socketio
from sqlalchemy import or_, and_
from app.decorators import role_required
from app import limiter
import threading



SERVICE_PREFIXES = {
    "Deposit": "DP",
    "Withdrawal": "WD",
    "Account Help": "AH",
    "Jewel Loan": "JL",
    "Account Opening": "AO"
}

DEFAULT_SERVICE_TIME = {
    "Deposit": 4.0,
    "Withdrawal": 2.5,
    "Account Help": 6.0,
    "Jewel Loan": 8.0,
    "Account Opening": 5.0
}

sequence_lock = threading.Lock()

def generate_service_token(service_type):
    today = date.today()
    prefix = SERVICE_PREFIXES.get(service_type, "TK")
 
    with sequence_lock:
        seq = DailySequence.query.filter_by(
            service_type=service_type, 
            date=today
        ).first()
        if not seq:
            seq = DailySequence(service_type=service_type, date=today, last_number=1)
            db.session.add(seq)
        else:
            seq.last_number += 1
        db.session.commit()
        return f"{prefix}-{seq.last_number:03d}"


def calculate_dynamic_wait_time(service_type, people_ahead):
    """
    Calculates wait time dynamically using:
    1. Rolling Average Handling Time (AHT) from recently completed tokens
    2. Number of active tellers currently serving this service (M/M/c queue)
    """
    if people_ahead <= 0:
        return 0, 1, DEFAULT_SERVICE_TIME.get(service_type, 4.0)

    active_tellers = db.session.query(Token.assigned_employee_id)\
        .filter(Token.service_type == service_type, Token.status == "serving")\
        .distinct().count()

    active_tellers = max(1, active_tellers)

    recent_tokens = Token.query.filter(
        Token.service_type == service_type,
        Token.status == "completed",
        Token.served_at.isnot(None),
        Token.completed_at.isnot(None)
    ).order_by(Token.completed_at.desc()).limit(10).all()

    if recent_tokens:
        durations = [
            (t.completed_at - t.served_at).total_seconds() / 60.0
            for t in recent_tokens
            if (t.completed_at - t.served_at).total_seconds() > 0
        ]
        avg_handling_time = round(sum(durations) / len(durations), 1) if durations else DEFAULT_SERVICE_TIME.get(service_type, 4.0)
    else:
        avg_handling_time = DEFAULT_SERVICE_TIME.get(service_type, 4.0)

    estimated_wait = round((people_ahead / active_tellers) * avg_handling_time)
    return max(1, estimated_wait), active_tellers, avg_handling_time


def count_people_ahead(target_token):
    """
    Counts waiting customers scheduled ahead based on priority,
    breaking ties using creation timestamp.
    """
    return Token.query.filter(
        Token.service_type == target_token.service_type,
        Token.status == "waiting",
        Token.id != target_token.id,
        or_(
            Token.priority < target_token.priority,
            and_(
                Token.priority == target_token.priority,
                Token.created_at < target_token.created_at
            )
        )
    ).count()


def user(app):
    @app.route("/user/dashboard")
    @role_required("user")
    def user_dashboard():
        user_id = session.get("user_id")

        active_token = Token.query.filter(
            Token.user_id == user_id,
            Token.status.in_(["waiting", "serving"])
        ).first()

        people_ahead = 0
        wait_time = 0
        active_tellers = 1

        if active_token:
            people_ahead = count_people_ahead(active_token)

            wait_time, active_tellers, _ = calculate_dynamic_wait_time(
                active_token.service_type, 
                people_ahead
            )

        return render_template(
            "dashboard_user.html",
            username=session.get("username"),
            active_token=active_token,
            people_ahead=people_ahead,
            wait_time=wait_time,
            active_tellers=active_tellers
        )
    
    @app.route("/user/get-token", methods=["POST"])
    @role_required("user")
    @limiter.limit("3 per minute")
    def get_token():
        user_id = session.get("user_id")

        active_token = Token.query.filter(
            Token.user_id == user_id,
            Token.status.in_(["waiting", "serving"])
        ).first()

        if active_token:
            return jsonify({
                "error": f"You already have an active token ({active_token.token_number}) for {active_token.service_type}!"
            }), 400

        service = request.form.get("service")
        if not service:
            return jsonify({"error": "Service type is required"}), 400

        priority = int(request.form.get("priority", 2))

        try:
            base_token = generate_service_token(service)
            token_number = f"SR-{base_token}" if priority == 1 else base_token

            token = Token(
                token_number=token_number,
                service_type=service,
                priority=priority,
                status="waiting",
                user_id=user_id,
                created_at=datetime.utcnow()
            )
            db.session.add(token)
            db.session.commit()

            socketio.emit("token_generated", {
                "token": token_number,
                "service": service,
                "created_at": token.created_at.strftime("%I:%M %p")
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Failed to generate token, please try again"}), 500

        people_ahead = count_people_ahead(token)
        wait_time, active_tellers, avg_time = calculate_dynamic_wait_time(service, people_ahead)

        return jsonify({
            "token": token_number,
            "people_ahead": people_ahead,
            "wait_time": wait_time,
            "active_tellers": active_tellers,
            "avg_service_time": avg_time,
            "service": service
        })

    @app.route("/user/cancel-token", methods=["POST"])
    @role_required("user")
    def cancel_token():
        user_id = session.get("user_id")
        active_token = Token.query.filter(
            Token.user_id == user_id,
            Token.status == "waiting"
        ).first()

        if not active_token:
            return jsonify({"error": "No active waiting token to cancel"}), 400

        active_token.status = "cancelled"
        db.session.commit()
        return jsonify({"message": "Token cancelled successfully"})