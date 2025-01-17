from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from sqlalchemy.orm import Session
from typing import List, Union

from src.core.database import get_db
from src.models.user import User, RoleType


def get_current_user():
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    db: Session = get_db()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    return user


def login_required():
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            return func(*args, **kwargs)

        return wrapped

    return decorator


def role_required(allowed_roles: Union[RoleType, List[RoleType]]):
    if isinstance(allowed_roles, RoleType):
        allowed_roles = [allowed_roles]

    def decorator(func):
        @wraps(func)
        @login_required()
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if user.role not in allowed_roles:
                return (
                    jsonify(
                        {
                            "error": "Permission denied",
                            "message": f"Required roles: {[role.value for role in allowed_roles]}",
                        }
                    ),
                    403,
                )
            return func(*args, **kwargs)

        return wrapped

    return decorator


def admin_required():
    return role_required(RoleType.ADMIN)


def guest_not_allowed():
    def decorator(func):
        @wraps(func)
        @login_required()
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if user.role == RoleType.GUEST:
                return (
                    jsonify(
                        {
                            "error": "Permission denied",
                            "message": "This endpoint is not accessible for guest users",
                        }
                    ),
                    403,
                )
            return func(*args, **kwargs)

        return wrapped

    return decorator
