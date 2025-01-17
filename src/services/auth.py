from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from uuid import UUID
import jwt
from authlib.integrations.flask_client import OAuth

from src.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.models.user import User, RefreshToken, PasswordResetToken, RoleType
from src.core.exceptions import (
    InvalidCredentialsError,
    TokenExpiredError,
    UserNotFoundError,
    TokenInvalidError,
)
from src.config.settings import settings


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.oauth = OAuth()
        self._setup_oauth_providers()

    def _setup_oauth_providers(self):
        # Setup Google OAuth
        self.oauth.register(
            name="google",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            access_token_url="https://accounts.google.com/o/oauth2/token",
            access_token_params=None,
            authorize_url="https://accounts.google.com/o/oauth2/auth",
            authorize_params=None,
            api_base_url="https://www.googleapis.com/oauth2/v1/",
            client_kwargs={"scope": "openid email profile"},
        )

        # Setup GitHub OAuth
        self.oauth.register(
            name="github",
            client_id=settings.GITHUB_CLIENT_ID,
            client_secret=settings.GITHUB_CLIENT_SECRET,
            access_token_url="https://github.com/login/oauth/access_token",
            access_token_params=None,
            authorize_url="https://github.com/login/oauth/authorize",
            authorize_params=None,
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "user:email"},
        )

    def authenticate_user(self, email: str, password: str) -> Tuple[User, str, str]:
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise InvalidCredentialsError("User account is deactivated")

        access_token = create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)

        return user, access_token, refresh_token

    def register_user(
        self, email: str, password: str, role: RoleType = RoleType.USER
    ) -> User:
        if self.db.query(User).filter(User.email == email).first():
            raise ValueError("Email already registered")

        user = User(email=email, password_hash=get_password_hash(password), role=role)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def _create_refresh_token(self, user_id: UUID) -> str:
        token = create_refresh_token(user_id)
        expires_at = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        refresh_token = RefreshToken(
            user_id=user_id, token=token, expires_at=expires_at
        )
        self.db.add(refresh_token)
        self.db.commit()

        return token

    def refresh_tokens(self, refresh_token: str) -> Tuple[str, str]:
        try:
            payload = decode_token(refresh_token)
            if payload["type"] != "refresh":
                raise TokenInvalidError("Invalid token type")

            token_record = (
                self.db.query(RefreshToken)
                .filter(
                    RefreshToken.token == refresh_token,
                    RefreshToken.is_revoked == False,
                )
                .first()
            )

            if not token_record or token_record.expires_at < datetime.utcnow():
                raise TokenExpiredError("Refresh token has expired")

            # Revoke the old refresh token
            token_record.is_revoked = True
            self.db.commit()

            # Create new tokens
            user_id = UUID(payload["sub"])
            new_access_token = create_access_token(user_id)
            new_refresh_token = self._create_refresh_token(user_id)

            return new_access_token, new_refresh_token

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise TokenInvalidError("Invalid refresh token")

    def create_password_reset_token(self, email: str) -> str:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise UserNotFoundError("User not found")

        # Invalidate any existing reset tokens
        existing_tokens = (
            self.db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.is_used == False,
            )
            .all()
        )
        for token in existing_tokens:
            token.is_used = True

        # Create new reset token
        token = jwt.encode(
            {
                "sub": str(user.id),
                "exp": datetime.utcnow() + timedelta(hours=24),
                "type": "reset",
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        self.db.add(reset_token)
        self.db.commit()

        return token

    def reset_password(self, token: str, new_password: str) -> bool:
        try:
            payload = decode_token(token)
            if payload["type"] != "reset":
                raise TokenInvalidError("Invalid token type")

            token_record = (
                self.db.query(PasswordResetToken)
                .filter(
                    PasswordResetToken.token == token,
                    PasswordResetToken.is_used == False,
                )
                .first()
            )

            if not token_record or token_record.expires_at < datetime.utcnow():
                raise TokenExpiredError("Reset token has expired")

            user = self.db.query(User).filter(User.id == UUID(payload["sub"])).first()
            if not user:
                raise UserNotFoundError("User not found")

            user.password_hash = get_password_hash(new_password)
            token_record.is_used = True
            self.db.commit()

            return True

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise TokenInvalidError("Invalid reset token")

    async def authenticate_oauth(
        self, provider: str, token_info: dict
    ) -> Tuple[User, str, str]:
        if provider == "google":
            user_info = await self.oauth.google.get("userinfo", token=token_info)
        elif provider == "github":
            user_info = await self.oauth.github.get("user", token=token_info)
        else:
            raise ValueError("Unsupported OAuth provider")

        email = user_info.get("email")
        if not email:
            raise ValueError("Email not provided by OAuth provider")

        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # Create new user if doesn't exist
            user = User(
                email=email,
                oauth_provider=provider,
                oauth_id=user_info.get("id"),
                is_verified=True,
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        access_token = create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)

        return user, access_token, refresh_token
