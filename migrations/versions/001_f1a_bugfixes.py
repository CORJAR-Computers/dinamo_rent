"""F1A Bugfixes - Integridad referencial y campos faltantes

Revision ID: 001_f1a
Revises:
Create Date: 2026-04-13

Changes:
  1. Fix Renta.__table_args__ (collate + indexes unificados) - requiere recrear tabla
  2. FK: Renta.id_reserva -> reservas.id (SET NULL)
  3. FK: Reserva.placa_asignada -> autos.placa (SET NULL)
  4. FK: Comparendo.id_renta -> rentas.id (SET NULL) - ya existe como FK
  5. FK: Comparendo.id_cliente -> clientes.id (SET NULL) - ya existe como FK
  6. Campo nuevo: gastos.placa -> autos.placa (SET NULL)
  7. Campo nuevo: clientes.updated_at (DATETIME, default NOW)
  8. Campo nuevo: reservas.updated_at (DATETIME, default NOW)
  9. Campo nuevo: mantenimiento_vehiculos.updated_at (DATETIME, default NOW)
  10. Campo nuevo: comparendos.updated_at (DATETIME, default NOW)
  11. Campo nuevo: pagos.updated_at (DATETIME, default NOW)
  12. Campo nuevo: gastos.updated_at (DATETIME, default NOW)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "001_f1a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Agregar campo placa a gastos (FK hacia autos)
    op.add_column("gastos", sa.Column("placa", sa.String(20), nullable=True))
    op.create_index("ix_gastos_placa", "gastos", ["placa"])

    # 2. Agregar FK: gastos.placa -> autos.placa
    op.create_foreign_key(
        "fk_gastos_placa_autos",
        "gastos",
        "autos",
        ["placa"],
        ["placa"],
        ondelete="SET NULL",
    )

    # 3. Agregar FK: rentas.id_reserva -> reservas.id
    #    (solo si no existe ya la constraint)
    op.create_foreign_key(
        "fk_rentas_id_reserva_reservas",
        "rentas",
        "reservas",
        ["id_reserva"],
        ["id"],
        ondelete="SET NULL",
    )

    # 4. Agregar FK: reservas.placa_asignada -> autos.placa
    op.create_foreign_key(
        "fk_reservas_placa_asignada_autos",
        "reservas",
        "autos",
        ["placa_asignada"],
        ["placa"],
        ondelete="SET NULL",
    )

    # 5. Agregar updated_at a tablas que no lo tienen
    op.add_column(
        "clientes",
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "reservas",
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "mantenimiento_vehiculos",
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "comparendos",
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "pagos",
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "gastos",
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    # 5. Remover updated_at
    op.drop_column("gastos", "updated_at")
    op.drop_column("pagos", "updated_at")
    op.drop_column("comparendos", "updated_at")
    op.drop_column("mantenimiento_vehiculos", "updated_at")
    op.drop_column("reservas", "updated_at")
    op.drop_column("clientes", "updated_at")

    # 4. Remover FKs
    op.drop_constraint("fk_reservas_placa_asignada_autos", "reservas", type_="foreignkey")
    op.drop_constraint("fk_rentas_id_reserva_reservas", "rentas", type_="foreignkey")
    op.drop_constraint("fk_gastos_placa_autos", "gastos", type_="foreignkey")

    # 3. Remover campo placa de gastos
    op.drop_index("ix_gastos_placa", "gastos")
    op.drop_column("gastos", "placa")
