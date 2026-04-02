# DentalCare — Sistema de Gestión Dental

Sistema completo de gestión para clínicas dentales desarrollado con Django 5 + PostgreSQL.

## Módulos

| Módulo | Descripción |
|---|---|
| **Pacientes** | Registro completo, historial, alergias, adjuntos |
| **Odontograma** | Diagrama dental interactivo con notación FDI |
| **Historia Clínica** | Notas clínicas, diagnósticos, planes de tratamiento |
| **Tratamientos** | Registro de procedimientos con estado y seguimiento |
| **Agenda** | Calendario FullCalendar, drag & drop, filtro por doctor |
| **Facturación** | Pagos, planes de cuotas, presupuestos, control de deudas |
| **Reportes** | Ingresos por mes, por método de pago, deudas pendientes |
| **Inventario** | Insumos dentales, movimientos, alertas de stock |
| **Personal** | Usuarios con roles: admin, dentista, asistente, recepción |
| **Multimedia** | Galería de fotos clínicas, radiografías, comparación antes/después |

## Instalación

### 1. Clonar y entorno virtual

```bash
cd ~/proyectos-django
python3 -m venv venv_dentalcare
source venv_dentalcare/bin/activate
cd dentalcare
pip install -r requirements.txt
```

### 2. Base de datos PostgreSQL

```sql
CREATE DATABASE dentalcare_db;
CREATE USER dentalcare_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE dentalcare_db TO dentalcare_user;
```

### 3. Variables de entorno (opcional)

```bash
export DB_NAME=dentalcare_db
export DB_USER=dentalcare_user
export DB_PASSWORD=tu_password
```

O editar directamente `dentalcare/settings.py`.

### 4. Migraciones y datos iniciales

```bash
python manage.py makemigrations pacientes agenda clinico facturacion inventario personal multimedia
python manage.py migrate
python manage.py shell < setup_inicial.py
python manage.py collectstatic --noinput
```

### 5. Ejecutar

```bash
python manage.py runserver
```

Abrir: http://127.0.0.1:8000/

## Credenciales por defecto

| Usuario | Contraseña | Rol |
|---|---|---|
| admin | admin123 | Administrador |
| doctor1 | doctor123 | Dentista |

## Estructura del proyecto

```
dentalcare/
├── dentalcare/          # Configuración principal
├── pacientes/           # Módulo core de pacientes
├── clinico/             # Odontograma, historia, tratamientos
├── agenda/              # Citas y calendario
├── facturacion/         # Pagos, planes, reportes
├── inventario/          # Insumos y stock
├── personal/            # Usuarios y roles
├── multimedia/          # Fotos y radiografías
├── templates/           # Todos los templates HTML
├── static/              # CSS, JS
├── media/               # Archivos subidos
├── requirements.txt
└── setup_inicial.py
```

## Tecnologías

- **Backend**: Django 5.1, PostgreSQL, psycopg3
- **Frontend**: Bootstrap 5, Chart.js, FullCalendar 6, Google Fonts
- **Imágenes**: Pillow 11

## Deployment (OVHcloud / Nginx + Gunicorn)

```bash
# Instalar gunicorn
pip install gunicorn

# Archivo de servicio: /etc/systemd/system/dentalcare.service
[Unit]
Description=DentalCare Django
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/dentalcare
ExecStart=/var/www/dentalcare/venv_dentalcare/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/dentalcare.sock \
    dentalcare.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Agregar IP del servidor a `ALLOWED_HOSTS` en `settings.py`.
