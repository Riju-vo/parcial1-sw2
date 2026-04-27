"""
projects.py — Blueprint de proyectos.
Fase 1: CRUD básico de proyectos.
Fase 2: url en proyecto, historial de colecciones, detalle de colección.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import Proyecto, Coleccion, Resultado
import json

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


@projects_bp.route('/<int:id_proyecto>/dashboard')
@login_required
def dashboard(id_proyecto):
    """Dashboard visual: graficas de evolucion del proyecto."""
    proyecto = Proyecto.query.get_or_404(id_proyecto)
    if proyecto.id_user != current_user.id_user:
        abort(403)

    colecciones = Coleccion.query\
        .filter_by(id_proyecto=id_proyecto)\
        .order_by(Coleccion.fecha_escaneo.asc())\
        .all()

    # ── Series para grafica de barras apiladas (cronologico) ──
    fechas_etiquetas = [c.fecha_escaneo.strftime('%d/%m %H:%M') for c in colecciones]
    serie_critico, serie_alto, serie_medio, serie_bajo = [], [], [], []
    for col in colecciones:
        c = col.conteo_por_riesgo
        serie_critico.append(c['Crítico'])
        serie_alto.append(c['Alto'])
        serie_medio.append(c['Medio'])
        serie_bajo.append(c['Bajo'])

    # ── Totales globales para dona ──
    totales = {'Crítico': sum(serie_critico), 'Alto': sum(serie_alto),
               'Medio': sum(serie_medio), 'Bajo': sum(serie_bajo)}

    # ── Tabla de vulnerabilidades con tendencia ──
    # Recopilar todos los nombres de vulnerabilidades que aparecen en algun escaneo
    todos_nombres = set()
    for col in colecciones:
        for r in col.resultados:
            todos_nombres.add(r.vulnerabilidad)

    ORDER = ['Bajo', 'Medio', 'Alto', 'Crítico']
    tabla_vulnerabilidades = []
    for nombre in sorted(todos_nombres):
        # Recopilar resultados de cada escaneo para esta vulnerabilidad
        historial_vuln = []  # lista de (nivel_riesgo, estado) por coleccion
        for col in colecciones:
            encontrado = next((r for r in col.resultados if r.vulnerabilidad == nombre), None)
            historial_vuln.append(encontrado)

        ultimo = next((h for h in reversed(historial_vuln) if h is not None), None)
        penultimo_list = [h for h in historial_vuln if h is not None]
        penultimo = penultimo_list[-2] if len(penultimo_list) >= 2 else None

        ocurrencias = sum(1 for h in historial_vuln if h is not None)

        # Calcular tendencia comparando ultimo vs penultimo escaneo
        tendencia = None
        if ultimo and penultimo and ultimo.nivel_riesgo in ORDER and penultimo.nivel_riesgo in ORDER:
            idx_ultimo = ORDER.index(ultimo.nivel_riesgo)
            idx_penult = ORDER.index(penultimo.nivel_riesgo)
            if idx_ultimo > idx_penult:
                tendencia = 'empeora'
            elif idx_ultimo < idx_penult:
                tendencia = 'mejora'
            else:
                tendencia = 'estable'

        tabla_vulnerabilidades.append({
            'nombre': nombre,
            'nivel_actual': ultimo.nivel_riesgo if ultimo else None,
            'estado': ultimo.estado if ultimo else '—',
            'ocurrencias': ocurrencias,
            'tendencia': tendencia,
        })

    tabla_vulnerabilidades.sort(
        key=lambda v: ORDER.index(v['nivel_actual']) if v['nivel_actual'] in ORDER else -1,
        reverse=True
    )

    return render_template('projects/dashboard.html',
                           proyecto=proyecto,
                           colecciones=colecciones,
                           fechas_etiquetas=fechas_etiquetas,
                           serie_critico=serie_critico,
                           serie_alto=serie_alto,
                           serie_medio=serie_medio,
                           serie_bajo=serie_bajo,
                           totales=totales,
                           tabla_vulnerabilidades=tabla_vulnerabilidades)


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
