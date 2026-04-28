"""
models.py — Modelos de la base de datos (SQLAlchemy).
Fase 1: Usuario, Proyecto.
Fase 2: Coleccion, Resultado + campo url en Proyecto.
"""
from datetime import datetime, timezone, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

# ── Zona horaria de Bolivia (UTC-4, sin horario de verano) ──
BOLIVIA_TZ = timezone(timedelta(hours=-4))


def now_bolivia():
    """Devuelve la fecha/hora actual en hora de Bolivia (UTC-4)."""
    return datetime.now(BOLIVIA_TZ).replace(tzinfo=None)


# ── Mapeo de niveles de riesgo (inglés → español para el CHECK de BD) ──
RISK_MAP = {
    'High':     'Alto',
    'Critical': 'Crítico',
    'Medium':   'Medio',
    'Low':      'Bajo',
    'Unknown':  'Bajo',
    'Error':    'Bajo',
}


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id_user        = db.Column(db.Integer, primary_key=True)
    user           = db.Column(db.String(50), unique=True, nullable=False)
    password       = db.Column(db.String(255), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=now_bolivia, nullable=False)
    activo         = db.Column(db.Boolean, default=True, nullable=False)

    proyectos = db.relationship('Proyecto', backref='owner', lazy=True,
                                cascade='all, delete-orphan')

    def get_id(self):
        return str(self.id_user)

    def set_password(self, plain_password: str):
        self.password = generate_password_hash(plain_password)

    def check_password(self, plain_password: str) -> bool:
        return check_password_hash(self.password, plain_password)

    def __repr__(self):
        return f'<Usuario {self.user}>'


class Proyecto(db.Model):
    __tablename__ = 'proyecto'

    id_proyecto    = db.Column(db.Integer, primary_key=True)
    nombre         = db.Column(db.String(150), nullable=False)
    url            = db.Column(db.String(500), nullable=True)   # URL objetivo del proyecto
    fecha_creacion = db.Column(db.DateTime, default=now_bolivia, nullable=False)
    id_user        = db.Column(db.Integer,
                               db.ForeignKey('usuario.id_user', ondelete='CASCADE'),
                               nullable=False)

    colecciones = db.relationship('Coleccion', backref='proyecto', lazy=True,
                                  cascade='all, delete-orphan',
                                  order_by='Coleccion.fecha_escaneo.desc()')

    def __repr__(self):
        return f'<Proyecto {self.nombre}>'


class Coleccion(db.Model):
    """Representa una sesión de escaneo (snapshot en el tiempo)."""
    __tablename__ = 'coleccion'

    id_coleccion  = db.Column(db.Integer, primary_key=True)
    fecha_escaneo = db.Column(db.DateTime, default=now_bolivia, nullable=False)
    id_proyecto   = db.Column(db.Integer,
                              db.ForeignKey('proyecto.id_proyecto', ondelete='CASCADE'),
                              nullable=False)

    resultados = db.relationship('Resultado', backref='coleccion', lazy=True,
                                 cascade='all, delete-orphan')

    @property
    def conteo_por_riesgo(self):
        """Devuelve dict con conteo de resultados por nivel de riesgo."""
        conteo = {'Crítico': 0, 'Alto': 0, 'Medio': 0, 'Bajo': 0}
        for r in self.resultados:
            if r.nivel_riesgo in conteo:
                conteo[r.nivel_riesgo] += 1
        return conteo

    def __repr__(self):
        return f'<Coleccion {self.id_coleccion} @ {self.fecha_escaneo}>'


class Resultado(db.Model):
    """Un resultado individual de vulnerabilidad dentro de un escaneo."""
    __tablename__ = 'resultado'

    id_resultado   = db.Column(db.Integer, primary_key=True)
    vulnerabilidad = db.Column(db.Text, nullable=False)
    estado         = db.Column(db.Text, default='Pendiente')
    nivel_riesgo   = db.Column(db.String(20))  # Bajo, Medio, Alto, Crítico

    id_coleccion   = db.Column(db.Integer,
                               db.ForeignKey('coleccion.id_coleccion', ondelete='CASCADE'),
                               nullable=False)

    def __repr__(self):
        return f'<Resultado {self.vulnerabilidad}: {self.nivel_riesgo}>'
