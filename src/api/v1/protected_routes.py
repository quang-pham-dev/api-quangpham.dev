from flask import Blueprint, jsonify
from src.api.v1.deps import (
    login_required,
    admin_required,
    role_required,
    guest_not_allowed,
)
from src.models.user import RoleType

protected_bp = Blueprint("protected", __name__)


@protected_bp.route("/user-info")
@login_required()
def get_user_info():
    """Endpoint accessible by any authenticated user"""
    return jsonify({"message": "You are authenticated!"})


@protected_bp.route("/admin-only")
@admin_required()
def admin_only():
    """Endpoint accessible only by admins"""
    return jsonify({"message": "Welcome, admin!"})


@protected_bp.route("/user-and-admin")
@role_required([RoleType.USER, RoleType.ADMIN])
def user_and_admin():
    """Endpoint accessible by both users and admins, but not guests"""
    return jsonify({"message": "Welcome, user or admin!"})


@protected_bp.route("/no-guests")
@guest_not_allowed()
def no_guests():
    """Endpoint not accessible by guests"""
    return jsonify({"message": "Welcome, non-guest user!"})
