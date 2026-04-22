# Módulo de Tratamientos y Planes de Pago — AdmiDent

Guía completa de uso con casos prácticos.  
URL base: `/clinico/paciente/{id}/tratamientos/`

---

## Índice

1. [Conceptos clave](#1-conceptos-clave)
2. [Pantalla de tratamientos](#2-pantalla-de-tratamientos)
3. [Caso de uso 1 — Crear un tratamiento](#3-caso-de-uso-1--crear-un-tratamiento)
4. [Caso de uso 2 — Cambiar el estado de un tratamiento](#4-caso-de-uso-2--cambiar-el-estado-de-un-tratamiento)
5. [Caso de uso 3 — Crear un plan de pagos en cuotas](#5-caso-de-uso-3--crear-un-plan-de-pagos-en-cuotas)
6. [Caso de uso 4 — Registrar el pago de una cuota](#6-caso-de-uso-4--registrar-el-pago-de-una-cuota)
7. [Caso de uso 5 — Tratamiento con pago al contado](#7-caso-de-uso-5--tratamiento-con-pago-al-contado)
8. [Caso de uso 6 — Eliminar un tratamiento](#8-caso-de-uso-6--eliminar-un-tratamiento)
9. [Cálculo de saldo y deuda](#9-cálculo-de-saldo-y-deuda)
10. [Estados y sus significados](#10-estados-y-sus-significados)
11. [Relación con otras secciones](#11-relación-con-otras-secciones)
12. [Preguntas frecuentes](#12-preguntas-frecuentes)

---

## 1. Conceptos clave

| Término | Descripción |
|---|---|
| **Servicio** | Procedimiento del catálogo (ej. "Extracción simple — Bs 150"). Define el precio de referencia. |
| **Tratamiento** | Instancia real de un servicio aplicado a un paciente. Puede tener un precio diferente al del catálogo (precio acordado). |
| **Precio acordado** | Monto negociado con el paciente para ese tratamiento específico. Puede ser mayor o menor al precio del catálogo. |
| **Plan de pago** | División del precio acordado en cuotas con fechas de vencimiento. |
| **Cuota (PlanPago)** | Una cuota individual dentro de un plan de pago. Tiene monto, fecha de vencimiento y estado. |
| **Saldo pendiente** | `Precio acordado − Total cuotas pagadas`. Lo que el paciente aún debe por ese tratamiento. |
| **Deuda total** | Suma de todas las cuotas pendientes del paciente en todos sus tratamientos. |

---

## 2. Pantalla de tratamientos

Al ingresar a `/clinico/paciente/{id}/tratamientos/` se muestra:

```
┌─────────────────────────────────────────────────────────┐
│  [Foto]  Nombre del paciente   CI · Teléfono · Email    │
│          [Ver historia] [Odontograma] [Galería] [Pagos] │
└─────────────────────────────────────────────────────────┘

  ┌───────────┐  ┌───────────┐  ┌───────────────────────┐
  │     3     │  │     1     │  │       Bs 350.00        │
  │Completados│  │En proceso │  │   Saldo pendiente      │
  └───────────┘  └───────────┘  └───────────────────────┘

  [+ Nuevo tratamiento]

  Tratamientos
  ─────────────────────────────────────────────────────────
  Tarjeta de cada tratamiento (servicio · diente · precio · estado)
```

### Barra de estadísticas

- **Completados**: Cantidad de tratamientos en estado `completado`.
- **En proceso**: Cantidad en estado `en_proceso`.
- **Saldo pendiente**: Suma del saldo pendiente de todos los tratamientos activos.

---

## 3. Caso de uso 1 — Crear un tratamiento

**Escenario**: El paciente Juan Pérez viene a su primera cita. El doctor decide realizarle una obturación en la pieza 16 y una limpieza.

### Pasos

1. Ir a `/clinico/paciente/7/tratamientos/`.
2. Hacer clic en el botón **+ Nuevo tratamiento**.
3. Se abre un panel lateral con el catálogo de servicios.
4. Buscar el servicio en la barra de búsqueda o navegar por categorías (chips horizontales).
5. Hacer clic en la tarjeta del servicio deseado — por ejemplo **"Obturación resina"**.
6. Se completa automáticamente el campo **Precio acordado** con el precio del catálogo.
7. Modificar el precio si se negoció uno diferente.
8. Seleccionar el **número de diente** (si aplica): cuadrante → pieza.
9. Agregar notas opcionales.
10. Hacer clic en **Guardar tratamiento**.

### Resultado

- Se crea un `Tratamiento` con estado inicial **`planificado`**.
- Aparece una nueva tarjeta en la lista de tratamientos.
- El contador de **Saldo pendiente** aumenta con el precio acordado (porque aún no hay cuotas pagadas).

> **Repetir** los pasos 2–10 para agregar la "Limpieza dental" como segundo tratamiento.

---

## 4. Caso de uso 2 — Cambiar el estado de un tratamiento

**Escenario**: El doctor comenzó la obturación de Juan. Después de terminarla, quiere marcarla como completada.

### Estados disponibles

```
planificado  →  en_proceso  →  completado
                             ↘  cancelado
```

### Pasos

1. En la tarjeta del tratamiento, hacer clic en el botón de estado (badge de color).
2. Se despliega un menú con los estados posibles.
3. Seleccionar el nuevo estado.
4. El cambio se guarda inmediatamente y la tarjeta actualiza su color.

### Colores por estado

| Estado | Color | Significado |
|---|---|---|
| `planificado` | Azul | Agendado, aún no iniciado |
| `en_proceso` | Amarillo/naranja | Actualmente en curso |
| `completado` | Verde | Finalizado con éxito |
| `cancelado` | Rojo/gris | Suspendido |

---

## 5. Caso de uso 3 — Crear un plan de pagos en cuotas

**Escenario**: Juan acordó pagar la obturación (Bs 600) en 3 cuotas mensuales a partir del 1 de mayo.

### Pasos

1. En la tarjeta del tratamiento **"Obturación resina — Bs 600"**, hacer clic en **Plan de pagos** (o el icono de calendario/cuotas).
2. Se abre un formulario con dos campos:
   - **Número de cuotas**: escribir `3`.
   - **Fecha de la primera cuota**: seleccionar `01/05/2026`.
3. Hacer clic en **Crear plan**.

### Lo que hace el sistema automáticamente

```
Precio acordado: Bs 600.00 ÷ 3 cuotas = Bs 200.00 por cuota

Cuota 1 — Bs 200.00 — vence 01/05/2026 — pendiente
Cuota 2 — Bs 200.00 — vence 31/05/2026 — pendiente
Cuota 3 — Bs 200.00 — vence 30/06/2026 — pendiente
```

> Las cuotas se espacian cada **30 días** a partir de la primera fecha.

### Ver el plan generado

Ir a **Pagos del paciente** (`/facturacion/paciente/7/`) para ver la tabla de cuotas con sus fechas y estados.

---

## 6. Caso de uso 4 — Registrar el pago de una cuota

**Escenario**: Juan se presenta el 2 de mayo y paga la primera cuota de Bs 200 en efectivo.

### Pasos

1. Ir a **Pagos del paciente** (`/facturacion/paciente/7/`).
2. En la tabla **Plan de pagos**, identificar la cuota 1 de "Obturación resina".
3. Hacer clic en el botón **Registrar pago** de esa cuota.
4. Se abre el formulario de pago con la cuota pre-seleccionada.
5. Completar:
   - **Método de pago**: Efectivo
   - **Monto**: `200.00` (ya viene completado)
   - **Fecha**: `02/05/2026`
   - **Concepto**: "Cuota 1 — Obturación resina" (ya viene completado)
   - **Número de recibo**: opcional
6. Hacer clic en **Registrar pago**.

### Resultado

- La cuota 1 cambia a estado **`pagado`** con fecha `02/05/2026`.
- El **saldo pendiente** del tratamiento disminuye de Bs 600 a Bs 400.
- Se crea un registro en el historial de pagos del paciente.
- El módulo de reportes de ingresos refleja el pago del día.

---

## 7. Caso de uso 5 — Tratamiento con pago al contado

**Escenario**: El doctor realiza una extracción (Bs 120) y el paciente paga todo de inmediato.

### Opción A — Sin plan de cuotas (registro directo)

1. Crear el tratamiento "Extracción simple" con precio acordado Bs 120.
2. Ir directamente a **Registrar pago** (`/facturacion/pago/nuevo/7/`).
3. Completar:
   - **Método de pago**: QR / Transferencia / Efectivo
   - **Monto**: `120.00`
   - **Concepto**: "Extracción simple — pago completo"
4. Guardar.

> En este caso **no se crea plan de cuotas**. El pago queda registrado en el historial pero el tratamiento no tendrá cuotas asociadas. El saldo pendiente del tratamiento permanecerá en Bs 120 a menos que se vincule mediante un plan de 1 cuota.

### Opción B — Plan de 1 cuota (recomendado para trazabilidad)

1. Crear el tratamiento.
2. Crear plan de pago con **1 cuota** y fecha de hoy.
3. Registrar el pago de esa cuota.

Con la opción B el sistema vincula automáticamente el pago a la cuota y el **saldo pendiente queda en Bs 0**.

---

## 8. Caso de uso 6 — Eliminar un tratamiento

**Escenario**: Se agregó por error un tratamiento duplicado.

### Pasos

1. En la tarjeta del tratamiento, hacer clic en el ícono de eliminar (papelera).
2. Aparece el **modal de confirmación**: _"¿Estás seguro de que quieres eliminar este tratamiento?"_
3. Hacer clic en **Aceptar**.

> **Advertencia**: Al eliminar un tratamiento también se eliminan sus cuotas (plan de pago) asociadas. Los pagos ya registrados (`Pago`) **no** se eliminan para mantener la integridad del historial financiero.

---

## 9. Cálculo de saldo y deuda

### Saldo pendiente por tratamiento

```
saldo_pendiente = precio_acordado − suma(cuotas con estado = 'pagado')
```

**Ejemplo**:
- Precio acordado: Bs 600
- Cuota 1 pagada: Bs 200
- Cuota 2 pagada: Bs 200
- Cuota 3 pendiente: Bs 200
- **Saldo pendiente = Bs 200**

### Deuda total del paciente

```
deuda_total = suma(todas las cuotas 'pendiente' de todos los tratamientos del paciente)
```

Esta cifra aparece en:
- La barra de estadísticas de tratamientos (campo **Saldo pendiente**).
- La pantalla de pagos del paciente.
- La tarjeta del paciente al crear un ticket/cobro.

### Cuotas vencidas

Una cuota se considera **vencida** cuando:
- Su estado es `pendiente`, **Y**
- Su `fecha_vencimiento` es anterior a la fecha actual.

Las cuotas vencidas se muestran con la fecha en **color rojo** en la tabla del plan de pagos.

---

## 10. Estados y sus significados

### Tratamiento (`Tratamiento.estado`)

| Estado | Descripción | Acción típica |
|---|---|---|
| `planificado` | Acordado, aún no iniciado | Cambiar a `en_proceso` cuando comience |
| `en_proceso` | El doctor está realizándolo (puede ser en varias sesiones) | Cambiar a `completado` al terminar |
| `completado` | Finalizado | Ninguna acción pendiente |
| `cancelado` | Suspendido por cualquier motivo | Ninguna acción pendiente |

### Cuota de pago (`PlanPago.estado`)

| Estado | Descripción | Color |
|---|---|---|
| `pendiente` | Aún no pagada | Amarillo / naranja |
| `pagado` | Pagada y vinculada a un `Pago` | Verde |
| `vencido` | Superó la fecha sin pagar | Rojo (se detecta automáticamente) |
| `cancelado` | Anulada manualmente | Gris |

---

## 11. Relación con otras secciones

```
Paciente
  ├── Tratamientos  ←─ esta pantalla
  │     └── Plan de pago (cuotas)
  │           └── Pago (registro contable)
  │
  ├── Historia clínica  (notas del doctor por sesión)
  ├── Odontograma       (mapa visual de piezas dentales)
  ├── Galería           (fotos clínicas antes/después)
  ├── Pagos             (/facturacion/paciente/{id}/)
  │     ├── Historial de pagos
  │     └── Plan de cuotas (vista consolidada)
  └── Agenda            (citas programadas)
```

### ¿Cuándo usar Ticket en lugar del plan de pagos?

| Situación | Recomendación |
|---|---|
| Cobro inmediato al finalizar una cita | **Ticket** — genera comprobante imprimible y cierra la cita automáticamente |
| Tratamiento largo con varias sesiones | **Tratamiento + Plan de pagos** — mejor trazabilidad de cuotas |
| Cobro de producto/insumo | **Ticket** — descuenta stock automáticamente |
| Presupuesto previo al tratamiento | **Presupuesto** — se puede aceptar/rechazar antes de comenzar |

---

## 12. Preguntas frecuentes

**¿Puedo cambiar el precio acordado después de crear el tratamiento?**  
No directamente desde la lista. Se debe eliminar el tratamiento y crearlo de nuevo con el precio correcto. Si ya tiene cuotas registradas, hacerlo con cuidado para no perder el historial.

**¿Qué pasa si las cuotas no suman exactamente el precio acordado?**  
El sistema divide el precio entre el número de cuotas con redondeo a 2 decimales. Si hay diferencia de centavos, esta queda reflejada en el saldo pendiente.

**¿Puedo agregar más cuotas después de crear el plan?**  
No es posible editar el plan existente desde la interfaz. Se puede cancelar el plan (eliminar las cuotas pendientes manualmente) y crear uno nuevo.

**¿El sistema marca automáticamente las cuotas como vencidas?**  
La propiedad `esta_vencida` se evalúa en tiempo real al mostrar la pantalla. No hay un proceso automático que cambie el estado a `vencido` en la base de datos; el color rojo es visual.

**¿Un tratamiento cancelado afecta la deuda del paciente?**  
Sí, mientras tenga cuotas en estado `pendiente`. Se deben cancelar también las cuotas pendientes del plan para que no aparezcan en la deuda.

**¿Puedo asociar un tratamiento a un diente específico?**  
Sí. Al crear el tratamiento se puede seleccionar el cuadrante y número de pieza (notación FDI: 11–18 superior derecho, 21–28 superior izquierdo, 31–38 inferior izquierdo, 41–48 inferior derecho).

---

*Documento generado para AdmiDent — Sistema de Gestión Dental.*
