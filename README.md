# VitalPet 🐾 - Sistema Integral de Gestión Veterinaria en Odoo 18

**Descripción**: Sistema profesional para la gestión integral de clínicas veterinarias, incluyendo:
- 📅 Agendar citas y visualización en calendario
- 📋 Gestión de historiales clínicos de mascotas
- 💊 Control de medicamentos e inventario
- 🛒 Integración con ventas e inventario de Odoo
- 💰 Facturación automática de servicios
- 👥 CRM para gestión de propietarios/clientes

**Stack Tecnológico**: Odoo 18.0 + PostgreSQL 15 + Docker Compose

## 📋 Estructura del Proyecto

```
Proyecto Odoo/
├── 🐳 INFRAESTRUCTURA
│   ├── docker-compose.yml          # Orquestación de servicios (Odoo + PostgreSQL)
│   ├── .devcontainer/              # Configuración VS Code dev container
│   │   └── devcontainer.json
│   ├── odoo.conf                   # Configuración de servidor Odoo
│   ├── .env                        # Variables de entorno (PostgreSQL, puertos)
│   ├── .env.example                # Template de variables de entorno
│   └── .gitignore                  # Exclusiones de versionado
│
├── 📚 DOCUMENTACIÓN
│   ├── README.md                   # Este archivo
│   ├── INTEGRACION_MODULOS.md      # Guía de integración con módulos Odoo
│   └── ExplicacionModeloOdoo.txt   # Notas de modelo de datos
│
└── 📦 MÓDULO PERSONALIZADO
    └── custom_addons/
        └── veterinaria_core/       # Módulo base: Gestión Veterinaria
            ├── __init__.py         # Inicializador del paquete
            ├── __manifest__.py     # Metadatos del módulo (dependencias, vistas, etc.)
            │
            ├── models/             # Modelos de datos ORM
            │   ├── __init__.py
            │   ├── paciente.py             # Mascotas/Pacientes
            │   ├── historia_clinica.py     # Registros de consultas
            │   ├── medicamento.py          # Catálogo de medicamentos
            │   ├── cita.py                 # Citas/Calendario
            │   └── producto.py             # Productos veterinarios
            │
            ├── views/              # Vistas XML (Forms, Lists, Calendars, etc.)
            │   ├── menu.xml                # Estructura de menú y acciones
            │   ├── paciente_view_new.xml   # Formulario profesional de pacientes
            │   ├── historia_clinica_view_new.xml  # Formulario de historiales
            │   ├── cita_view_new.xml       # Formulario de citas (con calendario)
            │   ├── medicamento_view_new.xml # Formulario de medicamentos
            │   ├── producto_view_new.xml   # Formulario de productos
            │   └── [archivos _view.xml]    # Vistas originales (legacy)
            │
            ├── security/           # Control de acceso
            │   └── ir.model.access.csv     # Permisos por grupo de usuarios
            │
            └── static/             # Recursos estáticos (CSS, JS, imágenes)
                └── description/
                    └── icon.png
```

## 🚀 Inicio Rápido

### Requisitos
- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Git** (para versionado)

### Levantar el Proyecto

```bash
# Clonar o descargar el proyecto
cd "Proyecto Odoo"

# Levantar contenedores (PostgreSQL + Odoo)
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f odoo
```

**Acceso a Odoo**:
- 🌐 URL: `http://localhost:8070`
- 👤 Usuario: `admin`
- 🔐 Contraseña: `admin`

### Instalar el Módulo Veterinaria

1. Ir a **Aplicaciones** en Odoo
2. Buscar "Veterinaria" o "veterinaria_core"
3. Hacer clic en **Instalar**
4. El menú "Veterinaria" aparecerá en la barra lateral

### Detener el Proyecto

```bash
# Pausar servicios (mantiene datos)
docker-compose stop

# Parar y eliminar contenedores (mantiene datos en volúmenes)
docker-compose down

# Parar y BORRAR todo (base de datos, volúmenes)
docker-compose down -v
```

