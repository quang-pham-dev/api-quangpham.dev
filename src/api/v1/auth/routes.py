from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.auth import AuthService
from src.schemas.auth import (
    UserCreate,
    UserLogin,
    TokenResponse,
    PasswordResetRequest,
    PasswordReset,
    RefreshTokenRequest,
)
from src.core.exceptions import (
    InvalidCredentialsError,
    TokenExpiredError,
    UserNotFoundError,
    TokenInvalidError,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = UserCreate(**request.get_json())
    db: Session = get_db()
    auth_service = AuthService(db)

    try:
        user = auth_service.register_user(email=data.email, password=data.password)
        return (
            jsonify(
                {"message": "User registered successfully", "user_id": str(user.id)}
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    data = UserLogin(**request.get_json())
    db: Session = get_db()
    auth_service = AuthService(db)

    try:
        user, access_token, refresh_token = auth_service.authenticate_user(
            email=data.email, password=data.password
        )
        return (
            jsonify(
                TokenResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_type="bearer",
                ).dict()
            ),
            200,
        )
    except InvalidCredentialsError as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    data = RefreshTokenRequest(**request.get_json())
    db: Session = get_db()
    auth_service = AuthService(db)

    try:
        access_token, refresh_token = auth_service.refresh_tokens(data.refresh_token)
        return (
            jsonify(
                TokenResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_type="bearer",
                ).dict()
            ),
            200,
        )
    except (TokenExpiredError, TokenInvalidError) as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = PasswordResetRequest(**request.get_json())
    db: Session = get_db()
    auth_service = AuthService(db)

    try:
        token = auth_service.create_password_reset_token(data.email)
        # In a real application, you would send this token via email
        # For development, we'll just return it
        return jsonify({"message": "Password reset token created", "token": token}), 200
    except UserNotFoundError as e:
        return jsonify({"error": str(e)}), 404


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = PasswordReset(**request.get_json())
    db: Session = get_db()
    auth_service = AuthService(db)

    try:
        auth_service.reset_password(data.token, data.new_password)
        return jsonify({"message": "Password reset successfully"}), 200
    except (TokenExpiredError, TokenInvalidError, UserNotFoundError) as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.route("/oauth/<provider>")
def oauth_login(provider):
    db: Session = get_db()
    auth_service = AuthService(db)

    return auth_service.oauth.create_client(provider).authorize_redirect(
        redirect_uri=current_app.config[f"{provider.upper()}_REDIRECT_URI"]
    )


@auth_bp.route("/oauth/<provider>/callback")
async def oauth_callback(provider):
    db: Session = get_db()
    auth_service = AuthService(db)

    token = auth_service.oauth.create_client(provider).authorize_access_token()
    try:
        user, access_token, refresh_token = await auth_service.authenticate_oauth(
            provider, token
        )
        return (
            jsonify(
                TokenResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_type="bearer",
                ).dict()
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
