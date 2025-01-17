from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

from src.core.database import db
from src.core.exceptions import register_error_handlers
from src.api.v1.auth.routes import auth_bp
from src.api.v1.protected_routes import protected_bp
from src.config.settings import settings


def create_app():
    app = Flask(__name__)

    # Configure app
    app.config.from_object(settings)

    # Initialize extensions
    CORS(app)
    db.init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(protected_bp, url_prefix="/api/v1/protected")

    # Register error handlers
    register_error_handlers(app)

    @app.route("/health")
    def health_check():
        return {"status": "healthy"}, 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
