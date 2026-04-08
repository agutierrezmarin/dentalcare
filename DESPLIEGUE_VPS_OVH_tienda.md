# Guía de Despliegue — Django en VPS OVH (Ubuntu 24.04)

> **Proyecto:** Tienda de Abarrotes · Django 6.0 · Python 3.13
> **Servidor:** OVH VPS Model 1 — 4 vCores · 4 GB RAM · 75 GB SSD NVMe
> **Stack de producción:** Nginx + Gunicorn + PostgreSQL + Certbot (HTTPS)

---

## ¿Debo cambiar de SQLite a PostgreSQL?

**Sí, absolutamente.** Para producción SQLite no es adecuado:

| Aspecto | SQLite | PostgreSQL |
|---|---|---|
| Escrituras simultáneas | Solo 1 a la vez (bloquea) | Múltiples sin bloqueos |
| Usuarios concurrentes | Problemas con >2 | Sin límite práctico |
| Backups | Copiar archivo (riesgo de corrupción) | `pg_dump` confiable |
| Tamaño máximo práctico | ~1 GB | Ilimitado |
| Integridad de datos | Básica | ACID completo |
| Performance con miles de registros | Degrada | Estable |

**Conclusión:** SQLite solo sirve para desarrollo local. Migra a PostgreSQL antes de ir a producción.

---

## Paso 0 — Preparación local (antes de subir)

### 0.1 Crear requirements.txt

```bash
# En tu máquina local, dentro del virtualenv
cd /home/alejandro/Documents/proyectos-django/proyecto_tienda
source venv_proytienda/bin/activate
pip freeze > abarrotes/requirements.txt
```

Edita `requirements.txt` y agrega si no están:
```
gunicorn>=21.2.0
psycopg2-binary>=2.9.9
python-decouple>=3.8
Pillow>=11.0.0
```

### 0.2 Crear archivo .env para variables de entorno

Crea `abarrotes/.env` (NO lo subas a git):
```ini
SECRET_KEY=clave-super-secreta-de-al-menos-50-caracteres-aqui
DEBUG=False
ALLOWED_HOSTS=tu-ip-del-vps,tu-dominio.com,www.tu-dominio.com

DB_NAME=tienda_db
DB_USER=tienda_user
DB_PASSWORD=contraseña-segura-aqui
DB_HOST=localhost
DB_PORT=5432
```

### 0.3 Actualizar settings.py para producción

```python
# abarrotes/settings.py — reemplazar las líneas actuales con:
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Base de datos PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Archivos estáticos y media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'   # donde collectstatic los pone
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 0.4 Crear .gitignore si no existe

```
.env
__pycache__/
*.pyc
db.sqlite3
staticfiles/
media/
venv*/
*.log
```

### 0.5 Subir el proyecto al VPS

```bash
# Opción A: con scp (desde tu máquina local)
scp -r /home/alejandro/Documents/proyectos-django/proyecto_tienda/abarrotes \
    root@IP_DEL_VPS:/var/www/tienda/

# Opción B: con git (recomendado)
git init
git add .
git commit -m "Primera versión"
# Crear repo en GitHub/GitLab y luego:
git remote add origin https://github.com/tu-usuario/tienda.git
git push -u origin main
```

---

## Paso 1 — Configuración inicial del VPS

Conectar al VPS:
```bash
ssh root@IP_DEL_VPS
```

### 1.1 Actualizar el sistema

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv python3-dev \
               postgresql postgresql-contrib libpq-dev \
               nginx git curl ufw
```

### 1.2 Crear usuario del sistema (no trabajar como root)

```bash
adduser deploy
usermod -aG sudo deploy
su - deploy
```

---

## Paso 2 — Configurar PostgreSQL

```bash
# Entrar a la consola de PostgreSQL
sudo -u postgres psql
```

