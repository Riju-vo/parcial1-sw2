"""
auth.py — Blueprint de autenticación.
Rutas: /auth/login, /auth/register, /auth/logout
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import Usuario

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('projects.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm  = request.form.get('confirm', '').strip()

        # Validaciones básicas
        if not username or not password:
            flash('Todos los campos son obligatorios.', 'danger')
        elif len(username) < 3:
            flash('El nombre de usuario debe tener al menos 3 caracteres.', 'danger')
        elif len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
        elif password != confirm:
            flash('Las contraseñas no coinciden.', 'danger')
        elif Usuario.query.filter_by(user=username).first():
            flash('Ese nombre de usuario ya está en uso.', 'danger')
        else:
            nuevo_usuario = Usuario(user=username)
            nuevo_usuario.set_password(password)
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('¡Cuenta creada! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('projects.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        usuario = Usuario.query.filter_by(user=username).first()

        if not usuario or not usuario.check_password(password):
            flash('Usuario o contraseña incorrectos.', 'danger')
        else:
            login_user(usuario, remember=request.form.get('remember') == 'on')
            # Redirigir al destino original si viene de @login_required
            next_page = request.args.get('next')
            flash(f'¡Bienvenido, {usuario.user}!', 'success')
            return redirect(next_page or url_for('projects.index'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))
