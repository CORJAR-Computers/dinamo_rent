# Mejoras UI — Sistema Dinamo Pro
> Documentación de cambios de diseño aplicados a `clientes_view.py`, `dashboard_view.py` y `calendario_view.py`

---

## Paleta de colores global

Todos los módulos comparten una paleta centralizada definida como constantes privadas al inicio de cada archivo. Esto garantiza coherencia visual sin depender de variables externas.

| Constante     | Valor       | Uso                                      |
|---------------|-------------|------------------------------------------|
| `_NAV`        | `#1a3558`   | Navy profundo — headers, títulos, texto principal destacado |
| `_BLUE`       | `#2563eb`   | Azul activo — acentos, bordes de foco, indicadores |
| `_BG`         | `#f1f5f9`   | Fondo gris suave — cuerpo de vistas      |
| `_SURF`       | `#ffffff`   | Superficie blanca — cards, paneles       |
| `_BORD`       | `#cbd5e1`   | Gris perla — bordes de cards y separadores |
| `_TEXT`       | `#1e293b`   | Texto principal                          |
| `_MUTED`      | `#64748b`   | Texto secundario / labels                |
| `_CLR_REQMARK`| `#dc2626`   | Rojo — asterisco de campos obligatorios  |

El gradiente institucional `navy → azul` se aplica así:

```python
background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 #1a3558, stop:1 #2563eb);
```

---

## `clientes_view.py` — Diálogo `ClienteFormDialog`

### Banner de encabezado

Se reemplazó el título plano `QLabel` por un banner de altura fija (`78px`) con gradiente horizontal navy→azul. Incluye:

- **Avatar circular** de 48×48px con fondo `rgba(255,255,255,0.18)` y ícono 👤.
- **Título dinámico**: muestra `"Nuevo Cliente"` o `"Editar Cliente"` con el nombre del registro.
- **Subtítulo**: descripción contextual en blanco semitransparente `rgba(255,255,255,0.78)`.

```python
def _build_header(self, is_edit: bool, datos) -> QWidget:
    header = QWidget()
    header.setObjectName("dlg_header")
    header.setFixedHeight(78)
    ...
```

### Sistema de cards (`_make_card`)

Cada card tiene:

- Borde izquierdo de acento de **4px** en `#2563eb`.
- Borde exterior `1px solid #cbd5e1` con radio de `8px`.
- Encabezado interno con **ícono emoji** en badge `#eff6ff` + título bold en navy.
- Separador `HLine` de 1px entre encabezado y campos.
- `setColumnStretch(0, 0)` / `setColumnStretch(1, 1)` para que los inputs siempre se expandan y los placeholders nunca se trunquen.

```python
def _make_card(title: str, parent, icon: str = "") -> tuple[QFrame, QGridLayout]:
    ...
    layout.setColumnStretch(0, 0)   # etiquetas: ancho fijo
    layout.setColumnStretch(1, 1)   # inputs: se expanden
```

### Labels con campo obligatorio

La función `_make_label` acepta `required=True` para insertar un asterisco rojo `#dc2626` mediante HTML inline, en lugar del texto literal `(*)`.

```python
def _make_label(text: str, required: bool = False) -> QLabel:
    if required:
        lbl.setText(
            f'<span style="color:{_CLR_TEXT};">{text}</span>'
            f' <span style="color:{_CLR_REQMARK}; font-weight:700;">*</span>'
        )
```

### Pestañas (QTabWidget)

- Indicador de tab activa: **línea inferior de 3px** en `#2563eb`, sin caja ni borde visible.
- Tabs con íconos: `"👤   Datos Personales"` y `"🚗   Licencia / Ubicación / Estado"`.
- Hover con línea inferior en `#94a3b8` para feedback visual.

### Scroll en pestañas

Cada pestaña envuelve su contenido en un `QScrollArea` para que los cards inferiores nunca queden cortados al redimensionar el diálogo.

```python
scroll = QScrollArea(tab)
scroll.setWidgetResizable(True)
scroll.setFrameShape(QFrame.Shape.NoFrame)
scroll.setStyleSheet("QScrollArea { background: transparent; border: none; } ...")
```

### Barra de botones

- Separador `HLine` antes de los botones.
- Leyenda de campos obligatorios con asterisco rojo a la izquierda.
- Botones `Cancelar` y `💾 Guardar Ficha` alineados a la derecha.

### Cards por pestaña

**Pestaña 1 — Datos Personales**

| Card           | Ícono | Campos                                      |
|----------------|-------|---------------------------------------------|
| Documentación  | 🪪    | Tipo de Documento, No. Documento *          |
| Contacto       | 📞    | Celular Principal, Celular Secundario, Email |
| Nombres        | ✍️   | Nombres *, Apellidos                        |
| Ubicación      | 🌍    | Nacionalidad, País Origen, Estado/Región, Ciudad |

**Pestaña 2 — Licencia / Ubicación / Estado**

| Card                   | Ícono | Campos                                    |
|------------------------|-------|-------------------------------------------|
| Licencia de Conducción | 🪪    | No. Licencia, Categoría/Tipo, Vencimiento |
| Estado del Cliente     | 🏷️   | Estado                                    |
| Dirección              | 📍    | Residencia, Temporal                      |
| Hospedaje              | 🏨    | Hotel/Hospedaje, No. Habitación           |

---

## `dashboard_view.py` — `DashboardWidget`

### Arquitectura de layout

Se migró de un `QVBoxLayout` con márgenes planos a una estructura de dos zonas:

1. **Banner** (`QWidget` fijo de 64px) con gradiente navy→azul.
2. **Área de contenido** (`QWidget` con fondo `#f1f5f9`) que crece con `stretch=1`.