### Reiniciar o Actualizar el Módulo

```bash
# Reiniciar Odoo (cuando cambies código)
docker-compose restart odoo

# Ver logs después de reinicio
docker-compose logs -f odoo | grep -i veterinaria
```

## 📝 Configuración

### Variables de Entorno (`.env`)

El archivo `.env` controla la configuración de servicios:

```env
# PostgreSQL (Base de Datos)
POSTGRES_DB=odoo              # Nombre de la base de datos
POSTGRES_USER=odoo            # Usuario de PostgreSQL
POSTGRES_PASSWORD=odoo        # Contraseña de PostgreSQL
DB_HOST=db                    # Host del contenedor DB
DB_PORT=5432                  # Puerto PostgreSQL
POSTGRES_DATA_PATH=./postgres_data  # Ruta de datos persistentes

# Odoo Server
ODOO_PORT=8070                # Puerto expuesto (localhost:8070)
ODOO_LOG_LEVEL=info           # Nivel de logging (debug, info, warning, error)
ODOO_WORKERS=4                # Número de worker processes
ODOO_ADMIN_PASSWD=admin       # Contraseña de master (para crear/eliminar BDs)
```

**Crear el archivo `.env`**:
```bash
cp .env.example .env
# Editar si necesitas cambiar valores por defecto
```

### Configuración de Odoo (`odoo.conf`)

Archivo de configuración del servidor Odoo:
- `db_host`, `db_port`, `db_user`, `db_password`: Conexión a PostgreSQL
- `db_name`: Nombre de la base de datos
- `addons_path`: Rutas donde buscar módulos
- `log_level`: Verbosidad de logs
- `workers`: Procesos simultáneos

**Editar solo si es necesario** - Valores por defecto incluídos.

### Volúmenes Docker

Los datos persistentes se almacenan en:
- `./postgres_data/`: Base de datos PostgreSQL
- `./custom_addons/`: Módulos personalizados
- Ambos están en `.gitignore` para no versionar datos

## 📦 Módulo: veterinaria_core

### Modelos de Datos

#### 1️⃣ Paciente (`veterinaria.paciente`)
Representa una mascota/animal bajo cuidado veterinario.

**Campos principales**:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | Char | Nombre de la mascota |
| `especie` | Selection | Perro, Gato, Conejo, Loro, etc. |
| `raza` | Char | Raza de la mascota |
| `fecha_nacimiento` | Date | Fecha de nacimiento |
| `peso` | Float | Peso en kg |
| `foto` | Binary | Imagen/foto de la mascota |
| `propietario_id` | Many2one | Vínculo con contacto (res.partner) |
| `alergias` | Text | Alergias conocidas |
| `estado_vacunacion` | Selection | Al día / Atrasado / Sin vacunas |
| `microchip` | Char | Número de microchip (opcional) |
| `estado` | Selection | Activo / Inactivo / Fallecido |
| `historia_clinica_ids` | One2many | Listado de consultas realizadas |

#### 2️⃣ Cita (`veterinaria.cita`)
Gestiona las citas veterinarias programadas.

**Campos principales**:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | Char | Nombre/ID de la cita |
| `paciente_id` | Many2one | Mascota a atender |
| `veterinario_id` | Many2one | Profesional veterinario (hr.employee) |
| `fecha_inicio` | Datetime | Fecha y hora de inicio |
| `fecha_fin` | Datetime | Fecha y hora de finalización |
| `motivo` | Text | Motivo de la cita |
| `estado` | Selection | Pendiente / Confirmada / Completada / Cancelada |
| `notas` | Text | Observaciones adicionales |

**Vista especial**: Aparece en **Calendario** con colores por veterinario

#### 3️⃣ Historia Clínica (`veterinaria.historia_clinica`)
Registro de cada consulta/tratamiento realizado.

