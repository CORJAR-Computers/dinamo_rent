# F1A — Instrucciones de Aplicación
## Dinamo Rent ERP — Bug Fixes Críticos

---

## Resumen de Cambios

| # | Cambio | Archivo | Riesgo |
|---|--------|---------|--------|
| 1 | Fix `__table_args__` duplicado en Renta | `core/models.py` | Bajo |
| 2 | `back_populates` Comparendo → Renta/Cliente | `core/models.py` | Bajo |
| 3 | FK `id_reserva` en Renta → Reserva | `core/models.py` + migración | Medio |
| 4 | FK `placa_asignada` en Reserva → Auto | `core/models.py` + migración | Medio |
| 5 | Campo `placa` en Gasto → Auto | `core/models.py` + migración + schemas + repo + service | Medio |
| 6 | `updated_at` en 6 tablas | `core/models.py` + migración | Bajo |
| 7 | `.gitignore` | Nuevo archivo | Ninguno |

---

## PASO 1 — Backup OBLIGATORIO

Antes de tocar nada, haz un backup de tu base de datos MySQL:

```bash
# Desde XAMPP Shell o CMD
mysqldump -u root dinamo_rent > backup_pre_f1a.sql
```

Y también copia tu carpeta del proyecto completa como respaldo:

```bash
xcopy /E /I "G:\Dinamo_Rent" "G:\Dinamo_Rent_backup_pre_f1a"
```

---

## PASO 2 — Copiar Archivos Modificados

Reemplaza estos archivos en tu proyecto con los archivos generados:

| Archivo Origen (download/) | Destino en tu proyecto |
|----------------------------|------------------------|
| `core/models.py` | `G:\Dinamo_Rent\core\models.py` |
| `core/schemas.py` | `G:\Dinamo_Rent\core\schemas.py` |
| `repositories/repositories_sa.py` | `G:\Dinamo_Rent\repositories\repositories_sa.py` |
| `services/services_extra.py` | `G:\Dinamo_Rent\services\services_extra.py` |
| `.gitignore` | `G:\Dinamo_Rent\.gitignore` |
| `migrations/versions/001_f1a_bugfixes.py` | `G:\Dinamo_Rent\migrations\versions\001_f1a_bugfixes.py` |

---

## PASO 3 — Limpiar __pycache__

Elimina TODOS los directorios `__pycache__` para evitar que Python use código viejo compilado:

```bash
# Desde PowerShell en G:\Dinamo_Rent
Get-ChildItem -Path . -Directory -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
```

---

## PASO 4 — Ejecutar Migración Alembic

Si NUNCA has usado Alembic antes (tu `migrations/versions/` estaba vacío):

```bash
# Opción A: Marcar la BD actual como "ya migrada" (NO ejecuta cambios, solo marca)
alembic stamp head

# Luego aplicar la migración F1A:
alembic upgrade head
```

Si prefieres NO usar Alembic y aplicar los cambios manualmente en MySQL:

```sql
-- 1. Agregar campo placa a gastos
ALTER TABLE gastos ADD COLUMN placa VARCHAR(20) NULL AFTER id;
CREATE INDEX ix_gastos_placa ON gastos (placa);
ALTER TABLE gastos ADD CONSTRAINT fk_gastos_placa_autos
    FOREIGN KEY (placa) REFERENCES autos(placa) ON DELETE SET NULL;

-- 2. Agregar FK id_reserva -> reservas
ALTER TABLE rentas ADD CONSTRAINT fk_rentas_id_reserva_reservas
    FOREIGN KEY (id_reserva) REFERENCES reservas(id) ON DELETE SET NULL;

-- 3. Agregar FK placa_asignada -> autos
ALTER TABLE reservas ADD CONSTRAINT fk_reservas_placa_asignada_autos
    FOREIGN KEY (placa_asignada) REFERENCES autos(placa) ON DELETE SET NULL;

-- 4. Agregar updated_at a tablas que no lo tienen
ALTER TABLE clientes ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE reservas ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE mantenimiento_vehiculos ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE comparendos ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE pagos ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE gastos ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
```

---

## PASO 5 — Inicializar Git (si no lo tienes)

```bash
cd G:\Dinamo_Rent
git init
git add .
git commit -m "F1A: Bug fixes criticos - integridad referencial y campos faltantes"
```

---

## PASO 6 — Verificar que todo funciona

1. Arranca la aplicación: `python main_qt.py`
2. Verifica el login
3. Crea un gasto nuevo — deberías ver el campo "Placa del Vehículo" (opcional)
4. Crea una reserva con placa asignada — verifica que se vincula al auto
5. Revisa un comparendo — debería mostrar la renta y cliente vinculados

---

## Notas Importantes

### Sobre la FK de Comparendos
Las FKs `comparendos.id_renta` y `comparendos.id_cliente` YA EXISTÍAN en tu modelo, pero no tenían `back_populates`. Esto significa que:
- La BD ya tenía las columnas con FK
- Solo agregamos las relaciones ORM (no cambia la BD)
- Ahora desde una Renta puedes ver sus comparendos: `renta.comparendos`
- Ahora desde un Cliente puedes ver sus comparendos: `cliente.comparendos`

### Sobre gastos.placa
El campo `placa` en gastos es **OPCIONAL** (nullable=True). Los gastos existentes tendrán `placa=NULL`. Los nuevos gastos podrán vincularse a un vehículo específico. Esto permite:
- Reportes de rentabilidad por vehículo
- Ver todos los gastos de un auto en particular
- Gastos generales (sin vehículo) siguen funcionando

### Sobre el __table_args__ de Renta
Antes tenías DOS definiciones de `__table_args__` en la clase Renta:
```python
__table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}  # Se PERDÍA
__table_args__ = (Index(...), Index(...))                   # Esta ganaba
```
Ahora están combinadas correctamente:
```python
__table_args__ = (
    Index(...), Index(...),
    {'mysql_collate': 'utf8mb4_unicode_ci'},
)
```

---

## Próximo Paso: F1B — Reestructuración de Services

Una vez que F1A esté funcionando, continuamos con:
- Separar cada Service en su propio archivo
- Extraer FinancialService (cálculos, balances, ROI)
- Crear DashboardService (KPIs)
- Reparar roi_flota() que devuelve ceros
