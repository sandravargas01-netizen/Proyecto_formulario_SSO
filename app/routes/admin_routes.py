from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Acceso denegado. Requiere rol administrador', 'danger')
            return redirect(url_for('paciente.list'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard."""
    from app.models.user import User
    from app.models.paciente import Paciente
    
    total_users = User.query.count()
    total_pacientes = Paciente.query.count()
    active_pacientes = Paciente.query.filter_by(estado='activo').count()
    
    context = {
        'total_users': total_users,
        'total_pacientes': total_pacientes,
        'active_pacientes': active_pacientes
    }
    return render_template('admin/dashboard.html', **context)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management page."""
    from app.models.user import User
    
    page = request.args.get('page', 1, type=int)
    users_list = User.query.paginate(page=page, per_page=10)
    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Reports page."""
    return render_template('admin/reports.html')