**Campos principales**:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `paciente_id` | Many2one | Mascota consultada |
| `veterinario_id` | Many2one | Veterinario que atendió |
| `fecha` | Datetime | Fecha y hora de la consulta |
| `motivo_consulta` | Text | Razón de la consulta |
| `diagnostico` | Text | Diagnóstico realizado |
| `tratamiento` | Html | Tratamiento prescrito |
| `medicamento_ids` | Many2many | Medicamentos recetados |
| `proxima_cita` | Datetime | Fecha de seguimiento |
| `temperatura` | Float | Temp. corporal en °C |
| `frecuencia_cardiaca` | Float | Pulsaciones por minuto |
| `peso_consulta` | Float | Peso en kg al momento |
| `estado` | Selection | Pendiente / Completada / Cancelada |

#### 4️⃣ Medicamento (`veterinaria.medicamento`)
Catálogo de medicamentos disponibles.

**Campos principales**:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | Char | Nombre del medicamento |
| `principio_activo` | Char | Compuesto activo |
| `tipo` | Char | Tipo (Antibiótico, Analgésico, etc.) |
| `via_administracion` | Selection | Oral / Inyectable / Tópico / Otro |
| `dosis_recomendada` | Char | Dosis sugerida |
| `descripcion` | Html | Descripción detallada |
| `contraindicaciones` | Html | Cuándo NO usar |
| `efectos_secundarios` | Html | Efectos adversos posibles |
| `proveedor_id` | Many2one | Proveedor (res.partner) |
| `activo` | Boolean | ¿Disponible en catálogo? |

#### 5️⃣ Producto Veterinario (`veterinaria.producto`)
Productos para venta (alimentos, accesorios, equipos, etc.).

**Campos principales**:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | Char | Nombre del producto |
| `tipo` | Selection | Medicamento / Alimento / Accesorio / Equipo / Servicio |
| `precio` | Float | Precio de venta |
| `cantidad` | Integer | Stock disponible |
| `descripcion` | Html | Descripción del producto |
| `proveedor_id` | Many2one | Proveedor (res.partner) |
| `activo` | Boolean | ¿Disponible para venta? |

---

### Relaciones entre Modelos

```
┌──────────────┐
│ res.partner  │ (Contactos/CRM)
│ (Clientes)   │
└──────┬───────┘
       │ 1:N
       │ propietario_id
       │
       ↓
┌──────────────┐      1:N       ┌─────────────────┐
│  Paciente    ├──────────────→ │ Historia Clínica│
│  (Mascotas)  │ historia_ids   │  (Consultas)    │
└──────────────┘                └────────┬────────┘
                                         │ N:N
                                         ↓
                                  ┌──────────────┐
                                  │ Medicamento  │
                                  │  (Catálogo)  │
                                  └──────────────┘

┌──────────────┐
│  Paciente    │
└──────┬───────┘
       │ 1:N
       │ paciente_id
       ↓
┌──────────────┐
│  Cita        │
│ (Calendario) │
└──────────────┘

┌──────────────┐
│  Producto    │ ← Vínculo con Inventario de Odoo
│  (Almacén)   │
└──────────────┘
```

---

### Dependencias de Módulos Odoo

El módulo `veterinaria_core` requiere:
- **base**: Funcionalidades básicas de Odoo
- **sale_management**: Gestión de ventas (cotizaciones, órdenes)
- **account**: Facturación y contabilidad
- **stock**: Gestión de inventario
- **crm**: Gestión de relaciones con clientes
- **calendar**: Vistas de calendario para citas

**Módulos relacionados disponibles en Odoo**:
- ✅ **Contactos** (res.partner): Para propietarios y proveedores
- ✅ **Recursos Humanos** (hr): Para veterinarios (hr.employee)
- ✅ **Inventario**: Stock de medicamentos y productos

## 🔧 Desarrollo

### Crear un Nuevo Modelo

En `custom_addons/veterinaria_core/models/`:

