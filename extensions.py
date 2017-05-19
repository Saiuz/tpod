# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager

login_manager = LoginManager()
db = SQLAlchemy()
migrate = Migrate()
manager = Manager()
