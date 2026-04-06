# Guía de Despliegue — AdmiDent en VPS OVH (Debian 13)

> **Stack:** Django 5.1 · PostgreSQL · Gunicorn · Nginx · Certbot (SSL)  
> **OS:** Debian 13 Trixie (64-bit)  
> **Python:** 3.12+

---

## Índice

1. [Preparar el servidor](#1-preparar-el-servidor)
2. [Crear usuario de aplicación](#2-crear-usuario-de-aplicación)
3. [Instalar dependencias del sistema](#3-instalar-dependencias-del-sistema)
4. [Configurar PostgreSQL](#4-configurar-postgresql)
5. [Subir el código fuente](#5-subir-el-código-fuente)
6. [Entorno virtual y dependencias Python](#6-entorno-virtual-y-dependencias-python)
7. [Variables de entorno (.env)](#7-variables-de-entorno-env)
8. [Configurar Django para producción](#8-configurar-django-para-producción)
9. [Migraciones y archivos estáticos](#9-migraciones-y-archivos-estáticos)
10. [Configurar Gunicorn como servicio](#10-configurar-gunicorn-como-servicio)
11. [Configurar Nginx](#11-configurar-nginx)
12. [Certificado SSL con Certbot](#12-certificado-ssl-con-certbot)
13. [Firewall](#13-firewall)
14. [Verificación final](#14-verificación-final)
15. [Comandos útiles de mantenimiento](#15-comandos-útiles-de-mantenimiento)

---

## 1. Preparar el servidor

Conectarse al VPS por SSH como `root`:

```bash
ssh root@<IP_DEL_VPS>
```

Actualizar el sistema:

```bash
apt update && apt upgrade -y
apt install -y curl wget git unzip software-properties-common
```

Configurar la zona horaria:

```bash
timedatectl set-timezone America/La_Paz
```

---

## 2. Crear usuario de aplicación

Nunca ejecutar la app como `root`. Crear un usuario dedicado:

```bash
adduser dentalcare
usermod -aG sudo dentalcare
```

Desde este punto, salvo indicación contraria, los comandos se ejecutan como `dentalcare`:

```bash
su - dentalcare
```

---

## 3. Instalar dependencias del sistema

```bash
sudo apt install -y \
  python3 python3-pip python3-venv python3-dev \
  postgresql postgresql-contrib \
  nginx \
  libpq-dev \
  libjpeg-dev libpng-dev zlib1g-dev \
  certbot python3-certbot-nginx
```

Verificar la versión de Python:

```bash
python3 --version   # debe ser 3.12+
```

---

## 4. Configurar PostgreSQL

Iniciar y habilitar PostgreSQL:

```bash
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

Crear la base de datos y el usuario:

```bash
sudo -u postgres psql
```

Dentro de la consola de psql:

```sql
CREATE DATABASE dentalcare_db;
CREATE USER dentalcare_user WITH PASSWORD 'TU_PASSWORD_SEGURO';
ALTER ROLE dentalcare_user SET client_encoding TO 'utf8';
ALTER ROLE dentalcare_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE dentalcare_user SET timezone TO 'America/La_Paz';
GRANT ALL PRIVILEGES ON DATABASE dentalcare_db TO dentalcare_user;
\q
```

> ⚠️ Cambia `TU_PASSWORD_SEGURO` por una contraseña fuerte. Guárdala, la usarás en el `.env`.

---

## 5. Subir el código fuente

### Opción A — Clonar desde Git (recomendado)

```bash
cd /home/dentalcare
git clone https://github.com/TU_USUARIO/dentalcare.git app
cd app
```

### Opción B — Subir por SFTP / SCP

Desde tu máquina local:

```bash
scp -r /home/alejandro/Documents/proyectos-django/dentalcare \
       dentalcare@<IP_DEL_VPS>:/home/dentalcare/app
```

Estructura esperada en el servidor:

```
/home/dentalcare/app/
├── agenda/
├── clinico/
├── dentalcare/          ← settings.py, urls.py
├── facturacion/
├── inventario/
├── pacientes/
├── personal/
├── static/
├── templates/
├── manage.py
└── requirements.txt
```

---

## 6. Entorno virtual y dependencias Python

```bash
cd /home/dentalcare/app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

---

## 7. Variables de entorno (.env)

Crear el archivo de entorno **fuera** del directorio del proyecto para mayor seguridad:

```bash
nano /home/dentalcare/.env
```

Contenido del `.env`:

```ini
# Django
DJANGO_SECRET_KEY=genera-una-clave-larga-y-aleatoria-aqui
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tudominio.com,www.tudominio.com,<IP_DEL_VPS>

# Base de datos
DB_NAME=dentalcare_db
DB_USER=dentalcare_user
DB_PASSWORD=TU_PASSWORD_SEGURO
DB_HOST=localhost
DB_PORT=5432
```

Generar una `SECRET_KEY` segura:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Permisos restrictivos al archivo:

```bash
chmod 600 /home/dentalcare/.env
```

---

## 8. Configurar Django para producción

Editar `dentalcare/settings.py`:

```bash
nano /home/dentalcare/app/dentalcare/settings.py
```

Reemplazar las líneas de configuración por las siguientes (usando `os.environ`):

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar .env
from dotenv import load_dotenv
load_dotenv('/home/dentalcare/.env')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')

# Base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     os.environ.get('DB_NAME',     'dentalcare_db'),
        'USER':     os.environ.get('DB_USER',     'dentalcare_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST':     os.environ.get('DB_HOST',     'localhost'),
        'PORT':     os.environ.get('DB_PORT',     '5432'),
    }
}

# Archivos estáticos y media
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'
```

Instalar `python-dotenv`:

```bash
source /home/dentalcare/app/venv/bin/activate
pip install python-dotenv
```

---

## 9. Migraciones y archivos estáticos

```bash
cd /home/dentalcare/app
source venv/bin/activate

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Crear directorios de media si no existen:

```bash
mkdir -p /home/dentalcare/app/media
chmod 755 /home/dentalcare/app/media
```

---

## 10. Configurar Gunicorn como servicio

Crear el archivo de socket:

```bash
sudo nano /etc/systemd/system/dentalcare.socket
```

```ini
[Unit]
Description=Gunicorn socket para AdmiDent

[Socket]
ListenStream=/run/dentalcare.sock

[Install]
WantedBy=sockets.target
```

Crear el servicio de Gunicorn:

```bash
sudo nano /etc/systemd/system/dentalcare.service
```

```ini
[Unit]
Description=Gunicorn daemon para AdmiDent
Requires=dentalcare.socket
After=network.target

[Service]
User=dentalcare
Group=www-data
WorkingDirectory=/home/dentalcare/app
EnvironmentFile=/home/dentalcare/.env
ExecStart=/home/dentalcare/app/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/dentalcare.sock \
          dentalcare.wsgi:application

Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Activar y arrancar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dentalcare.socket
sudo systemctl start dentalcare.socket
sudo systemctl enable dentalcare
sudo systemctl start dentalcare
```

Verificar que el socket existe:

```bash
sudo systemctl status dentalcare.socket
file /run/dentalcare.sock
```

---

## 11. Configurar Nginx

Crear el bloque del sitio:

```bash
sudo nano /etc/nginx/sites-available/dentalcare
```

```nginx
server {
    listen 80;
    server_name tudominio.com www.tudominio.com;

    client_max_body_size 20M;

    location = /favicon.ico { access_log off; log_not_found off; }

    # Archivos estáticos
    location /static/ {
        alias /home/dentalcare/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Archivos media (fotos de pacientes, etc.)
    location /media/ {
        alias /home/dentalcare/app/media/;
        expires 7d;
    }

    # Proxy hacia Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/dentalcare.sock;
        proxy_read_timeout  300;
        proxy_connect_timeout 300;
    }
}
```

Habilitar el sitio:

```bash
sudo ln -s /etc/nginx/sites-available/dentalcare /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Dar permiso a Nginx para acceder al directorio del usuario:

```bash
sudo usermod -aG dentalcare www-data
chmod 710 /home/dentalcare
```

---

## 12. Certificado SSL con Certbot

```bash
sudo certbot --nginx -d tudominio.com -d www.tudominio.com
```

Certbot modifica automáticamente el bloque de Nginx para redirigir HTTP → HTTPS y configurar el certificado.

Verificar la renovación automática:

```bash
sudo certbot renew --dry-run
```

El certificado se renueva automáticamente mediante un timer de systemd.

---

## 13. Firewall

Configurar `ufw` para permitir solo los puertos necesarios:

```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'    # puertos 80 y 443
sudo ufw enable
sudo ufw status
```

---

## 14. Verificación final

```bash
# Estado de todos los servicios
sudo systemctl status dentalcare.socket
sudo systemctl status dentalcare
sudo systemctl status nginx
sudo systemctl status postgresql

# Ver logs de Gunicorn en tiempo real
sudo journalctl -u dentalcare -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

Abrir el navegador y visitar `https://tudominio.com`. Deberías ver el sistema de inicio de sesión de AdmiDent.

---

## 15. Comandos útiles de mantenimiento

### Actualizar el código (deploy)

```bash
cd /home/dentalcare/app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart dentalcare
```

### Reiniciar servicios

```bash
sudo systemctl restart dentalcare         # reiniciar Gunicorn
sudo systemctl reload nginx               # recargar Nginx sin cortar conexiones
sudo systemctl restart postgresql         # reiniciar base de datos
```

### Backup de la base de datos

```bash
sudo -u postgres pg_dump dentalcare_db > /home/dentalcare/backup_$(date +%Y%m%d).sql
```

Restaurar backup:

```bash
sudo -u postgres psql dentalcare_db < /home/dentalcare/backup_YYYYMMDD.sql
```

### Ver logs de errores Django

```bash
sudo journalctl -u dentalcare --since "1 hour ago"
```

### Crear superusuario en producción

```bash
cd /home/dentalcare/app
source venv/bin/activate
python manage.py createsuperuser
```

---

## Notas de seguridad

| Punto | Acción |
|---|---|
| `DEBUG = False` | Obligatorio en producción |
| `SECRET_KEY` | Única, larga, nunca en el repositorio |
| `ALLOWED_HOSTS` | Solo tu dominio e IP |
| Contraseña DB | Fuerte y diferente a la del sistema |
| Archivo `.env` | Permisos `600`, fuera del repo |
| Backups | Programar con cron al menos diariamente |
| Actualizaciones | `apt upgrade` semanal como mínimo |

---

*Guía generada para AdmiDent — Sistema de Gestión Dental · Django 5.1 · Debian 13*
