# INSTRUCCIONES: Corrección de Vistas post-F1B/F1C

## Problema

Durante F1B se reestructuraron los servicios: 3 métodos se eliminaron de `RentaService`
y se movieron a nuevos servicios. Las vistas (views) que llamaban estos métodos
quedaron rotas porque los imports se actualizaron parcialmente o no se migraron
los métodos correspondientes.

**Error reportado:**
```
AttributeError: type object 'DashboardService' has no attribute 'obtener_activas'
```

---

## Cambios de métodos en F1B (Resumen)

| Método original | Servicio original | Nuevo servicio | Nuevo nombre |
|----------------|-------------------|----------------|--------------|
| `RentaService.kpi_globales()` | RentaService | DashboardService | `DashboardService.kpi_globales()` |
| `RentaService.roi_flota()` | RentaService | FinancialService | `FinancialService.roi_flota()` |
| `RentaService.balance_mensual()` | RentaService | InformeService | `InformeService.balance_mensual_real()` |
| `RentaService.obtener_activas()` | RentaService | DashboardService | `DashboardService.obtener_activas()` ← NUEVO |

---

## Paso 1: Reemplazar services/dashboard_service.py

Copiar el archivo `dashboard_service.py` actualizado a tu proyecto. Este archivo ahora
incluye **7 métodos** en vez de solo 1:

| Método | Qué hace |
|--------|----------|
| `kpi_globales()` | KPIs del dashboard (ya existía) |
| `obtener_activas()` | **NUEVO** - Lista de rentas activas (arregla el error) |
| `obtener_alertas()` | **NUEVO** - Todas las alertas (clientes + internas) |
| `obtener_rentas_por_vencer()` | **NUEVO** - Rentas que vencen en 3 días |
| `obtener_documentos_por_vencer()` | **NUEVO** - Docs (SOAT/Tecno) por vencer |
| `obtener_alertas_flota()` | **NUEVO** - Alertas técnicas de flota |
| `obtener_resumen_financiero()` | **NUEVO** - Resumen financiero del mes |

**Acción:**
```
Copiar download/services/dashboard_service.py → G:\Dinamo_Rent\services\dashboard_service.py
```

---

## Paso 2: Actualizar views/dashboard_view.py

La vista del dashboard probablemente tiene llamadas como esta:

### 2a. Búsqueda global en dashboard_view.py

Busca TODAS las llamadas a servicios en `cargar_datos()` y otros métodos.
Reemplaza según esta tabla:

| Buscar (viejo) | Reemplazar con (nuevo) |
|-----------------|----------------------|
| `RentaService.obtener_activas` | `DashboardService.obtener_activas` |
| `RentaService.kpi_globales` | `DashboardService.kpi_globales` |
| `AlertaService.obtener_todas_las_alertas` | `DashboardService.obtener_alertas` (opcional, ambos funcionan) |
| `AlertaRepositorySA.obtener_rentas_por_vencer` | `DashboardService.obtener_rentas_por_vencer` (opcional) |

### 2b. Verificar el import al inicio del archivo

Asegúrate de que el import sea correcto:

```python
# CORRECTO:
from services.dashboard_service import DashboardService

# Si también necesitas otros servicios:
from services.renta_service import RentaService
from services.alerta_service import AlertaService
```

### 2c. Ejemplo de cómo debería quedar cargar_datos()

```python
def cargar_datos(self):
    # Rentas activas (antes: RentaService.obtener_activas)
    rentas = self.ejecutar_seguro(DashboardService.obtener_activas) or []

    # KPIs del dashboard (antes: RentaService.kpi_globales)
    kpis = self.ejecutar_seguro(DashboardService.kpi_globales) or {}

    # Alertas (opcional, puedes seguir usando AlertaService directamente)
    alertas = self.ejecutar_seguro(DashboardService.obtener_alertas) or {}

    # ... resto de la lógica de la vista
```

---

## Paso 3: Actualizar views/informes_view.py

Esta vista probablemente usa los métodos financieros que se movieron.

### 3a. Búsqueda global

| Buscar (viejo) | Reemplazar con (nuevo) |
|-----------------|----------------------|
| `RentaService.roi_flota()` | `FinancialService.roi_flota()` |
| `RentaService.balance_mensual()` | `InformeService.balance_mensual_real()` |

### 3b. Verificar imports

```python
# Agregar estos imports si no están:
from services.financial_service import FinancialService
from services.informe_service import InformeService
```

---

## Paso 4: Búsqueda GLOBAL en TODAS las vistas

Para estar seguro de que no hay más referencias rotas, hacer una búsqueda
global en la carpeta `views/` de tu proyecto:

### Buscar y reemplazar en todos los archivos .py:

1. **Buscar:** `RentaService.kpi_globales`
   **Reemplazar:** `DashboardService.kpi_globales`
   **Agregar import:** `from services.dashboard_service import DashboardService`

2. **Buscar:** `RentaService.roi_flota`
   **Reemplazar:** `FinancialService.roi_flota`
   **Agregar import:** `from services.financial_service import FinancialService`

3. **Buscar:** `RentaService.balance_mensual`
   **Reemplazar:** `InformeService.balance_mensual_real`
   **Agregar import:** `from services.informe_service import InformeService`

4. **Buscar:** `RentaService.obtener_activas`
   **Reemplazar:** `DashboardService.obtener_activas`
   **(el import de DashboardService ya debería estar)**

---

## Paso 5: Limpiar __pycache__

Después de hacer todos los cambios, limpiar la caché de Python:

```bash
# En G:\Dinamo_Rent\ ejecutar:
del /s /q __pycache__
del /s /q *.pyc

# O en PowerShell:
Get-ChildItem -Path . -Filter __pycache__ -Recurse | Remove-Item -Recurse -Force
```

---

## Paso 6: Probar

1. Iniciar la aplicación: `python main_qt.py`
2. Hacer login
3. Verificar que el Dashboard carga sin errores
4. Navegar a Informes → verificar que ROI y Balance funcionan
5. Navegar a Rentas → verificar CRUD funciona
6. Navegar a Alertas → verificar que se muestran correctamente

---

## Checklist de Verificación

- [ ] `services/dashboard_service.py` reemplazado (7 métodos)
- [ ] `dashboard_view.py` actualizado (imports + llamadas)
- [ ] `informes_view.py` actualizado (roi_flota + balance_mensual)
- [ ] Búsqueda global en views/ completada
- [ ] `__pycache__` limpiado
- [ ] Aplicación inicia sin errores en Dashboard
- [ ] Informes → ROI funciona
- [ ] Informes → Balance mensual funciona
