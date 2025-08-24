# app/__init__.py
from flask import Flask
from .sse_manager import SseManager
import queue

def create_app():
    app = Flask(__name__)
    app.sse_manager = SseManager()

    from .main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api.routes import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
