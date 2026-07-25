# F1B — Instrucciones de Aplicación
## Dinamo Rent ERP — Reestructuración de Services

---

## Resumen de Cambios

Se separaron 2 archivos monolíticos en **16 archivos individuales** + 2 wrappers de compatibilidad.

### ANTES (2 archivos):
```
services/
├── services.py          (486 líneas, 5 servicios)
└── services_extra.py    (535 líneas, 9 servicios)
```

### DESPUÉS (18 archivos):
```
services/
├── __init__.py              ← Importación centralizada
├── services.py              ← Wrapper (re-exporta, 100% compatible)
├── services_extra.py        ← Wrapper (re-exporta, 100% compatible)
├── auto_service.py          ← AutoService
├── cliente_service.py       ← ClienteService
├── renta_service.py         ← RentaService (solo CRUD, sin lógica financiera)
├── auth_service.py          ← AuthService
├── backup_service.py        ← BackupService
├── reserva_service.py       ← ReservaService
├── mantenimiento_service.py ← MantenimientoService
├── usuario_service.py       ← UsuarioService
├── inspeccion_service.py    ← InspeccionService
├── comparendo_service.py    ← ComparendoService
├── pago_service.py          ← PagoService
├── gasto_service.py         ← GastoService
├── alerta_service.py        ← AlertaService
├── informe_service.py       ← InformeService
├── financial_service.py     ← NUEVO: Cálculos, ROI (CORREGIDO)
└── dashboard_service.py     ← NUEVO: KPIs del dashboard
```

### Cambios en Repositorios:
- `InformeRepositorySA`: 3 métodos nuevos para ROI
  - `obtener_ingresos_por_vehiculo()` → dict {placa: total}
  - `obtener_mantenimiento_por_vehiculo()` → dict {placa: total}
  - `obtener_gastos_por_vehiculo()` → dict {placa: total}

---

## ⚠️ CAMBIOS QUE PUEDEN ROMPER VISTAS

### 1. RentaService ya NO tiene estos métodos:

| Método eliminado | Dónde usarlo ahora |
|-----------------|-------------------|
| `RentaService.balance_mensual()` | `InformeService.balance_mensual_real()` |
| `RentaService.roi_flota()` | `FinancialService.roi_flota()` |
| `RentaService.kpi_globales()` | `DashboardService.kpi_globales()` |
| `RentaService._calcular_total()` | `FinancialService.calcular_total_renta()` |
| `RentaService._calcular_total_cierre()` | `FinancialService.calcular_total_cierre()` |

### 2. Las vistas que usen estos métodos necesitan actualizar sus imports:

```python
# ANTES:
from services.services import RentaService

balance = RentaService.balance_mensual()  # ← YA NO EXISTE
roi = RentaService.roi_flota()  # ← YA NO EXISTE
kpi = RentaService.kpi_globales()  # ← YA NO EXISTE

# DESPUÉS:
from services import InformeService, FinancialService, DashboardService

balance = InformeService.balance_mensual_real()
roi = FinancialService.roi_flota()
kpi = DashboardService.kpi_globales()
```

---

## PASO 1 — Backup

```bash
# Ya deberías tener git, así que:
cd G:\Dinamo_Rent
git add .
git commit -m "Estado antes de F1B"
```

---

## PASO 2 — Copiar Archivos

Copia TODOS los archivos de `services/` al proyecto:

| Origen (download/services/) | Destino |
|-----------------------------|---------|
| Todos los archivos `.py` | `G:\Dinamo_Rent\services\` |

También actualiza:
| Archivo | Destino |
|---------|---------|
| `repositories/repositories_sa.py` | `G:\Dinamo_Rent\repositories\repositories_sa.py` |

---

## PASO 3 — Actualizar Imports en Vistas

Busca en tus vistas dónde se usan los métodos eliminados y actualiza:

### En `views/dashboard_view.py`:
```python
# Buscar: RentaService.kpi_globales()
# Reemplazar por: DashboardService.kpi_globales()
from services.dashboard_service import DashboardService
```

### En `views/informes_view.py`:
```python
# Buscar: RentaService.roi_flota()
# Reemplazar por: FinancialService.roi_flota()
from services.financial_service import FinancialService

# Buscar: RentaService.balance_mensual()
# Reemplazar por: InformeService.balance_mensual_real()
from services.informe_service import InformeService
```

### En `main_qt.py`:
Los imports actuales (`from services.services import AuthService, BackupService`) siguen funcionando porque `services.py` es ahora un wrapper.

---

## PASO 4 — Limpiar y Probar

```bash
# Limpiar cache
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# Ejecutar
python main_qt.py
```

Verificar:
1. ✅ Login funciona
2. ✅ Dashboard carga sin error
3. ✅ Informes → ROI muestra datos reales (no ceros)
4. ✅ Rentas → Crear y cerrar funciona
5. ✅ Pagos, Gastos, Reservas funcionan

---

## PASO 5 — Commit

```bash
git add .
git commit -m "F1B: Reestructuración de Services - 16 archivos individuales"
```

---

## Próximo Paso: F1C — Reestructuración de Repositories

Cuando F1B esté funcionando, continuamos con:
- Separar cada Repository en su propio archivo
- Eliminar `get_session_legacy()` si no se usa