**Paso 1**: Crear archivo `mi_modelo.py`:
```python
from odoo import models, fields

class MiModelo(models.Model):
    _name = 'veterinaria.mi_modelo'
    _description = 'Descripción del modelo'
    _inherit = ['mail.thread']  # Opcional: para comentarios

    name = fields.Char('Nombre', required=True)
    descripcion = fields.Text('Descripción')
    fecha = fields.Datetime('Fecha', default=fields.Datetime.now)
    activo = fields.Boolean('Activo?', default=True)
    
    # Relación con otro modelo
    paciente_id = fields.Many2one('veterinaria.paciente', 'Paciente')
```

**Paso 2**: Registrarlo en `models/__init__.py`:
```python
from . import paciente
from . import historia_clinica
from . import medicamento
from . import cita
from . import producto
from . import mi_modelo  # ← AGREGAR ESTA LÍNEA
```

**Paso 3**: Actualizar `__manifest__.py`:
```python
{
    'name': 'Veterinaria Core',
    'version': '18.0.1.0.0',
    'depends': ['base', 'sale_management', 'account', 'stock', 'crm', 'calendar', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/paciente_view_new.xml',
        # ... más vistas
    ],
    'installable': True,
    'auto_install': False,
}
```

### Crear una Vista XML

En `custom_addons/veterinaria_core/views/`:

**Paso 1**: Crear archivo `mi_modelo_view.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        <!-- VISTA LISTA (Tree) -->
        <record id="mi_modelo_view_list" model="ir.ui.view">
            <field name="name">Modelo - Lista</field>
            <field name="model">veterinaria.mi_modelo</field>
            <field name="arch" type="xml">
                <list>
                    <field name="name"/>
                    <field name="fecha"/>
                    <field name="activo"/>
                </list>
            </field>
        </record>

        <!-- VISTA FORMULARIO -->
        <record id="mi_modelo_view_form" model="ir.ui.view">
            <field name="name">Modelo - Formulario</field>
            <field name="model">veterinaria.mi_modelo</field>
            <field name="arch" type="xml">
                <form>
                    <sheet>
                        <h1><field name="name"/></h1>
                        <group>
                            <field name="fecha"/>
                            <field name="paciente_id"/>
                        </group>
                        <notebook>
                            <page string="Detalles">
                                <field name="descripcion"/>
                            </page>
                        </notebook>
                    </sheet>
                </form>
            </field>
        </record>

        <!-- ACCIÓN (Menú) -->
        <record id="mi_modelo_action" model="ir.actions.act_window">
            <field name="name">Mi Modelo</field>
            <field name="res_model">veterinaria.mi_modelo</field>
            <field name="view_mode">list,form</field>
        </record>
    </data>
</odoo>
```

### Agregar a Menú

En `views/menu.xml`, agregar dentro de `<menuitem id="veterinaria_menu_item_manage">`:
```xml
<menuitem id="veterinaria_submenu_mi_modelo"
    name="Mi Modelo"
    action="veterinaria_core.mi_modelo_action"
    parent="veterinaria_menu_item_manage"/>
```

### Agregar Acceso de Seguridad

En `security/ir.model.access.csv`, agregar línea:
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_mi_modelo_all,Access veterinaria.mi_modelo,model_veterinaria_mi_modelo,base.group_user,1,1,1,1
```

### Recargar Módulo

```bash
# Reiniciar Odoo
docker-compose restart odoo

# Ver logs
docker-compose logs -f odoo | head -100
```

Luego en Odoo:
1. Ir a **Aplicaciones**
2. Buscar "Veterinaria Core"
3. Hacer clic en **⚙️ Actualizar** (o Desinstalar → Reinstalar)

---

## 📊 Flujo de Datos Típico

```
1. CREAR PACIENTE
   └─ Ingresar nombre, especie, propietario (desde Contactos)

2. AGENDAR CITA
   └─ Seleccionar paciente, fecha, veterinario
   └─ Aparece en CALENDARIO

3. REALIZAR CONSULTA
   └─ Crear Historia Clínica
   └─ Seleccionar medicamentos del catálogo
   └─ Registrar diagnóstico y vitales

