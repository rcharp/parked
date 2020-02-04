from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail
from flask_wtf import CsrfProtect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
from threading import Lock

debug_toolbar = DebugToolbarExtension()
mail = Mail()
csrf = CsrfProtect()
db = SQLAlchemy()
login_manager = LoginManager()
cache = Cache(config={'CACHE_TYPE': 'redis'})
timeout = 9999999999999999
lock = Lock()
