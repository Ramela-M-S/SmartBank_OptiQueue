from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify

def role_required(allowed_roles):
    """
    Role-Based Access Control (RBAC) Decorator.
    Accepts a single role string or a list of roles.
    Example:
        @role_required("admin")
        @role_required("employee")
        @role_required(["employee", "admin"])
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get("user_id")
            user_role = session.get("role")

            if not user_id or not user_role:
                if request.is_json or request.method == "POST":
                    return jsonify({"error": "Authentication required. Please log in."}), 401
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login"))

            if user_role not in allowed_roles:
                if request.is_json or request.method == "POST":
                    return jsonify({"error": "Forbidden: You do not have permission for this resource."}), 403
                flash("Access denied: You do not have permission to view this page.", "danger")
                return redirect(url_for("home_page"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator