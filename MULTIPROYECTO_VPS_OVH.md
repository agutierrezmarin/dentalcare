# Dos proyectos Django en el mismo VPS OVH — Sin afectar el proyecto existente

> **Proyecto 1 (ya desplegado):** Tienda de Abarrotes  
> **Proyecto 2 (nuevo):** AdmiDent — Sistema Dental  
> **OS:** Debian 13 / Ubuntu 24.04  
> **Stack compartido:** Nginx · PostgreSQL · Certbot  
> **Claves:** cada proyecto tiene su propio socket, servicio, BD y entorno virtual

---

## Cómo conviven los dos proyectos

```
Internet
   │
   ▼
 Nginx  ◄─── un solo proceso, escucha en :80 y :443
   │
   ├── tienda.tudominio.com  ──►  /run/tienda.sock  ──►  Gunicorn (tienda)
   │
   └── dental.tudominio.com  ──►  /run/dentalcare.sock  ──►  Gunicorn (dentalcare)

PostgreSQL
   ├── tienda_db       ← usuario: tienda_user
   └── dentalcare_db   ← usuario: dentalcare_user
```

**Lo que NO se toca del proyecto existente:**
- Su servicio Gunicorn (`tienda.service`)
- Su bloque Nginx (`/etc/nginx/sites-available/tienda`)
- Su base de datos y usuario PostgreSQL
- Su directorio y entorno virtual

**Lo que se agrega:**
- Un nuevo socket/servicio para AdmiDent
- Un nuevo bloque Nginx para AdmiDent
- Una nueva BD PostgreSQL para AdmiDent

---

## Paso 1 — Verificar el estado actual del servidor

Antes de tocar nada, confirmar que el proyecto existente funciona:

```bash
sudo systemctl status tienda        # o el nombre de tu servicio actual
sudo systemctl status nginx
sudo systemctl status postgresql
```

Si todo está `active (running)`, proceder. Si algo falla, resolverlo primero.

Ver los sockets activos para no usar un nombre que ya exista:

```bash
ls /run/*.sock
```

Ver los bloques Nginx activos:

```bash
ls /etc/nginx/sites-enabled/
```

---

## Paso 2 — Crear usuario del sistema para AdmiDent

Mantener cada proyecto bajo su propio usuario evita que uno pueda leer archivos del otro:

```bash
sudo adduser dentalcare
sudo usermod -aG www-data dentalcare
```

> Si prefieres usar el mismo usuario que el proyecto existente, sáltate este paso y reemplaza
> `dentalcare` por tu usuario actual en todos los comandos.

---

## Paso 3 — Crear la base de datos PostgreSQL para AdmiDent

PostgreSQL ya está corriendo. Solo hay que agregar una BD y un usuario nuevos,
**sin tocar la BD del proyecto existente**:

```bash
sudo -u postgres psql
```

```sql
-- Solo crear lo nuevo, NO modificar nada existente
CREATE DATABASE dentalcare_db;
CREATE USER dentalcare_user WITH PASSWORD 'PASSWORD_MUY_SEGURO';
ALTER ROLE dentalcare_user SET client_encoding TO 'utf8';
ALTER ROLE dentalcare_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE dentalcare_user SET timezone TO 'America/La_Paz';
GRANT ALL PRIVILEGES ON DATABASE dentalcare_db TO dentalcare_user;
\q
```

Verificar que la BD del proyecto 1 sigue intacta:

```bash
sudo -u postgres psql -c "\l"
# Deben aparecer AMBAS bases de datos
```

---

## Paso 4 — Subir el código de AdmiDent

```bash
su - dentalcare
cd /home/dentalcare
git clone https://github.com/TU_USUARIO/dentalcare.git app
# o copiar por SCP desde tu máquina local:
# scp -r ./dentalcare dentalcare@IP:/home/dentalcare/app
```

---

## Paso 5 — Entorno virtual de AdmiDent

Cada proyecto tiene su propio `venv` — **nunca compartir entornos virtuales**:

```bash
cd /home/dentalcare/app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

---

## Paso 6 — Archivo .env de AdmiDent

```bash
nano /home/dentalcare/.env
```

```ini
SECRET_KEY=genera-una-clave-nueva-diferente-a-la-del-otro-proyecto
DEBUG=False
ALLOWED_HOSTS=dental.tudominio.com,www.dental.tudominio.com

DB_NAME=dentalcare_db
DB_USER=dentalcare_user
DB_PASSWORD=PASSWORD_MUY_SEGURO
DB_HOST=localhost
DB_PORT=5432
```

```bash
chmod 600 /home/dentalcare/.env
```

> ⚠️ La `SECRET_KEY` debe ser **diferente** a la del proyecto existente.  
> Generar una: `python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

---

## Paso 7 — Migraciones y estáticos de AdmiDent

```bash
cd /home/dentalcare/app
source venv/bin/activate

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser

mkdir -p media
chmod 755 media
```

---

## Paso 8 — Servicio Gunicorn para AdmiDent

Este es el punto clave: **nombre de socket y servicio completamente diferentes** al del proyecto existente.

### 8.1 Socket

```bash
sudo nano /etc/systemd/system/dentalcare.socket
```

```ini
[Unit]
Description=Gunicorn socket — AdmiDent

[Socket]
ListenStream=/run/dentalcare.sock

[Install]
WantedBy=sockets.target
```

### 8.2 Servicio

```bash
sudo nano /etc/systemd/system/dentalcare.service
```

