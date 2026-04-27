"""
models.py — Modelos de la base de datos (SQLAlchemy).
Fase 1: Usuario y Proyecto.
Schema sincronizado con el script SQL oficial.
"""
from datetime import datetime, timezone, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

# ── Zona horaria de Bolivia (UTC-4, sin horario de verano) ──
BOLIVIA_TZ = timezone(timedelta(hours=-4))


def now_bolivia():
    """Devuelve la fecha/hora actual en hora de Bolivia (UTC-4)."""
    return datetime.now(BOLIVIA_TZ).replace(tzinfo=None)  # guarda como naive local


class Usuario(UserMixin, db.Model):
    """
    Tabla: usuario
    Campos: id_user, user, password, fecha_creacion, activo
    """
    __tablename__ = 'usuario'

    id_user         = db.Column(db.Integer, primary_key=True)
    user            = db.Column(db.String(50), unique=True, nullable=False)
    password        = db.Column(db.String(255), nullable=False)
    fecha_creacion  = db.Column(db.DateTime, default=now_bolivia, nullable=False)
    activo          = db.Column(db.Boolean, default=True, nullable=False)

    # Relación 1:N con Proyecto
    proyectos = db.relationship('Proyecto', backref='owner', lazy=True,
                                cascade='all, delete-orphan')

    def get_id(self):
        return str(self.id_user)

    def set_password(self, plain_password: str):
        """Genera y almacena el hash de la contraseña."""
        self.password = generate_password_hash(plain_password)

    def check_password(self, plain_password: str) -> bool:
        """Verifica la contraseña contra el hash almacenado."""
        return check_password_hash(self.password, plain_password)

    def __repr__(self):
        return f'<Usuario {self.user}>'


class Proyecto(db.Model):
    """
    Tabla: proyecto
    Campos: id_proyecto, nombre, fecha_creacion, id_user
    """
    __tablename__ = 'proyecto'

    id_proyecto    = db.Column(db.Integer, primary_key=True)
    nombre         = db.Column(db.String(150), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=now_bolivia, nullable=False)
    id_user        = db.Column(db.Integer,
                               db.ForeignKey('usuario.id_user', ondelete='CASCADE'),
                               nullable=False)

    def __repr__(self):
        return f'<Proyecto {self.nombre}>'
