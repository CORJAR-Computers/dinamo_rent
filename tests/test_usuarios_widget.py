"""Tests for UsuariosWidget — user administration panel."""

from unittest.mock import patch


from views.usuarios_view import UsuariosWidget, UsuarioFormDialog


# ── Mock data ─────────────────────────────────────────────────────────────────
_MOCK_USUARIOS = [
    {
        "username": "admin",
        "nombre": "Administrador Principal",
        "rol": "Administrador",
        "email": "admin@dinamo.com",
        "activo": 1,
        "ultimo_acceso": "2026-05-25 10:00",
        "debe_cambiar_password": False,
    },
    {
        "username": "oper1",
        "nombre": "Operador Uno",
        "rol": "Operador",
        "email": "oper1@dinamo.com",
        "activo": 1,
        "ultimo_acceso": "",
        "debe_cambiar_password": True,
    },
    {
        "username": "inactivo",
        "nombre": "Usuario Inactivo",
        "rol": "Supervisor",
        "email": "user@dinamo.com",
        "activo": 0,
        "ultimo_acceso": "",
        "debe_cambiar_password": False,
    },
]


@patch("views.usuarios_view.UsuarioService.listar", return_value=_MOCK_USUARIOS)
class TestUsuariosWidget:
    """Suite de pruebas para UsuariosWidget."""

    def test_instancia(self, mock_listar, qapp):
        """UsuariosWidget se instancia correctamente."""
        from tests.helpers import BaseWidgetTestMixin

        widget = UsuariosWidget()
        BaseWidgetTestMixin.check_base_widget(widget)
        assert isinstance(widget, UsuariosWidget)
        widget.deleteLater()

    def test_tiene_banner_y_tabla(self, mock_listar, qapp):
        """El widget tiene buscador, filtro y tabla."""
        widget = UsuariosWidget()
        assert hasattr(widget, "txt_buscar")
        assert hasattr(widget, "cmb_filtro")
        assert hasattr(widget, "tabla")
        widget.deleteLater()

    def test_columnas_tabla(self, mock_listar, qapp):
        """La tabla tiene las columnas esperadas."""
        widget = UsuariosWidget()
        headers = [
            widget.tabla.horizontalHeaderItem(i).text() for i in range(widget.tabla.columnCount())
        ]
        assert "Usuario" in headers
        assert "Nombre Completo" in headers
        assert "Rol" in headers
        assert "Estado" in headers
        widget.deleteLater()

    # ── Carga de datos ─────────────────────────────────────────────────

    def test_cargar_usuarios_pinta_filas(self, mock_listar, qapp):
        """cargar_usuarios() pinta filas en la tabla."""
        widget = UsuariosWidget()
        widget.cargar_usuarios()
        assert widget.tabla.rowCount() == len(_MOCK_USUARIOS)
        mock_listar.assert_called()
        widget.deleteLater()

    def test_cargar_usuarios_muestra_usuernames(self, mock_listar, qapp):
        """Los usernames se muestran correctamente."""
        widget = UsuariosWidget()
        widget.cargar_usuarios()
        assert widget.tabla.item(0, 0).text() == "admin"
        assert widget.tabla.item(1, 0).text() == "oper1"
        widget.deleteLater()

    def test_cargar_usuarios_muestra_estados(self, mock_listar, qapp):
        """Los estados Activo/Inactivo se muestran."""
        widget = UsuariosWidget()
        widget.cargar_usuarios()
        assert "Activo" in widget.tabla.cellWidget(0, 4).text()
        assert "Activo" in widget.tabla.cellWidget(1, 4).text()
        assert "Inactivo" in widget.tabla.cellWidget(2, 4).text()
        widget.deleteLater()

    def test_cargar_usuarios_debe_cambiar(self, mock_listar, qapp):
        """Columna 'Debe Cambiar' muestra indicador cuando aplica."""
        widget = UsuariosWidget()
        widget.cargar_usuarios()
        # usuario 1 (oper1) debe cambiar
        col_debe = 6
        item = widget.tabla.item(1, col_debe)
        assert item is not None
        assert "Sí" in item.text()
        widget.deleteLater()

    def test_cargar_usuarios_vacio(self, mock_listar, qapp):
        """Lista vacía: 0 filas."""
        mock_listar.return_value = []
        widget = UsuariosWidget()
        widget.cargar_usuarios()
        assert widget.tabla.rowCount() == 0
        widget.deleteLater()

    def test_cargar_usuarios_con_error(self, mock_listar, qapp):
        """Cuando el servicio lanza excepción, no crashea."""
        from core.exceptions import DinamoBaseError

        mock_listar.side_effect = DinamoBaseError("Error DB")
        widget = UsuariosWidget()
        widget.cargar_usuarios()  # No debe lanzar
        assert widget.tabla.rowCount() == 0
        widget.deleteLater()

    # ── Filtro ─────────────────────────────────────────────────────────

    def test_filtrar_por_texto(self, mock_listar, qapp):
        """Filtrar por texto reduce resultados."""
        widget = UsuariosWidget()
        widget.cargar_usuarios()
        widget.txt_buscar.setText("admin")
        assert widget.tabla.rowCount() == 1
        assert widget.tabla.item(0, 0).text() == "admin"
        widget.deleteLater()

    def test_filtrar_por_pendiente(self, mock_listar, qapp):
        """Filtro 'Pendiente de cambio' muestra solo usuarios que deben cambiar."""
        widget = UsuariosWidget()
        widget.cargar_usuarios()
        widget.cmb_filtro.setCurrentIndex(1)
        assert widget.tabla.rowCount() == 1
        assert "Sí" in widget.tabla.item(0, 6).text()
        widget.deleteLater()

    def test_filtrar_vacio_restaura(self, mock_listar, qapp):
        """Texto vacío restaura todos los registros."""
        widget = UsuariosWidget()
        widget.cargar_usuarios()
        widget.txt_buscar.setText("Inexistente")
        assert widget.tabla.rowCount() == 0
        widget.txt_buscar.setText("")
        assert widget.tabla.rowCount() == len(_MOCK_USUARIOS)
        widget.deleteLater()


# ── Tests para UsuarioFormDialog ─────────────────────────────────────────────


class TestUsuarioFormDialog:
    """Tests de instanciación del formulario de usuario."""

    def test_instancia_nuevo(self, qapp):
        """UsuarioFormDialog se instancia para nuevo usuario."""
        dlg = UsuarioFormDialog()
        assert dlg is not None
        assert "Usuario" in dlg.windowTitle()
        dlg.deleteLater()

    def test_instancia_editar(self, qapp):
        """UsuarioFormDialog con datos carga valores."""
        dlg = UsuarioFormDialog(
            datos_usuario={
                "username": "admin",
                "nombre": "Admin",
                "rol": "Administrador",
                "activo": 1,
            }
        )
        assert dlg.txt_nombre.text() == "Admin"
        assert dlg.txt_username.text() == "admin"
        # Username debe estar deshabilitado en edición
        assert not dlg.txt_username.isEnabled()
        dlg.deleteLater()