Dentro de psql ejecutar:
```sql
CREATE DATABASE tienda_db;
CREATE USER tienda_user WITH PASSWORD 'contraseña-segura-aqui';
ALTER ROLE tienda_user SET client_encoding TO 'utf8';
ALTER ROLE tienda_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE tienda_user SET timezone TO 'America/La_Paz';
GRANT ALL PRIVILEGES ON DATABASE tienda_db TO tienda_user;
-- En PostgreSQL 15+ también necesitas:
\c tienda_db
GRANT ALL ON SCHEMA public TO tienda_user;
\q
```

---

## Paso 3 — Desplegar el proyecto

### 3.1 Clonar o subir el proyecto

```bash
sudo mkdir -p /var/www/tienda
sudo chown deploy:deploy /var/www/tienda
cd /var/www/tienda

# Si usas git:
git clone https://github.com/tu-usuario/tienda.git .

# Si subiste con scp, los archivos ya están en /var/www/tienda/
```

### 3.2 Crear entorno virtual e instalar dependencias

```bash
cd /var/www/tienda
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Crear el archivo .env en el servidor

```bash
nano /var/www/tienda/.env
```

Pegar el contenido del `.env` con los valores reales del servidor.

### 3.4 Migrar base de datos y configurar Django

```bash
cd /var/www/tienda
source venv/bin/activate

# Migraciones
python manage.py migrate

# Recopilar archivos estáticos
python manage.py collectstatic --noinput

# Crear superusuario
python manage.py createsuperuser

# Verificar que todo esté bien
python manage.py check --deploy
```

---

## Paso 4 — Configurar Gunicorn

Gunicorn es el servidor WSGI que corre Django en producción.

### 4.1 Probar Gunicorn manualmente

```bash
cd /var/www/tienda
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 abarrotes.wsgi:application
# Ctrl+C para detener
```

### 4.2 Crear servicio systemd para Gunicorn

```bash
sudo nano /etc/systemd/system/tienda.service
```

Contenido del archivo:
```ini
[Unit]
Description=Gunicorn — Tienda de Abarrotes
After=network.target

[Service]
User=deploy
Group=www-data
WorkingDirectory=/var/www/tienda
EnvironmentFile=/var/www/tienda/.env
ExecStart=/var/www/tienda/venv/bin/gunicorn \
          --access-logfile /var/log/gunicorn/access.log \
          --error-logfile /var/log/gunicorn/error.log \
          --workers 3 \
          --bind unix:/run/tienda.sock \
          abarrotes.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Crear directorio de logs
sudo mkdir -p /var/log/gunicorn
sudo chown deploy:deploy /var/log/gunicorn

# Activar e iniciar el servicio
sudo systemctl daemon-reload
sudo systemctl start tienda
sudo systemctl enable tienda
sudo systemctl status tienda
```

---

## Paso 5 — Configurar Nginx

Nginx recibe las peticiones HTTP/HTTPS y las pasa a Gunicorn via socket Unix.

### 5.1 Crear configuración de Nginx

```bash
sudo nano /etc/nginx/sites-available/tienda
```

Contenido:
```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com IP_DEL_VPS;

    # Archivos estáticos (CSS, JS, imágenes del sistema)
    location /static/ {
        alias /var/www/tienda/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Archivos subidos por usuarios (logos, fotos)
    location /media/ {
        alias /var/www/tienda/media/;
        expires 7d;
    }

    # Todo lo demás → Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/tienda.sock;
        proxy_read_timeout 120;
        proxy_connect_timeout 120;
        client_max_body_size 10M;
    }
}
```

```bash
# Activar el sitio
sudo ln -s /etc/nginx/sites-available/tienda /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default   # quitar sitio por defecto
sudo nginx -t                              # verificar configuración
sudo systemctl restart nginx
```

---

## Paso 6 — Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'    # puertos 80 y 443
sudo ufw enable
sudo ufw status
```

---

## Paso 7 — HTTPS con Certbot (Let's Encrypt) — Requiere dominio