```ini
[Unit]
Description=Gunicorn daemon — AdmiDent
Requires=dentalcare.socket
After=network.target

[Service]
User=dentalcare
Group=www-data
WorkingDirectory=/home/dentalcare/app
EnvironmentFile=/home/dentalcare/.env
ExecStart=/home/dentalcare/app/venv/bin/gunicorn \
          --access-logfile - \
          --workers 2 \
          --bind unix:/run/dentalcare.sock \
          dentalcare.wsgi:application

Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

> Se usan **2 workers** en lugar de 3 para no saturar la RAM si el VPS tiene poca memoria.
> Con 4 GB RAM puedes subir a 3 workers sin problema.

### 8.3 Activar

```bash
sudo systemctl daemon-reload
sudo systemctl enable dentalcare.socket
sudo systemctl start  dentalcare.socket
sudo systemctl enable dentalcare
sudo systemctl start  dentalcare
```

Verificar que el nuevo socket existe **y** que el socket del proyecto 1 sigue ahí:

```bash
ls /run/*.sock
# Debe mostrar los dos: tienda.sock y dentalcare.sock
```

---

## Paso 9 — Bloque Nginx para AdmiDent

Se agrega un **nuevo archivo** en `sites-available`. El archivo del proyecto existente no se modifica.

```bash
sudo nano /etc/nginx/sites-available/dentalcare
```

```nginx
server {
    listen 80;
    server_name dental.tudominio.com www.dental.tudominio.com;

    client_max_body_size 20M;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /home/dentalcare/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/dentalcare/app/media/;
        expires 7d;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/dentalcare.sock;
        proxy_read_timeout    300;
        proxy_connect_timeout 300;
    }
}
```

Habilitar **solo** este nuevo bloque:

```bash
sudo ln -s /etc/nginx/sites-available/dentalcare /etc/nginx/sites-enabled/
```

Verificar que la configuración es válida antes de recargar:

```bash
sudo nginx -t
```

Si dice `syntax is ok` y `test is successful`:

```bash
sudo systemctl reload nginx
```

> `reload` recarga la configuración **sin cortar conexiones activas** del proyecto existente.
> Es diferente a `restart`.

---

## Paso 10 — SSL para AdmiDent

El certificado del proyecto existente **no se toca**. Certbot agrega uno nuevo para el dominio de AdmiDent:

```bash
sudo certbot --nginx -d dental.tudominio.com -d www.dental.tudominio.com
```

Certbot detecta que ya tiene certificados para el otro proyecto y solo agrega el nuevo.

Verificar que ambos certificados están activos:

```bash
sudo certbot certificates
```

---

## Paso 11 — Verificación final

### Proyecto existente (tienda) — debe seguir funcionando exactamente igual

```bash
sudo systemctl status tienda
curl -I https://tienda.tudominio.com
```

### Proyecto nuevo (dental) — debe responder

```bash
sudo systemctl status dentalcare
curl -I https://dental.tudominio.com
```

### Estado global

```bash
# Todos los servicios activos
sudo systemctl status tienda dentalcare nginx postgresql

# Sockets presentes
ls -la /run/*.sock

# Logs de AdmiDent
sudo journalctl -u dentalcare -n 50

# Logs de la tienda (sin cambios)
sudo journalctl -u tienda -n 10
```

---

## Resumen: qué tiene cada proyecto por separado

| Componente | Tienda (proyecto 1) | AdmiDent (proyecto 2) |
|---|---|---|
| Usuario del sistema | `tienda` | `dentalcare` |
| Directorio | `/home/tienda/app/` | `/home/dentalcare/app/` |
| Entorno virtual | `/home/tienda/app/venv/` | `/home/dentalcare/app/venv/` |
| Archivo `.env` | `/home/tienda/.env` | `/home/dentalcare/.env` |
| BD PostgreSQL | `tienda_db` | `dentalcare_db` |
| Usuario PostgreSQL | `tienda_user` | `dentalcare_user` |
| Socket Gunicorn | `/run/tienda.sock` | `/run/dentalcare.sock` |
| Servicio systemd | `tienda.service` | `dentalcare.service` |
| Bloque Nginx | `sites-available/tienda` | `sites-available/dentalcare` |
| Dominio | `tienda.tudominio.com` | `dental.tudominio.com` |
| Certificado SSL | Propio | Propio |

---

## Comandos de mantenimiento para AdmiDent (sin afectar la tienda)

```bash
# Actualizar código
cd /home/dentalcare/app && git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart dentalcare      # solo reinicia AdmiDent

# Ver logs en tiempo real
sudo journalctl -u dentalcare -f

# Reiniciar solo AdmiDent si hay problemas
sudo systemctl restart dentalcare

# Recargar Nginx (aplica para ambos proyectos, sin cortar conexiones)
sudo systemctl reload nginx

# Backup solo de la BD de AdmiDent
sudo -u postgres pg_dump dentalcare_db > ~/backup_dental_$(date +%Y%m%d).sql
```

---

## Problemas comunes

### Nginx devuelve 502 Bad Gateway
El socket de Gunicorn no está corriendo:
```bash
sudo systemctl status dentalcare
sudo systemctl restart dentalcare
```

### Nginx devuelve 403 Forbidden en /static/ o /media/
Nginx no tiene permiso para leer los archivos:
```bash
sudo chmod 710 /home/dentalcare
sudo chmod -R 755 /home/dentalcare/app/staticfiles
sudo chmod -R 755 /home/dentalcare/app/media
```

### Error de base de datos al iniciar
Verificar que la BD existe y las credenciales en `.env` son correctas:
```bash
sudo -u postgres psql -c "\l"
source /home/dentalcare/app/venv/bin/activate
cd /home/dentalcare/app
python manage.py dbshell    # debe abrir psql sin error
```

### El proyecto 1 dejó de funcionar después de recargar Nginx
Verificar que su bloque Nginx sigue habilitado:
```bash
ls /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

*La regla de oro: cada proyecto es una isla — usuario, entorno, BD, socket y dominio propios.*
