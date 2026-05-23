from views.components import ModernMessageBox
"""
views/usuarios_view.py — Vista para la Administracion de Usuarios.
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QLineEdit, QDialog,
    QFormLayout, QComboBox, QGroupBox, QWidget,
    QAbstractItemView, QMenu,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QFont

from core.config import COLOR_EXITO, COLOR_PELIGRO
from services.backup_service import BackupService
from services.usuario_service import UsuarioService
from core.exceptions import DinamoBaseError
from views.base_widget import BaseWidget
from views.styles import btn_danger, btn_primary, btn_success, btn_warning, edit_search, group_box, input_field, input_combo, dialog_background, dialog_title

# ── Paleta coherente con el sistema Dinamo Pro ────────────────────────
_NAV   = "#1a3558"
_BLUE  = "#2563eb"
_BG    = "#f1f5f9"
_SURF  = "#ffffff"
_BORD  = "#cbd5e1"
_TEXT  = "#1e293b"
_MUTED = "#64748b"


# =============================================================================
# DIALOGO CREAR/EDITAR USUARIO
# =============================================================================
class UsuarioFormDialog(QDialog):
    """Dialogo para crear o editar un usuario."""

    def __init__(self, parent=None, datos_usuario=None, session_id: str = None):
        super().__init__(parent)
        self.setWindowTitle("Gestion de Usuario")
        self.setMinimumSize(450, 500)
        dialog_background(self)
        self.datos_usuario = datos_usuario or {}
        self._session_id = session_id

        self._setup_ui()
        if self.datos_usuario:
            self._cargar_datos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Titulo
        titulo = QLabel(
            "Editar Usuario" if self.datos_usuario else "Nuevo Usuario"
        )
        dialog_title(titulo)
        layout.addWidget(titulo)

        # Formulario
        form_layout = QFormLayout()

        self.txt_nombre = QLineEdit(); input_field(self.txt_nombre)
        self.txt_username = QLineEdit(); input_field(self.txt_username)
        self.txt_email = QLineEdit(); input_field(self.txt_email)

        self.cmb_rol = QComboBox(); input_combo(self.cmb_rol)
        self.cmb_rol.addItems(["Administrador", "Operador", "Supervisor", "Mecanico"])

        self.cmb_estado = QComboBox(); input_combo(self.cmb_estado)
        self.cmb_estado.addItems(["Activo", "Inactivo"])

        form_layout.addRow("Nombre Completo:", self.txt_nombre)
        form_layout.addRow("Usuario (Login):", self.txt_username)
        form_layout.addRow("Email:", self.txt_email)
        form_layout.addRow("Rol / Perfil:", self.cmb_rol)
        form_layout.addRow("Estado:", self.cmb_estado)
        layout.addLayout(form_layout)

        # Seccion contrasena
        group_pass = QGroupBox("Seguridad")
        group_box(group_pass)
        lay_pass = QFormLayout()

        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setPlaceholderText(
            "Dejar vacio para no cambiar" if self.datos_usuario else "Nueva contrasena"
        )
        input_field(self.txt_pass)

        self.txt_confirm = QLineEdit()
        self.txt_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_confirm.setPlaceholderText("Repetir contrasena")
        input_field(self.txt_confirm)

        lay_pass.addRow("Contrasena:", self.txt_pass)
        lay_pass.addRow("Confirmar:", self.txt_confirm)
        group_pass.setLayout(lay_pass)
        layout.addWidget(group_pass)

        # Botones
        btn_layout = QHBoxLayout()

        btn_cancel = QPushButton("Cancelar")
        btn_danger(btn_cancel)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Guardar Usuario")
        btn_primary(btn_save)
        btn_save.clicked.connect(self._guardar)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _cargar_datos(self):
        d = self.datos_usuario
        self.txt_nombre.setText(str(d.get("nombre", "")))
        self.txt_username.setText(str(d.get("username", "")))
        self.txt_username.setEnabled(False)  # Username no se cambia
        self.txt_email.setText(str(d.get("email", "")))
        self.cmb_rol.setCurrentText(str(d.get("rol", "Operador")))

        activo = d.get("activo", 1)
        self.cmb_estado.setCurrentIndex(0 if activo == 1 else 1)

    def _guardar(self):
        pwd = self.txt_pass.text()
        pwd2 = self.txt_confirm.text()

        if pwd and pwd != pwd2:
            ModernMessageBox.warning(self, "Validacion", "Las contrasenas no coinciden.")
            self.txt_confirm.setFocus()
            return

        if not self.datos_usuario and not pwd:
            ModernMessageBox.warning(
                self, "Validacion", "La contrasena es obligatoria para nuevos usuarios."
            )
            self.txt_pass.setFocus()
            return

        estado = 1 if self.cmb_estado.currentIndex() == 0 else 0

        datos = {
            "username": self.txt_username.text().strip(),
            "nombre": self.txt_nombre.text().strip(),
            "rol": self.cmb_rol.currentText(),
            "email": self.txt_email.text().strip(),
            "activo": estado,
            "password_raw": pwd,  # El servicio se encarga de hashear
        }

        try:
            if self.datos_usuario:
                UsuarioService.actualizar(datos, session_id=self._session_id)
            else:
                UsuarioService.crear(datos, session_id=self._session_id)

            ModernMessageBox.success(self, "Exito", "Usuario guardado correctamente.")
            self.accept()
        except DinamoBaseError as e:
            ModernMessageBox.error(self, "Error", str(e))


# =============================================================================
# WIDGET PRINCIPAL DE USUARIOS
# =============================================================================
class UsuariosWidget(BaseWidget):
    """Panel de Administracion de Usuarios."""

    def __init__(self, session_id: str = None):
        super().__init__(session_id=session_id)
        self.setStyleSheet(f"QWidget {{ background: {_BG}; }} QLabel {{ color: {_TEXT}; }}")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Banner superior ──────────────────────────────────────────
        from views.layouts.form_helpers import create_banner
        banner = create_banner("👤", "Administracion de Usuarios", "Gestion de usuarios y permisos del sistema", self.cargar_usuarios)
        main_layout.addWidget(banner)

        # ── Área de contenido ─────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {_BG}; }}")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(14)
        main_layout.addWidget(content, stretch=1)

        # ── Barra de busqueda ────────────────────────────────────────
        top = QHBoxLayout()

        self.txt_buscar = QLineEdit()
        edit_search(self.txt_buscar)
        self.txt_buscar.setPlaceholderText("Buscar usuario...")
        self.txt_buscar.setMinimumWidth(250)
        self.txt_buscar.textChanged.connect(self._filtrar)
        top.addWidget(self.txt_buscar)

        btn_new = QPushButton("+ Crear Usuario")
        btn_success(btn_new)
        btn_new.clicked.connect(self._nuevo_usuario)
        top.addWidget(btn_new)

        btn_backup = QPushButton("Crear Backup Manual")
        btn_warning(btn_backup)
        btn_backup.clicked.connect(self._hacer_backup)
        top.addWidget(btn_backup)

        c_lay.addLayout(top)

        # ── Tabla ────────────────────────────────────────────────────
        self.tabla = QTableWidget()
        self.tabla.setAlternatingRowColors(True)
        self._configurar_tabla()
        c_lay.addWidget(self.tabla)

        self._lista: list[dict] = []
        self.cargar_usuarios()

    def _configurar_tabla(self):
        cols = ["Usuario", "Nombre Completo", "Rol", "Email", "Estado", "Ultimo Acceso"]
        self.tabla.setColumnCount(len(cols))
        self.tabla.setHorizontalHeaderLabels(cols)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.cellDoubleClicked.connect(self._editar_usuario)
        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self._mostrar_menu)

    # ── Carga de datos ─────────────────────────────────────────

    def cargar_usuarios(self):
        self.tabla.setRowCount(0)
        self._lista = []

        try:
            usuarios = UsuarioService.listar(session_id=self._session_id)
            self._lista = usuarios
            self._pintar_filas(usuarios)
        except DinamoBaseError as e:
            self.mostrar_error(f"No se pudieron cargar los usuarios:\n{e}")

    def _pintar_filas(self, usuarios: list[dict]):
        self.tabla.setRowCount(0)
        for i, u in enumerate(usuarios):
            self.tabla.insertRow(i)

            estado = "Activo" if u.get("activo") == 1 else "Inactivo"
            display_name = u.get("nombre") or ""

            items = [
                u.get("username", ""),
                display_name,
                u.get("rol", ""),
                u.get("email", ""),
                estado,
                u.get("ultimo_acceso", "") or "Nunca",
            ]

            for j, val in enumerate(items):
                it = QTableWidgetItem(str(val))
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if j == 4:  # Columna de Estado
                    color = COLOR_EXITO if estado == "Activo" else COLOR_PELIGRO
                    it.setForeground(QBrush(QColor(color)))
                    fnt = QFont(it.font())
                    fnt.setBold(True)
                    it.setFont(fnt)

                self.tabla.setItem(i, j, it)

    # ── Filtro ─────────────────────────────────────────────────

    def _filtrar(self):
        txt = self.txt_buscar.text().lower()
        if not txt:
            self._pintar_filas(self._lista)
            return
        filtrados = [
            u for u in self._lista
            if txt in str(u.get("username", "")).lower()
            or txt in str(u.get("nombre", "")).lower()
            or txt in str(u.get("email", "")).lower()
            or txt in str(u.get("rol", "")).lower()
        ]
        self._pintar_filas(filtrados)

    # ── Acciones ───────────────────────────────────────────────

    def _nuevo_usuario(self):
        dlg = UsuarioFormDialog(self, session_id=self._session_id)
        if dlg.exec():
            self.cargar_usuarios()

    def _editar_usuario(self, row, col):
        if row >= len(self._lista):
            return
        datos = self._lista[row]
        dlg = UsuarioFormDialog(self, datos, session_id=self._session_id)
        if dlg.exec():
            self.cargar_usuarios()

    def _mostrar_menu(self, pos):
        item = self.tabla.itemAt(pos)
        if not item:
            return

        row = item.row()
        if row >= len(self._lista):
            return
        username = self._lista[row].get("username", "")

        menu = QMenu(self)
        ac_edit = menu.addAction("Editar usuario")
        ac_del = menu.addAction("Eliminar usuario")

        acc = menu.exec(self.tabla.viewport().mapToGlobal(pos))
        if acc == ac_edit:
            self._editar_usuario(row, 0)
        elif acc == ac_del:
            self._eliminar(username)

    def _eliminar(self, username: str):
        respuesta = ModernMessageBox.question(
            self, "Confirmar",
            f"Eliminar usuario '{username}'?\nEsta accion no se puede deshacer.",
        )
        if respuesta == QDialog.Accepted:
            try:
                UsuarioService.eliminar(username, session_id=self._session_id)
                self.mostrar_exito("Usuario eliminado correctamente.")
                self.cargar_usuarios()
            except DinamoBaseError as e:
                self.mostrar_error(str(e))

    def _hacer_backup(self):
        btn = self.sender()
        if btn:
            btn.setEnabled(False)
            btn.setText("Guardando...")

        try:
            ok, msg = BackupService.crear()
            if ok:
                ModernMessageBox.success(self, "Respaldo Exitoso", msg)
            else:
                ModernMessageBox.error(self, "Error", msg)
        except Exception as e:
            self.mostrar_error(str(e))
        finally:
            if btn:
                btn.setEnabled(True)
                btn.setText("Crear Backup Manual")