```python
main_layout.setContentsMargins(0, 0, 0, 0)  # sin márgenes en el root
```

### Banner superior

- Ícono 📊 en círculo `rgba(255,255,255,0.15)`.
- Título `"Tablero de Operaciones"` + subtítulo en blanco semitransparente.
- Botón `"↻  Actualizar"` en estilo vidrio esmerilado (border rgba blanco).

### `_KpiCard` rediseñada

Cada tarjeta KPI ahora tiene tres zonas:

1. **Banda superior de 6px** — gradiente horizontal del color semántico del KPI.
2. **Columna izquierda** — título en mayúsculas muted + valor numérico grande (`30pt`, bold, tracking negativo).
3. **Ícono decorativo derecho** — círculo de 44px con fondo semitransparente del color del KPI.

```python
_KpiCard("Disponibles",     "🟢", COLOR_EXITO,   "#22c55e")
_KpiCard("Rentas Activas",  "🚗", COLOR_PRIMARIO, "#2563eb")
_KpiCard("En Taller",       "🔧", COLOR_ALERTA,  "#f59e0b")
_KpiCard("Alertas Críticas","⚠️", COLOR_PELIGRO, "#ef4444")
```

### `_section_header()` — helper de encabezados

Reemplaza los `QLabel` planos con `styles.lbl_section`. Genera un widget con:

- Barra vertical de 4px con gradiente azul→navy.
- Ícono opcional.
- Texto en navy bold con letter-spacing.

```python
lay_al.addWidget(_section_header("Alertas de Flota y Vencimientos", "🔔"))
lay_r.addWidget(_section_header("Rentas Activas", "📋"))
```

### `_apply_table_style()` — helper de tablas

Extiende `styles.table_widget()` con:

- Headers con gradiente navy (`#1a3558` → `#1e3f6e`), texto blanco bold.
- Fondo alterno en `#f8fafc`.
- Bordes redondeados de `6px` en el widget completo.
- Separador de grid en `#e2e8f0`.

---

## `calendario_view.py` — `CalendarioWidget`

### Arquitectura de layout

Misma estructura de dos zonas que el dashboard:

1. **Banner** de 64px con gradiente y texto descriptivo.
2. **Área de contenido** con padding interno de `20/16px`.

### Banner superior

- Ícono 📅 en círculo `rgba(255,255,255,0.15)`.
- Título `"Calendario de Disponibilidad"` + subtítulo `"Vista mensual de la flota"`.

### Barra de navegación (card blanca)

Se reemplazaron los botones `btn_default` genéricos por una **card blanca** (`border-radius: 10px`) que contiene:

- Botones `"◀ Anterior"` / `"Siguiente ▶"` / `"↻ Actualizar"` con hover azul y border dinámico.
- Label del mes en `13pt`, bold, color navy, centrado con `addStretch()` a ambos lados.

```python
nav_card = QFrame()
nav_card.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px;")
```

### Leyenda como pills

Se reemplazaron los `QLabel` con funciones de estilo externas por **badges pill** auto-contenidos, cada uno con fondo semitransparente del color del estado y borde del mismo tono:

```python
pill.setStyleSheet(f"""
    background: {color}33;
    border: 1px solid {color};
    border-radius: 12px;
    padding: 4px 12px;
""")
```

Se añadió una pill adicional para **fin de semana** en gris neutro.

### Tabla del calendario

- Headers en gradiente navy (coherente con el dashboard).
- Columna vehículo: texto bold en navy con placa + marca/modelo.
- Ancho de celdas de días reducido a `44px` para mejor densidad.
- Altura de fila fija en `42px`.
- **Día actual** resaltado con fondo `#dbeafe` y marcador `●` en azul `#2563eb`.
- Fines de semana con fuente bold (sin cambio de color para no chocar con los colores de estado).

```python
if fecha_dia == hoy:
    item.setBackground(color_hoy_bg)
    item.setText("●")
    item.setForeground(QColor(_BLUE))
```

### Constante de meses

Se eliminó la lista local dentro de `cargar_calendario()` y se migró a una constante de clase:

```python
class CalendarioWidget(BaseWidget):
    _MESES = ["Enero", "Febrero", ..., "Diciembre"]
```

---

## Eliminaciones y limpiezas

| Elemento eliminado                      | Razón                                                    |
|-----------------------------------------|----------------------------------------------------------|
| `dialog_title` de imports               | Reemplazado por banner de gradiente                      |
| `lbl_section` de imports (clientes)     | Reemplazado por `_make_card` con encabezado propio       |
| `legend_available/rented/reserved`      | Reemplazados por pills auto-contenidos en calendario     |
| `lbl_subtitle` de imports (calendario)  | Reemplazado por label estilizado dentro del nav_card     |
| Lista `meses` local en `cargar_calendario` | Migrada a `_MESES` como constante de clase            |
| Márgenes `25px` planos en dashboard     | Reemplazados por zona banner + zona contenido            |

---

## Convenciones adoptadas

- Todas las constantes de color se declaran al inicio del módulo con prefijo `_`.
- Los helpers de UI (`_make_card`, `_section_header`, `_apply_table_style`) son funciones libres, no métodos, para facilitar su reutilización.
- El gradiente institucional `navy → azul` se usa exclusivamente en elementos de alto nivel: banners de módulo, headers de tabla, bandas de KPI.
- El gradiente vertical `azul → navy` se usa para elementos de acento secundario: barras laterales de sección, barra de `_section_header`.
- Los campos obligatorios se marcan **solo con asterisco HTML** (`required=True`), nunca con texto como `"(*)"`.
