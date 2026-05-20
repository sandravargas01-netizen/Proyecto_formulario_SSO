# Salud Ocupacional - Sistema de Gestión

Una aplicación web desarrollada con Flask para la gestión de pacientes y usuarios en un contexto de salud ocupacional.

## 🚀 Características

- **Autenticación de usuarios** con Flask-Login y contraseñas hasheadas
- **Gestión de pacientes** (CRUD completo)
- **Panel de administración** con estadísticas y gestión de usuarios
- **Base de datos SQLite** con SQLAlchemy ORM
- **Formularios validados** con Flask-WTF
- **Interfaz responsiva** con Bootstrap 5
- **Plantillas Jinja2** para renderizado dinámico

## 📋 Requisitos Previos

- Python 3.8+
- pip (gestor de paquetes de Python)

## ⚙️ Instalación

### 1. Clonar o descargar el proyecto

```bash
cd Proyecto_formulario
```

### 2. Crear un entorno virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones (opcional)
# Por defecto usa SQLite local
```

## 🏃 Ejecutar la Aplicación

```bash
python run.py
```

La aplicación estará disponible en: **http://localhost:5000**

## 📦 Estructura del Proyecto

```
Proyecto_formulario/
├── app/
│   ├── models/              # Modelos de base de datos
│   │   ├── user.py         # Modelo de usuario
│   │   └── paciente.py     # Modelo de paciente
│   ├── routes/             # Blueprints de rutas
│   │   ├── auth_routes.py     # Autenticación
│   │   ├── paciente_routes.py # CRUD de pacientes
│   │   └── admin_routes.py    # Panel admin
│   ├── forms/              # Formularios Flask-WTF
│   │   ├── login_form.py
│   │   └── paciente_form.py
│   ├── templates/          # Plantillas Jinja2
│   │   ├── auth/
│   │   ├── pacientes/
│   │   └── admin/
│   ├── static/             # Archivos estáticos
│   │   ├── css/style.css
│   │   └── js/main.js
│   ├── __init__.py         # Factory de aplicación
│   └── config.py           # Configuraciones
├── instance/               # Base de datos (ignorado en Git)
├── migrations/             # Migraciones (futuro)
├── run.py                  # Punto de entrada
├── requirements.txt        # Dependencias
└── README.md              # Este archivo
```

## 🔑 Funcionalidades Principales

### Autenticación
- Registro de nuevos usuarios
- Inicio de sesión seguro
- Cierre de sesión
- Protección de rutas con login requerido

### Gestión de Pacientes
- Listar todos los pacientes
- Crear nuevos pacientes
- Editar información de pacientes
- Eliminar pacientes
- Ver detalles de un paciente

### Panel de Administración
- Dashboard con estadísticas
- Gestión de usuarios (vista)
- Sección de reportes (en desarrollo)

## 👤 Roles de Usuario

- **Admin**: Acceso completo, incluyendo panel de administración
- **Staff**: Acceso a gestión de pacientes
- **Paciente**: Acceso limitado (futuro)

## 🛠️ Tecnologías Utilizadas

| Tecnología | Versión | Propósito |
|-----------|---------|----------|
| Flask | 2.3.3 | Framework web |
| SQLAlchemy | 3.0.5 | ORM |
| Flask-Login | 0.6.2 | Gestión de sesiones |
| Flask-WTF | 1.1.1 | Formularios con CSRF |
| Bootstrap | 5.1.3 | CSS Framework |
| SQLite | - | Base de datos |

## 📝 Variables de Entorno

```env
FLASK_APP=run.py
FLASK_ENV=development          # o 'production'
SECRET_KEY=tu-clave-secreta
DATABASE_URL=sqlite:///...     # Opcional, usa SQLite por defecto
```

## 🔐 Seguridad

- Contraseñas hasheadas con Werkzeug
- Protección CSRF en todos los formularios
- Sesiones seguras con cookies HttpOnly
- Validación de entrada en formularios

## 🚀 Despliegue en Producción

1. Cambiar `FLASK_ENV` a `production`
2. Configurar un servidor WSGI (Gunicorn, uWSGI)
3. Usar una base de datos robusta (PostgreSQL recomendado)
4. Configurar variables de entorno de producción
5. Implementar HTTPS

Ejemplo con Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## 📚 Próximas Fases

- [ ] Sistema de reportes
- [ ] Notificaciones por email
- [ ] API REST
- [ ] Tests automatizados
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Exportación de datos (PDF, Excel)

## 🐛 Troubleshooting

**Error: "No module named 'app'"**
- Asegúrate de estar en el directorio raíz del proyecto

**Error: "Database file not found"**
- La carpeta `instance/` se crea automáticamente
- Verifica permisos de escritura en el directorio

**Puerto 5000 en uso**
- Cambia el puerto: `app.run(port=5001)`

## 📞 Soporte

Para reportar bugs o sugerir mejoras, contacta al equipo de desarrollo.

## 📄 Licencia

Este proyecto está bajo licencia propietaria. Todos los derechos reservados.

---

**Última actualización:** 2024
**Versión:** 1.0.0
# Proyecto_formulario_SSO
