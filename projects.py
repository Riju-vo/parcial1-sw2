"""
projects.py — Blueprint de proyectos.
Fase 1: CRUD básico de proyectos.
Fase 2: url en proyecto, historial de colecciones, detalle de colección.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import Proyecto, Coleccion, Resultado

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
        url    = request.form.get('url', '').strip()

        if not nombre:
            flash('El nombre del proyecto es obligatorio.', 'danger')
        elif len(nombre) > 150:
            flash('El nombre no puede superar los 150 caracteres.', 'danger')
        else:
            proyecto = Proyecto(
                nombre=nombre,
                url=url or None,
                id_user=current_user.id_user
            )
            db.session.add(proyecto)
            db.session.commit()
            flash(f'Proyecto "{nombre}" creado correctamente.', 'success')
            return redirect(url_for('projects.detalle', id_proyecto=proyecto.id_proyecto))

    return render_template('projects/nuevo.html')


@projects_bp.route('/<int:id_proyecto>')
@login_required
def detalle(id_proyecto):
    """Detalle del proyecto: info + historial de escaneos (colecciones)."""
    proyecto = Proyecto.query.get_or_404(id_proyecto)
    if proyecto.id_user != current_user.id_user:
        abort(403)

    # Colecciones ordenadas de más reciente a más antigua
    colecciones = Coleccion.query\
        .filter_by(id_proyecto=id_proyecto)\
        .order_by(Coleccion.fecha_escaneo.desc())\
        .all()

    # Calcular conteo por riesgo para cada colección (para la tabla resumen)
    historial = []
    for col in colecciones:
        conteo = {'Crítico': 0, 'Alto': 0, 'Medio': 0, 'Bajo': 0}
        for r in col.resultados:
            if r.nivel_riesgo in conteo:
                conteo[r.nivel_riesgo] += 1
        historial.append({'coleccion': col, 'conteo': conteo})

    return render_template('projects/detalle.html',
                           proyecto=proyecto,
                           historial=historial)


@projects_bp.route('/<int:id_proyecto>/coleccion/<int:id_coleccion>')
@login_required
def coleccion_detalle(id_proyecto, id_coleccion):
    """Detalle de un escaneo específico (colección)."""
    proyecto = Proyecto.query.get_or_404(id_proyecto)
    if proyecto.id_user != current_user.id_user:
        abort(403)

    coleccion = Coleccion.query.get_or_404(id_coleccion)
    if coleccion.id_proyecto != id_proyecto:
        abort(404)

    # Colección anterior (para comparación)
    coleccion_anterior = Coleccion.query\
        .filter(
            Coleccion.id_proyecto == id_proyecto,
            Coleccion.fecha_escaneo < coleccion.fecha_escaneo
        )\
        .order_by(Coleccion.fecha_escaneo.desc())\
        .first()

    # Construir mapa de resultados anteriores para comparar: {vulnerabilidad: nivel_riesgo}
    resultados_anteriores = {}
    if coleccion_anterior:
        for r in coleccion_anterior.resultados:
            resultados_anteriores[r.vulnerabilidad] = r.nivel_riesgo

    resultados = coleccion.resultados

    return render_template('projects/coleccion.html',
                           proyecto=proyecto,
                           coleccion=coleccion,
                           resultados=resultados,
                           resultados_anteriores=resultados_anteriores)


@projects_bp.route('/<int:id_proyecto>/eliminar', methods=['POST'])
@login_required
def eliminar(id_proyecto):
    """Eliminar un proyecto (y en cascada sus colecciones y resultados)."""
    proyecto = Proyecto.query.get_or_404(id_proyecto)
    if proyecto.id_user != current_user.id_user:
        abort(403)
    nombre = proyecto.nombre
    db.session.delete(proyecto)
    db.session.commit()
    flash(f'Proyecto "{nombre}" eliminado.', 'info')
    return redirect(url_for('projects.index'))
