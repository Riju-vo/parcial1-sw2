"""
extensions.py — Instancias de Flask-SQLAlchemy y Flask-Login.
Se definen aquí para evitar importaciones circulares entre web_interface.py,
models.py, auth.py y projects.py.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

# Redirige al login cuando se requiere autenticación
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Inicia sesión para acceder a esta sección.'
login_manager.login_message_category = 'warning'
