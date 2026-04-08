# AdmiDent — Casos de Uso y Funcionalidad del Sistema

> Sistema de Gestión Dental · Django 5.1  
> Versión 1.0

---

## Índice

1. [Roles de usuario](#1-roles-de-usuario)
2. [Módulo: Pacientes](#2-módulo-pacientes)
3. [Módulo: Agenda](#3-módulo-agenda)
4. [Módulo: Clínico](#4-módulo-clínico)
5. [Módulo: Facturación](#5-módulo-facturación)
6. [Módulo: Inventario](#6-módulo-inventario)
7. [Módulo: Personal](#7-módulo-personal)
8. [Módulo: Multimedia](#8-módulo-multimedia)
9. [Módulo: Dashboard](#9-módulo-dashboard)
10. [Matriz de permisos por rol](#10-matriz-de-permisos-por-rol)

---

## 1. Roles de usuario

| Rol | Descripción |
|---|---|
| **Administrador** | Acceso total al sistema. Ve todos los módulos, reportes, personal e inventario. |
| **Dentista** | Ve su propia agenda, sus pacientes y su historial clínico. |
| **Asistente** | Apoya en agenda y pacientes. Acceso limitado. |
| **Recepcionista** | Gestiona citas, pacientes y cobros básicos. |

---

## 2. Módulo: Pacientes

**URL base:** `/pacientes/`

### Descripción
Registro central de todos los pacientes de la clínica. Almacena datos personales, médicos, historial de alergias y archivos adjuntos.

### Casos de uso

#### CU-PAC-01: Registrar nuevo paciente
- **Actor:** Recepcionista, Asistente, Administrador
- **Flujo:**
  1. Acceder a `/pacientes/nuevo/`
  2. Ingresar datos personales: nombres, apellidos, C.I., fecha de nacimiento, sexo, tipo de sangre, teléfono, email, dirección
  3. Subir foto de perfil (opcional) con vista previa
  4. Ingresar contacto de emergencia
  5. Guardar — el sistema crea el registro y redirige al detalle
- **Validaciones:** C.I. no duplicado, campos obligatorios marcados con `*`

#### CU-PAC-02: Ver detalle de paciente
- **Actor:** Todos los roles
- **Flujo:**
  1. Buscar paciente desde el listado o la barra de búsqueda global
  2. Ver datos personales, resumen de deuda, próximas citas, historial de pagos
  3. Accesos rápidos a: Historia clínica, Odontograma, Tratamientos, Presupuestos, Galería
- **Información visible:** datos personales, alergias registradas, documentos adjuntos, deuda pendiente

#### CU-PAC-03: Editar datos del paciente
- **Actor:** Recepcionista, Asistente, Administrador
- **Flujo:**
  1. Desde el detalle, clic en "Editar"
  2. Modificar campos necesarios
  3. Cambiar foto de perfil con vista previa antes de guardar
  4. Guardar cambios

#### CU-PAC-04: Registrar alergia
- **Actor:** Dentista, Asistente, Administrador
- **Flujo:**
  1. Desde el detalle del paciente, sección "Alergias"
  2. Indicar tipo, descripción, reacción y gravedad
  3. Guardar — aparece en el perfil como alerta visual

#### CU-PAC-05: Subir documento adjunto
- **Actor:** Todos los roles
- **Descripción:** Adjuntar radiografías, recetas, exámenes de laboratorio u otros archivos al expediente del paciente
- **Tipos:** radiografía, receta, examen, consentimiento, otro

#### CU-PAC-06: Buscar paciente
- **Actor:** Todos los roles
- **Flujo:**
  1. Usar la barra de búsqueda en el topbar (escritorio) o el modal de búsqueda (móvil)
  2. Buscar por nombre, apellido, C.I. o teléfono
  3. Resultados en tiempo real desde 2 caracteres

### Datos principales del paciente

| Campo | Descripción |
|---|---|
| Nombres / Apellidos | Nombre completo |
| C.I. | Cédula de identidad |
| Fecha de nacimiento | Calcula edad automáticamente |
| Tipo de sangre | A+, A-, B+, B-, AB+, AB-, O+, O- |
| Teléfono / Email | Contacto directo |
| Foto de perfil | Imagen con vista previa al editar |
| Alergias | Lista con nivel de gravedad |
| Archivos adjuntos | Documentos clínicos digitalizados |

---

## 3. Módulo: Agenda

**URL base:** `/agenda/`

### Descripción
Gestión completa de citas médicas. Incluye calendario interactivo, verificación de disponibilidad en tiempo real y detección de conflictos de horario.

### Casos de uso

#### CU-AGE-01: Ver calendario de citas
- **Actor:** Todos los roles
- **Flujo:**
  1. Acceder a `/agenda/`
  2. Ver citas en vista mes/semana/día
  3. Filtrar por doctor (admin) o ver solo las propias (dentista)
  4. Cada evento muestra: paciente, servicio, horario, estado y color del doctor
- **Funcionalidad:** arrastrar citas para reprogramar, clic en evento para ver detalles

#### CU-AGE-02: Crear nueva cita
- **Actor:** Todos los roles
- **Flujo:**
  1. Clic en un slot del calendario o botón "Nueva cita"
  2. Seleccionar paciente (existente o nuevo inline)
  3. Seleccionar doctor (pre-seleccionado al usuario actual si es dentista)
  4. Seleccionar sillón y servicio
  5. Indicar fecha, hora de inicio y hora de fin
  6. El sistema verifica disponibilidad en tiempo real
  7. Modal de confirmación muestra resumen antes de guardar
- **Validaciones:**
  - Hora fin > hora inicio
  - Sin solapamiento con citas existentes del doctor
  - Panel de disponibilidad muestra doctores libres y ocupados

#### CU-AGE-03: Verificar disponibilidad de doctor
- **Actor:** Todos los roles (automático al llenar el formulario)
- **Flujo:**
  1. Al seleccionar doctor, fecha y horario, el sistema consulta `/agenda/citas/disponibilidad/` automáticamente
  2. Panel verde: doctor disponible
  3. Panel rojo: conflicto — muestra la cita que colisiona
  4. Botones clicables de doctores disponibles para seleccionar rápidamente
- **Tiempo de respuesta:** verificación con debounce de 380ms

#### CU-AGE-04: Editar cita existente
- **Actor:** Todos los roles
- **Flujo:**
  1. Clic en la cita en el calendario o desde el listado de hoy
  2. Modificar doctor, sillón, servicio, fecha u horario
  3. El sistema re-verifica disponibilidad excluyendo la cita actual
  4. Confirmar en modal de resumen

#### CU-AGE-05: Cambiar estado de cita
- **Actor:** Todos los roles
- **Estados disponibles:**

| Estado | Descripción |
|---|---|
| Programada | Cita agendada, pendiente de confirmación |
| Confirmada | Paciente confirmó asistencia |
| En curso | Atención en progreso |
| Completada | Atención finalizada |
| Cancelada | Cita cancelada |
| No asistió | Paciente no se presentó |

- **Restricción:** citas cobradas no pueden cambiar de estado

#### CU-AGE-06: Ver agenda del día
- **Actor:** Todos los roles
- **Flujo:** Acceder a `/agenda/hoy/` — lista cronológica de todas las citas del día con estado, paciente y doctor

#### CU-AGE-07: Cobrar cita directamente
- **Actor:** Recepcionista, Administrador
- **Flujo:**
  1. Desde el detalle de la cita, clic en "Cobrar"
  2. El sistema genera un ticket de pago vinculado a la cita
  3. La cita queda marcada como cobrada

#### CU-AGE-08: Mover cita (drag & drop)
- **Actor:** Todos los roles
- **Flujo:** Arrastrar el evento en el calendario a una nueva fecha/hora — el sistema actualiza automáticamente

---

## 4. Módulo: Clínico

**URL base:** `/clinico/`

### Descripción
Historial clínico completo del paciente. Incluye odontograma interactivo, historia clínica, notas de consulta y plan de tratamientos.

### Casos de uso

#### CU-CLI-01: Ver y editar odontograma
- **Actor:** Dentista, Administrador
- **Flujo:**
  1. Desde el detalle del paciente, acceder al odontograma
  2. Hacer clic en cualquier diente para registrar su condición
  3. Condiciones: sano, caries, obturado, ausente, corona, implante, fractura, etc.
  4. Guardar — el odontograma queda asociado al paciente con fecha y doctor

#### CU-CLI-02: Historia clínica
- **Actor:** Dentista, Administrador
- **Flujo:**
  1. Acceder a `/clinico/paciente/<id>/historia/`
  2. Registrar motivo de consulta inicial, antecedentes médicos, antecedentes dentales, hábitos
  3. Agregar notas de consulta en cada visita: hallazgos, diagnóstico, plan de tratamiento
- **Una historia clínica por paciente**, con múltiples notas de consulta cronológicas

#### CU-CLI-03: Plan de tratamientos
- **Actor:** Dentista, Administrador
- **Flujo:**
  1. Acceder a `/clinico/paciente/<id>/tratamientos/`
  2. Agregar tratamiento: seleccionar servicio, diente, doctor, precio acordado
  3. Vincular tratamiento a una cita al agendar
  4. Actualizar estado: pendiente → en proceso → completado
- **Integración:** los tratamientos vinculados aparecen en el calendario con ícono especial

#### CU-CLI-04: Gestionar servicios (solo admin)
- **Actor:** Administrador
- **Flujo:**
  1. Acceder a `/clinico/servicios/`
  2. Ver lista de servicios agrupados por categoría con precio y duración
  3. Editar precio, duración o descripción desde un modal
  4. Activar/desactivar servicios sin eliminarlos
- **Categorías:** Preventivo, Restaurador, Endodoncia, Cirugía, Ortodoncia, Estética, Periodoncia

---

## 5. Módulo: Facturación

**URL base:** `/facturacion/`

### Descripción
Gestión financiera de la clínica. Maneja pagos, presupuestos, tickets de cobro, planes de pago y reportes de ingresos.

### Casos de uso

#### CU-FAC-01: Registrar pago
- **Actor:** Recepcionista, Administrador
- **Flujo:**
  1. Acceder a `/facturacion/pago/nuevo/` o desde el detalle del paciente
  2. Seleccionar paciente, doctor, método de pago y monto
  3. Ingresar concepto y número de recibo (opcional)
  4. Guardar — el pago queda registrado y reduce la deuda del paciente

#### CU-FAC-02: Ver historial de pagos del paciente
- **Actor:** Todos los roles
- **Flujo:**
  1. Desde el detalle del paciente, acceder a "Pagos"
  2. Ver lista cronológica de pagos, total pagado y deuda pendiente
  3. Botón "Registrar pago" para agregar nuevo

#### CU-FAC-03: Crear presupuesto
- **Actor:** Dentista, Recepcionista, Administrador
- **Flujo:**
  1. Acceder a `/facturacion/presupuesto/<paciente_id>/nuevo/`
  2. Agregar servicios desde un modal de selección con buscador
  3. Especificar diente, cantidad, precio y descuento por ítem
  4. El sistema calcula subtotales y total en tiempo real
  5. Guardar con estado: borrador, presentado, aprobado, rechazado
- **Acciones:** imprimir/exportar a PDF, cambiar estado

#### CU-FAC-04: Ver presupuesto
- **Actor:** Todos los roles
- **Flujo:**
  1. Acceder a `/facturacion/presupuesto/<id>/`
  2. Ver tabla de ítems con precios y descuentos
  3. Cambiar estado del presupuesto
  4. Imprimir versión para el paciente
- **Responsive:** tabla en desktop, tarjetas en móvil

#### CU-FAC-05: Generar ticket de cobro
- **Actor:** Recepcionista, Administrador
- **Flujo:**
  1. Al completar una cita, clic en "Cobrar"
  2. El sistema genera un ticket numerado vinculado a la cita
  3. Seleccionar método de pago y aplicar descuento global
  4. El ticket lista los servicios prestados con precios
  5. Imprimir o guardar

#### CU-FAC-06: Plan de pagos en cuotas
- **Actor:** Recepcionista, Administrador
- **Flujo:**
  1. Desde un tratamiento, crear plan de pago
  2. Definir número de cuotas y fechas de vencimiento
  3. Registrar el pago de cada cuota individualmente
  4. El sistema marca las cuotas como pagadas/pendientes/vencidas

#### CU-FAC-07: Reporte de ingresos (solo admin)
- **Actor:** Administrador
- **Flujo:**
  1. Acceder a `/facturacion/reporte/`
  2. Ver KPIs: ingresos del día, semana, mes y año
  3. Gráfico de barras de ingresos por período
  4. Filtrar por: días (últimos 30), meses (últimos 12), años (últimos 5)
  5. Tabla de ingresos por doctor con total, cantidad de cobros y pacientes únicos
  6. Tabla por método de pago
  7. Exportar a Excel
- **Móvil:** gráfico se abre en modal para mejor visualización

---

## 6. Módulo: Inventario

**URL base:** `/inventario/`  
**Acceso:** Solo Administrador

### Descripción
Control de stock de insumos y materiales dentales. Registra entradas, salidas y genera alertas de reposición.

### Casos de uso

#### CU-INV-01: Ver lista de insumos
- **Actor:** Administrador
- **Flujo:**
  1. Acceder a `/inventario/`
  2. Ver todos los insumos activos agrupados por categoría
  3. Ver stock actual vs stock mínimo
  4. Alertas visuales en rojo para insumos que necesitan reposición

#### CU-INV-02: Registrar nuevo insumo
- **Actor:** Administrador
- **Flujo:**
  1. Clic en "Nuevo insumo"
  2. Ingresar: nombre, categoría, unidad de medida, stock actual, stock mínimo, precio unitario, proveedor
  3. Guardar

#### CU-INV-03: Registrar movimiento de inventario
- **Actor:** Administrador
- **Flujo:**
  1. Desde el listado, clic en el insumo → "Movimiento"
  2. Seleccionar tipo: entrada (compra/donación) o salida (uso/merma)
  3. Ingresar cantidad y motivo
  4. El sistema actualiza el stock automáticamente y registra el historial
- **Alerta automática:** si el stock cae por debajo del mínimo, se muestra alerta en el listado

### Categorías de insumos
Anestesia · Resinas y composites · Instrumental · Descartables · Medicamentos

---

## 7. Módulo: Personal

**URL base:** `/personal/`  
**Acceso:** Lista/CRUD → solo Administrador · Mi perfil → todos los roles

### Descripción
Gestión del equipo de la clínica. Administra usuarios, roles, especialidades y configuración de agenda por doctor.

### Casos de uso

#### CU-PER-01: Ver lista de personal
- **Actor:** Administrador
- **Flujo:**
  1. Acceder a `/personal/`
  2. Ver todos los miembros activos con rol, especialidad y estado
  3. Accesos rápidos a editar o desactivar

#### CU-PER-02: Crear nuevo usuario del sistema
- **Actor:** Administrador
- **Flujo:**
  1. Acceder a `/personal/nuevo/`
  2. Ingresar datos personales y credenciales de acceso
  3. Asignar rol: Administrador, Dentista, Asistente o Recepcionista
  4. Para dentistas: ingresar especialidad y color de agenda
  5. Guardar — el usuario puede iniciar sesión inmediatamente

#### CU-PER-03: Editar datos de personal
- **Actor:** Administrador
- **Flujo:**
  1. Desde la lista, clic en "Editar"
  2. Modificar datos, rol, especialidad o color de agenda
  3. Opción de cambiar contraseña

#### CU-PER-04: Desactivar/activar usuario
- **Actor:** Administrador
- **Descripción:** Desactivar un usuario impide su acceso al sistema sin eliminarlo. El historial clínico queda intacto.

#### CU-PER-05: Gestionar mi perfil (todos los usuarios)
- **Actor:** Todos los roles
- **Flujo:**
  1. Acceder a `/personal/perfil/`
  2. Actualizar foto de perfil, teléfono y datos personales
  3. Cambiar contraseña
- **Cada usuario solo puede editar su propio perfil**

### Color de agenda por doctor
Cada dentista tiene asignado un color único que se refleja en:
- Eventos del calendario (color del evento)
- Leyenda del calendario (chip de color)
- Filtros de doctor

---

## 8. Módulo: Multimedia

**URL base:** `/multimedia/`

### Descripción
Galería fotográfica clínica por paciente. Permite documentar el progreso del tratamiento con fotos del antes/después.

### Casos de uso

#### CU-MUL-01: Ver galería del paciente
- **Actor:** Dentista, Administrador
- **Flujo:**
  1. Desde el detalle del paciente, acceder a "Galería"
  2. Ver fotos organizadas por tipo y fecha
  3. Fotos asociadas a un diente específico o tratamiento

#### CU-MUL-02: Subir foto clínica
- **Actor:** Dentista, Asistente, Administrador
- **Flujo:**
  1. En la galería, clic en "Subir foto"
  2. Seleccionar imagen, tipo (antes, durante, después, radiografía, extra)
  3. Agregar título, descripción, número de diente y tratamiento relacionado
  4. Guardar

#### CU-MUL-03: Comparación antes/después
- **Actor:** Dentista, Administrador
- **Flujo:**
  1. Acceder a "Comparar" en la galería del paciente
  2. Seleccionar foto "antes" y foto "después"
  3. El sistema genera una comparación visual lado a lado
  4. Agregar título y notas

---

## 9. Módulo: Dashboard

**URL:** `/`

### Descripción
Panel principal personalizado según el rol del usuario. Muestra información relevante de un vistazo.

### Vista para Administrador

| Sección | Contenido |
|---|---|
| KPIs | Pacientes activos · Citas hoy · Citas del mes · Ingresos del mes |
| Tabla citas hoy | Hora, paciente, doctor, servicio, estado (clic → editar) |
| Resumen de estados | Conteo por estado de las citas del día |
| Próximas citas | Lista con doctor, fecha y servicio |
| Acceso rápido | Nuevo paciente · Agendar cita · Ver reportes · Gestionar personal |

### Vista para Dentista / Asistente / Recepcionista

| Sección | Contenido |
|---|---|
| KPIs | Mis pacientes · Citas hoy · Citas del mes · Completadas del mes |
| Tabla mis citas hoy | Hora, paciente, servicio, estado (sin columna doctor) |
| Mis próximas citas | Lista con fecha, hora, servicio y estado |
| Acceso rápido | Agendar cita · Ver mis pacientes · Calendario · Agenda de hoy |

---

## 10. Matriz de permisos por rol

| Módulo / Acción | Admin | Dentista | Asistente | Recepcionista |
|---|:---:|:---:|:---:|:---:|
| **Dashboard** — ver propio | ✅ | ✅ | ✅ | ✅ |
| **Pacientes** — listar todos | ✅ | ❌ (solo propios) | ❌ (solo propios) | ✅ |
| **Pacientes** — crear/editar | ✅ | ✅ | ✅ | ✅ |
| **Agenda** — ver calendario propio | ✅ | ✅ | ✅ | ✅ |
| **Agenda** — ver todos los doctores | ✅ | ❌ | ❌ | ❌ |
| **Agenda** — crear/editar citas | ✅ | ✅ | ✅ | ✅ |
| **Clínico** — historia/odontograma | ✅ | ✅ | ✅ | ❌ |
| **Clínico** — servicios (CRUD) | ✅ | ❌ | ❌ | ❌ |
| **Facturación** — pagos/tickets | ✅ | ✅ | ✅ | ✅ |
| **Facturación** — presupuestos | ✅ | ✅ | ✅ | ✅ |
| **Facturación** — reportes | ✅ | ❌ | ❌ | ❌ |
| **Inventario** — todo | ✅ | ❌ | ❌ | ❌ |
| **Personal** — lista/CRUD | ✅ | ❌ | ❌ | ❌ |
| **Personal** — mi perfil | ✅ | ✅ | ✅ | ✅ |
| **Multimedia** — galería | ✅ | ✅ | ✅ | ❌ |

---

## Flujos principales del sistema

```
Nuevo paciente
     │
     ▼
Historia clínica ──► Odontograma
     │
     ▼
Plan de tratamiento
     │
     ▼
Agendar cita ──► Verificación disponibilidad
     │
     ▼
Atención (en curso)
     │
     ├──► Nota clínica
     ├──► Foto clínica (galería)
     └──► Actualizar tratamiento
          │
          ▼
     Cobrar cita ──► Ticket de pago
          │
          ▼
     Reporte de ingresos (admin)
```

---

*AdmiDent — Sistema de Gestión Dental · Documentación v1.0*
