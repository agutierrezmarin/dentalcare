"""
Script de datos iniciales para DentalCare.
Ejecutar con: python manage.py shell < setup_inicial.py
"""
from django.contrib.auth.models import User
from personal.models import PerfilUsuario
from clinico.models import CategoriaServicio, Servicio
from agenda.models import Sillon
from facturacion.models import MetodoPago
from inventario.models import CategoriaInsumo, Insumo

print("=== Iniciando setup de DentalCare ===")

# ── Superusuario admin ────────────────────────────────
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@dental.bo', 'admin123')
    admin.first_name = 'Administrador'
    admin.last_name = 'Sistema'
    admin.save()
    PerfilUsuario.objects.get_or_create(user=admin, defaults={'rol': 'admin'})
    print("✓ Usuario admin creado (admin / admin123)")
else:
    print("  Usuario admin ya existe")

# ── Doctor de ejemplo ─────────────────────────────────
if not User.objects.filter(username='doctor1').exists():
    doc = User.objects.create_user('doctor1', 'doctor@dental.bo', 'doctor123')
    doc.first_name = 'Juan Carlos'
    doc.last_name = 'Quispe'
    doc.save()
    PerfilUsuario.objects.get_or_create(
        user=doc,
        defaults={'rol': 'dentista', 'especialidad': 'Odontología General', 'color_agenda': '#4e9ff5'}
    )
    print("✓ Doctor Juan Carlos Quispe creado (doctor1 / doctor123)")

# ── Categorías de servicios ───────────────────────────
cats = {
    'Preventivo': '#34d399',
    'Restaurador': '#4e9ff5',
    'Endodoncia': '#a78bfa',
    'Cirugía': '#f87171',
    'Ortodoncia': '#fbbf24',
    'Estética': '#22d3ee',
    'Periodoncia': '#fb923c',
}
cat_objs = {}
for nombre, color in cats.items():
    c, _ = CategoriaServicio.objects.get_or_create(nombre=nombre, defaults={'color': color})
    cat_objs[nombre] = c
print(f"✓ {len(cats)} categorías de servicio creadas")

# ── Servicios ─────────────────────────────────────────
servicios = [
    ('Preventivo', 'Consulta y revisión', 50, 30),
    ('Preventivo', 'Limpieza dental / profilaxis', 150, 60),
    ('Preventivo', 'Aplicación de flúor', 80, 30),
    ('Preventivo', 'Sellante dental', 60, 20),
    ('Restaurador', 'Resina compuesta (1 cara)', 180, 45),
    ('Restaurador', 'Resina compuesta (2 caras)', 220, 60),
    ('Restaurador', 'Resina compuesta (3 caras)', 280, 75),
    ('Restaurador', 'Incrustación de porcelana', 550, 90),
    ('Endodoncia', 'Endodoncia uniradicular', 450, 90),
    ('Endodoncia', 'Endodoncia biradicular', 600, 120),
    ('Endodoncia', 'Endodoncia multirradicular', 750, 120),
    ('Cirugía', 'Extracción simple', 120, 30),
    ('Cirugía', 'Extracción de cordal', 350, 60),
    ('Cirugía', 'Implante dental', 2200, 120),
    ('Ortodoncia', 'Brackets metálicos', 2500, 60),
    ('Ortodoncia', 'Brackets cerámicos', 3500, 60),
    ('Ortodoncia', 'Alineadores removibles', 4000, 60),
    ('Estética', 'Blanqueamiento dental', 400, 90),
    ('Estética', 'Carilla de porcelana', 800, 60),
    ('Periodoncia', 'Raspado y alisado radicular', 250, 60),
]

for cat_nombre, nombre, precio, duracion in servicios:
    Servicio.objects.get_or_create(
        nombre=nombre,
        defaults={
            'categoria': cat_objs[cat_nombre],
            'precio': precio,
            'duracion_minutos': duracion
        }
    )
print(f"✓ {len(servicios)} servicios creados")

# ── Sillones ──────────────────────────────────────────
sillones = [
    ('Sillón 1', '#4e9ff5'),
    ('Sillón 2', '#34d399'),
    ('Sillón 3', '#a78bfa'),
]
for nombre, color in sillones:
    Sillon.objects.get_or_create(nombre=nombre, defaults={'color': color})
print(f"✓ {len(sillones)} sillones creados")

# ── Métodos de pago ───────────────────────────────────
metodos = ['Efectivo', 'QR / Transferencia', 'Tarjeta débito', 'Tarjeta crédito', 'Pago móvil']
for m in metodos:
    MetodoPago.objects.get_or_create(nombre=m)
print(f"✓ {len(metodos)} métodos de pago creados")

# ── Insumos dentales ──────────────────────────────────
cat_insumos = {}
for nombre in ['Anestesia', 'Resinas y composites', 'Instrumental', 'Descartables', 'Medicamentos']:
    c, _ = CategoriaInsumo.objects.get_or_create(nombre=nombre)
    cat_insumos[nombre] = c

insumos_lista = [
    ('Anestesia', 'Lidocaína 2% carpule', 'unidad', 50, 10, 5.5),
    ('Anestesia', 'Articaína 4% carpule', 'unidad', 30, 8, 7.0),
    ('Resinas y composites', 'Resina composite A2', 'gr', 20, 5, 45),
    ('Resinas y composites', 'Resina composite A3', 'gr', 15, 5, 45),
    ('Instrumental', 'Guantes látex S', 'caja', 5, 2, 25),
    ('Instrumental', 'Guantes látex M', 'caja', 8, 2, 25),
    ('Instrumental', 'Mascarillas descartables', 'caja', 10, 3, 18),
    ('Descartables', 'Baberos descartables', 'unidad', 200, 50, 0.5),
    ('Descartables', 'Jeringas desechables 3ml', 'unidad', 100, 20, 0.8),
    ('Medicamentos', 'Amoxicilina 500mg', 'unidad', 50, 10, 2.5),
    ('Medicamentos', 'Ibuprofeno 400mg', 'unidad', 60, 10, 1.5),
]

for cat, nombre, unidad, stock, minimo, precio in insumos_lista:
    Insumo.objects.get_or_create(
        nombre=nombre,
        defaults={
            'categoria': cat_insumos[cat],
            'unidad': unidad,
            'stock_actual': stock,
            'stock_minimo': minimo,
            'precio_unitario': precio,
        }
    )
print(f"✓ {len(insumos_lista)} insumos creados")

print("\n=== Setup completado ===")
print("Acceso: http://127.0.0.1:8000/")
print("Admin:  http://127.0.0.1:8000/admin/")
print("Usuario admin: admin / admin123")
print("Usuario doctor: doctor1 / doctor123")