4. VENDER PRODUCTOS
   └─ Ir a Ventas (módulo Odoo estándar)
   └─ Crear orden de venta
   └─ Agregar Productos Veterinarios
   └─ Confirmar y Facturar

5. CONTABILIDAD
   └─ Factura se registra automáticamente
   └─ Reportes de ingresos disponibles en Contabilidad
```

---

## 🐛 Solución de Problemas

### Problema: "Modelo no encontrado"
**Solución**: 
```bash
docker-compose restart odoo
# O reinstalar el módulo en Aplicaciones
```

### Problema: "Permiso denegado"
**Solución**: 
- Ir a **Configuración → Seguridad → Control de Acceso**
- Verificar permisos en `security/ir.model.access.csv`

### Problema: "Cambios no aparecen"
**Solución**:
- Limpiar caché del navegador (Ctrl+Shift+Del)
- Reiniciar Odoo: `docker-compose restart odoo`

### Problema: Base de datos corrupta
**Solución**:
```bash
# ADVERTENCIA: ELIMINA TODOS LOS DATOS
docker-compose down -v
docker-compose up -d
# Ir a http://localhost:8070 e instalar módulo nuevamente
```

---

## 📚 Documentación Adicional

VitalPet incluye documentación completa para desarrollo, deployment y troubleshooting:

### 📖 Guías Esenciales

| Documento | Descripción | Audiencia |
|-----------|-----------|-----------|
| **[PRIMEROS_PASOS.md](PRIMEROS_PASOS.md)** | Guía paso a paso para iniciarse con el sistema | Usuarios nuevos, QA |
| **[INTEGRACION_MODULOS.md](INTEGRACION_MODULOS.md)** | Cómo integran los módulos Odoo (Ventas, Inventario, CRM) | Product Owner, Desarrolladores |
| **[ESPECIFICACIONES_TECNICAS.md](ESPECIFICACIONES_TECNICAS.md)** | Arquitectura, BD, modelos ORM, seguridad | Arquitectos, Desarrolladores, DevOps |
| **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** | Lista de verificación para go-live | DevOps, QA Lead |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Solución de problemas comunes con FAQ | Soporte, Desarrolladores |

### 🚀 Flujo Recomendado de Lecturas

1. **Primer día**: 
   - Leer este README
   - Ejecutar [PRIMEROS_PASOS.md](PRIMEROS_PASOS.md)
   - Crear 2-3 pacientes de prueba

2. **Primera semana**:
   - Estudiar [INTEGRACION_MODULOS.md](INTEGRACION_MODULOS.md)
   - Revisar [ESPECIFICACIONES_TECNICAS.md](ESPECIFICACIONES_TECNICAS.md)

3. **Antes de producción**:
   - Completar [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
   - Revisar [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 📚 Documentación Oficial
        <record id="view_model_list" model="ir.ui.view">
            <field name="name">veterinaria.modelo.list</field>
            <field name="model">veterinaria.modelo</field>
            <field name="arch" type="xml">
                <tree>
                    <field name="name"/>
                </tree>
            </field>
        </record>
    </data>
</odoo>
```

## 🐛 Solución de Problemas

### Los contenedores no inician
```bash
docker-compose logs -f
```

### Necesito reinstalar el módulo
```bash
# Eliminar contenedores y volúmenes
docker-compose down -v

# Levantar nuevamente
docker-compose up -d
```

### Cambios en el código no se reflejan
- Reinicia el servicio de Odoo: `docker-compose restart odoo`
- O actualiza el módulo desde la interfaz de Odoo

## 📚 Recursos

- [Documentación oficial de Odoo 18](https://www.odoo.com/documentation/18.0/)
- [Guía de desarrollo de módulos](https://www.odoo.com/documentation/18.0/developer/tutorials.html)

## 👥 Equipo

VitalPet Team

## 📄 Licencia

LGPL-3
