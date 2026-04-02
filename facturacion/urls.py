from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    path('pago/nuevo/',                         views.registrar_pago,       name='pago'),
    path('pago/nuevo/<int:paciente_pk>/',        views.registrar_pago,       name='pago_paciente'),
    path('paciente/<int:paciente_pk>/',          views.detalle_pagos,        name='detalle_pagos'),
    path('plan/<int:tratamiento_pk>/crear/',     views.crear_plan_pago,      name='crear_plan'),
    path('reporte/',                             views.reporte_ingresos,     name='reporte'),
    path('presupuesto/<int:paciente_pk>/nuevo/', views.crear_presupuesto,    name='crear_presupuesto'),
    path('presupuesto/<int:pk>/',                views.ver_presupuesto,      name='ver_presupuesto'),
    # Tickets
    path('ticket/buscar/',                       views.buscar_items_ticket,  name='buscar_items_ticket'),
    path('ticket/nuevo/<int:cita_pk>/',          views.crear_ticket,         name='crear_ticket'),
    path('ticket/<int:pk>/',                     views.ticket_detalle,       name='ticket_detalle'),
]
