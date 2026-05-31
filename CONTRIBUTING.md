# Guía de Contribución — VitalPet

Gracias por tu interés en contribuir a **VitalPet**. Este documento establece las reglas y flujos de trabajo para que todos los integrantes del equipo colaboren de forma ordenada y efectiva.

---

## Tabla de Contenidos

1. [Código de Conducta](#1-código-de-conducta)
2. [Configuración del Entorno de Desarrollo](#2-configuración-del-entorno-de-desarrollo)
3. [Estructura de Ramas](#3-estructura-de-ramas)
4. [Flujo de Trabajo (Git Flow)](#4-flujo-de-trabajo-git-flow)
5. [Convenciones de Commits](#5-convenciones-de-commits)
6. [Creación de Pull Requests](#6-creación-de-pull-requests)
7. [Revisión de Código](#7-revisión-de-código)
8. [Estándares de Código](#8-estándares-de-código)
9. [Reportar Bugs](#9-reportar-bugs)
10. [Proponer Nuevas Funcionalidades](#10-proponer-nuevas-funcionalidades)

---

## 1. Código de Conducta

Al contribuir a este proyecto, aceptas cumplir con el [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). El respeto, la comunicación constructiva y la colaboración son fundamentales para el equipo.

---

## 2. Configuración del Entorno de Desarrollo

### Requisitos previos

- Docker 20.10+ y Docker Compose 2.0+
- Git 2.30+
- Editor de código (VS Code recomendado)

### Pasos iniciales

```bash
# 1. Hacer fork del repositorio (si eres colaborador externo)
#    O clonar directamente si eres miembro del equipo:
git clone https://github.com/DavidGR21/Proyecto-Odoo.git
cd Proyecto-Odoo

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con los valores de tu entorno local

# 3. Levantar el entorno
docker-compose up -d --build

# 4. Verificar que todo funciona
docker-compose ps
docker-compose logs -f odoo
```

### Configurar Git correctamente

```bash
git config user.name "Tu Nombre"
git config user.email "tu_email@ejemplo.com"
```

---

## 3. Estructura de Ramas

El proyecto usa una adaptación de **Git Flow** con las siguientes ramas:

| Rama | Propósito | Merges desde |
|---|---|---|
| `main` | Código estable en producción. Nunca se hace push directo. | `develop` vía PR |
| `develop` | Rama de integración. Siempre debe estar lista para release. | Feature branches vía PR |
| `feature/<nombre>` | Nuevas funcionalidades. | Propia |
| `fix/<nombre>` | Corrección de bugs. | Propia |
| `hotfix/<nombre>` | Correcciones urgentes en producción. | `main` |
| `docs/<nombre>` | Solo documentación. | Propia |
| `refactor/<nombre>` | Refactorizaciones sin cambio de funcionalidad. | Propia |

### Reglas de ramas

- **Nunca** hacer push directo a `main` o `develop`.
- Los nombres de rama deben ser en minúsculas con guiones: `feature/portal-cliente`, `fix/stock-negativo`.
- Las ramas deben ser de corta duración (máximo una semana para features pequeños).
- Eliminar la rama remota una vez que el PR sea mergeado.

### Crear una nueva rama

```bash
# Siempre partir de develop (o main para hotfixes)
git checkout develop
git pull origin develop
git checkout -b feature/nombre-de-la-funcionalidad
```

---

## 4. Flujo de Trabajo (Git Flow)

```
main ────────────────────────────────────────────────────▶ producción
  ↑                                                     ↑
  │                                                     │
develop ──────────────────────────────────────────────▶ release
  ↑          ↑          ↑          ↑
  │          │          │          │
feature/A  feature/B  fix/C    refactor/D
```

### Proceso completo para un feature

```bash
# 1. Crear rama desde develop
git checkout develop && git pull origin develop
git checkout -b feature/mi-feature

# 2. Desarrollar con commits frecuentes
git add custom_addons/veterinaria_core/models/mi_modelo.py
git commit -m "feat: agregar modelo de turno veterinario"

# 3. Mantener la rama actualizada con develop
git fetch origin
git rebase origin/develop

# 4. Subir la rama
git push origin feature/mi-feature

# 5. Abrir Pull Request hacia develop en GitHub
# 6. Esperar revisión y aprobación
# 7. Hacer merge (Squash and Merge para features, Merge Commit para releases)
# 8. Eliminar la rama tras el merge
git push origin --delete feature/mi-feature
git branch -d feature/mi-feature
```

---

## 5. Convenciones de Commits

Seguimos la especificación **[Conventional Commits](https://www.conventionalcommits.org/)**:

```
<tipo>(<ámbito>): <descripción corta en imperativo>

[cuerpo opcional: explica el QUÉ y el POR QUÉ]

[pie opcional: referencias a issues, breaking changes]
```

### Tipos permitidos

| Tipo | Uso |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Solo documentación |
| `style` | Formato, espacios, punto y coma (sin cambio de lógica) |
| `refactor` | Refactorización sin cambio de comportamiento |
| `test` | Añadir o modificar tests |
| `chore` | Tareas de mantenimiento (dependencias, CI, etc.) |
| `perf` | Mejora de rendimiento |
| `revert` | Revertir un commit anterior |

### Ámbitos sugeridos

`core`, `web`, `sri`, `portal`, `facturacion`, `inventario`, `citas`, `recetas`, `vacunas`, `seguridad`, `docker`, `docs`

### Ejemplos válidos

```bash
feat(citas): agregar validación de conflicto de horario en veterinario
fix(inventario): corregir descuento de stock negativo al cancelar factura
docs(api): documentar endpoints del portal del cliente
chore(docker): actualizar versión de PostgreSQL a 15.4
feat(sri): implementar firma XAdES-BES con certificado .p12
fix(portal): redirigir correctamente cuando factura no pertenece al usuario
```

### Reglas para mensajes de commit

- Usar verbos en imperativo: "agregar", "corregir", "actualizar", no "agregado" ni "se agregó".
- Primera letra en minúscula.
- Sin punto al final de la descripción corta.
- Máximo 72 caracteres en la primera línea.
- Si el commit cierra un issue: `Closes #42` en el pie.

---

## 6. Creación de Pull Requests

### Antes de abrir un PR

- [ ] El código corre sin errores en local (`docker-compose up -d --build`)
- [ ] El módulo se instala/actualiza sin errores en Odoo
- [ ] Se probaron los casos principales en la interfaz
- [ ] El código sigue las convenciones del proyecto (ver sección 8)
- [ ] No se incluyen archivos sensibles (`.env`, `.p12`, contraseñas)

### Estructura del PR

**Título:** Siguiendo Conventional Commits: `feat(módulo): descripción corta`

**Descripción (template):**

```markdown
## Descripción
Breve explicación de qué hace este PR y por qué es necesario.

## Cambios realizados
- [ ] Nuevo modelo `veterinaria.X` con campos Y, Z
- [ ] Vista de lista y formulario para X
- [ ] Seguridad: ACL para grupos Veterinario y Admin

## Cómo probar
1. Instalar/actualizar el módulo `veterinaria_core`
2. Ir a Veterinaria → X
3. Verificar que ...

## Screenshots (si aplica)
[Insertar capturas de pantalla]

## Issues relacionados
Closes #XX
```

### Reglas para PRs

- Un PR = una funcionalidad o un fix. No mezclar cambios no relacionados.
- El PR debe ser revisado por **al menos un** integrante del equipo antes del merge.
- Resolver todos los comentarios de revisión antes de hacer merge.
- Usar **Squash and Merge** para features pequeños, **Merge Commit** para releases.
- No borrar el historial de commits relevante con `--force`.

---

## 7. Revisión de Código

### Responsabilidades del revisor

- Verificar que el código siga los estándares del proyecto.
- Comprobar que no hay vulnerabilidades obvias (SQL injection, XSS, permisos abiertos).
- Sugerir mejoras constructivas, nunca de forma despectiva.
- Aprobar o solicitar cambios con comentarios claros.
- Revisar en un plazo máximo de **48 horas** tras la asignación.

### Responsabilidades del autor

- Responder a todos los comentarios antes de solicitar re-revisión.
- No hacer merge sin al menos una aprobación.
- Si se solicitan cambios, actualizarlos en nuevos commits (no amend en ramas compartidas).

---

## 8. Estándares de Código

### Python (modelos Odoo)

- Seguir [PEP 8](https://pep8.org/) para estilo general.
- Usar 4 espacios de indentación (sin tabs).
- Nombres de variables y métodos en `snake_case`.
- Nombres de clases en `PascalCase`.
- No dejar `print()` ni `pdb` en el código entregado.
- Métodos privados con prefijo `_` (ej: `_calcular_total`).
- Usar `sudo()` solo cuando sea estrictamente necesario y documentar el motivo.

```python
# Correcto
class VeterinariaReceta(models.Model):
    _name = 'veterinaria.receta'

    def _calcular_cantidad_total(self):
        for linea in self:
            linea.cantidad_total = linea.dosis * (24 / linea.frecuencia_horas) * linea.duracion_dias

# Incorrecto
class receta(models.Model):
    def calcularCantidad(self):
        ...
```

### XML (vistas Odoo)

- Indentar con 4 espacios.
- Nombrar IDs de vistas con el patrón: `view_<modelo_sin_puntos>_<tipo>` (ej: `view_veterinaria_receta_form`).
- Usar `<record>` para definir vistas, no `<act_window>` directamente.
- Comentar secciones complejas.

### Seguridad

- Cada modelo nuevo debe tener entradas en `security/ir.model.access.csv` para todos los grupos pertinentes.
- Usar `domain` en campos relacionales para filtrar registros correctamente.
- No usar `sudo()` en controladores del portal sin validar pertenencia del registro al usuario.

---

## 9. Reportar Bugs

Usar el sistema de **Issues de GitHub**:

1. Verificar que el bug no esté ya reportado.
2. Crear un issue con la etiqueta `bug`.
3. Incluir:
   - Descripción clara del problema.
   - Pasos para reproducirlo.
   - Comportamiento esperado vs. observado.
   - Versión de Odoo, Docker, sistema operativo.
   - Logs relevantes (de `docker-compose logs odoo`).
   - Capturas de pantalla si aplica.

---

## 10. Proponer Nuevas Funcionalidades

1. Crear un **Issue** con la etiqueta `enhancement`.
2. Describir la funcionalidad y su valor para el proyecto.
3. Esperar retroalimentación del equipo antes de comenzar a implementar.
4. Una vez aprobada, crear la rama `feature/nombre` y abrir el PR cuando esté lista.

---

## Recursos Útiles

- [Documentación de Odoo 18](https://www.odoo.com/documentation/18.0/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [PEP 8 — Guía de estilo Python](https://pep8.org/)
- [docs/API.md](docs/API.md) — Documentación técnica del proyecto
