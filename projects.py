"""
projects.py — Blueprint de proyectos.
Rutas: /proyectos, /proyectos/nuevo, /proyectos/<id>, /proyectos/<id>/eliminar
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import Proyecto

projects_bp = Blueprint('projects', __name__, url_prefix='/proyectos')


@projects_bp.route('/')
@login_required
def index():
    """Dashboard: lista todos los proyectos del usuario logueado."""
    proyectos = Proyecto.query.filter_by(id_user=current_user.id_user)\
                              .order_by(Proyecto.fecha_creacion.desc())\
                              .all()
    return render_template('projects/index.html', proyectos=proyectos)


@projects_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    """Crear nuevo proyecto."""
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        if not nombre:
            flash('El nombre del proyecto es obligatorio.', 'danger')
        elif len(nombre) > 120:
            flash('El nombre no puede superar los 120 caracteres.', 'danger')
        else:
            proyecto = Proyecto(nombre=nombre, id_user=current_user.id_user)
            db.session.add(proyecto)
            db.session.commit()
            flash(f'Proyecto "{nombre}" creado correctamente.', 'success')
            return redirect(url_for('projects.index'))

    return render_template('projects/nuevo.html')


@projects_bp.route('/<int:id_proyecto>')
@login_required
def detalle(id_proyecto):
    """Detalle de un proyecto (placeholder para Fase 2 — colecciones y resultados)."""
    proyecto = Proyecto.query.get_or_404(id_proyecto)
    # Verificar que el proyecto pertenece al usuario logueado
    if proyecto.id_user != current_user.id_user:
        abort(403)
    return render_template('projects/detalle.html', proyecto=proyecto)


@projects_bp.route('/<int:id_proyecto>/eliminar', methods=['POST'])
@login_required
def eliminar(id_proyecto):
    """Eliminar un proyecto."""
    proyecto = Proyecto.query.get_or_404(id_proyecto)
    if proyecto.id_user != current_user.id_user:
        abort(403)
    nombre = proyecto.nombre
    db.session.delete(proyecto)
    db.session.commit()
    flash(f'Proyecto "{nombre}" eliminado.', 'info')
    return redirect(url_for('projects.index'))