> Si solo tienes IP (sin dominio), salta este paso. HTTPS funciona con dominio.

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Certbot modifica nginx automáticamente y configura renovación automática
# Verificar renovación automática:
sudo certbot renew --dry-run
```

---

## Paso 8 — Migrar datos de SQLite a PostgreSQL

Si ya tienes datos en SQLite que quieres conservar:

### Opción A — exportar/importar datos (recomendada)

```bash
# En tu máquina LOCAL (con SQLite aún activo):
source venv_proytienda/bin/activate
cd abarrotes

# Exportar todos los datos excepto contenttypes y auth.permissions
python manage.py dumpdata \
  --exclude auth.permission \
  --exclude contenttypes \
  --indent 2 \
  > datos_exportados.json

# Copiar al servidor
scp datos_exportados.json deploy@IP_DEL_VPS:/var/www/tienda/
```

```bash
# En el SERVIDOR (con PostgreSQL configurado):
cd /var/www/tienda
source venv/bin/activate

# Asegurarse de que las migraciones estén aplicadas
python manage.py migrate

# Importar los datos
python manage.py loaddata datos_exportados.json
```

### Opción B — empezar desde cero

Si no tienes datos importantes en desarrollo, simplemente:
```bash
python manage.py migrate          # crea las tablas vacías
python manage.py createsuperuser  # crea el admin
```
Y registras los datos nuevamente desde la interfaz.

---

## Paso 9 — Comandos de mantenimiento útiles

```bash
# Ver logs en tiempo real
sudo journalctl -u tienda -f
sudo tail -f /var/log/gunicorn/error.log
sudo tail -f /var/log/nginx/error.log

# Reiniciar después de cambios en el código
cd /var/www/tienda && git pull
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart tienda

# Backup de la base de datos PostgreSQL
pg_dump -U tienda_user -h localhost tienda_db > backup_$(date +%Y%m%d).sql

# Restaurar backup
psql -U tienda_user -h localhost tienda_db < backup_20260311.sql

# Ver estado de los servicios
sudo systemctl status tienda nginx postgresql
```

---

## Paso 10 — Verificación final

```bash
# Desde el servidor
curl http://localhost/         # debe devolver HTML
curl http://IP_DEL_VPS/       # desde fuera
python manage.py check --deploy  # debe mostrar 0 errores críticos
```

Lista de verificación antes de dar por finalizado el despliegue:

- [ ] `DEBUG=False` en `.env`
- [ ] `SECRET_KEY` es una cadena aleatoria larga (mínimo 50 caracteres)
- [ ] `ALLOWED_HOSTS` contiene solo el dominio/IP del servidor
- [ ] PostgreSQL funcionando con las migraciones aplicadas
- [ ] `collectstatic` ejecutado — los archivos CSS/JS cargan correctamente
- [ ] La carpeta `media/` existe y tiene permisos de escritura para el usuario `deploy`
- [ ] Gunicorn corriendo como servicio systemd
- [ ] Nginx sirviendo correctamente estático y redirigiendo a Gunicorn
- [ ] Firewall activado (solo puertos 22, 80, 443)
- [ ] HTTPS activo si tienes dominio
- [ ] Backup inicial de la BD guardado

---

## Resumen de la arquitectura en producción

```
Internet
   │
   ▼
[Nginx :80/:443]  ← HTTPS, archivos estáticos/media
   │
   ▼  (socket Unix /run/tienda.sock)
[Gunicorn]  ← 3 workers Django
   │
   ▼
[Django 6.0]  ← lógica de la aplicación
   │
   ▼
[PostgreSQL]  ← base de datos persistente
```

---

## Números de referencia (VPS Model 1)

| Recurso | Valor |  Uso estimado |
|---|---|---|
| vCores | 4 | Gunicorn: 3 workers = OK |
| RAM | 4 GB | Django+Postgres+Nginx ≈ 800 MB en reposo |
| SSD | 75 GB | Código + BD + media ≈ 2 GB iniciales |
| Ancho de banda | 500 Mbps | Más que suficiente |

El VPS Model 1 de OVH es más que suficiente para este sistema con decenas de usuarios simultáneos.
