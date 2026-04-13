"""
views/usuarios_view.py — Vista refactorizada para la Administración de Usuarios.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QLabel,
    QLineEdit, QDialog, QFormLayout, QComboBox, QMessageBox,
    QGroupBox, QAbstractItemView, QMenu
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QCursor, QAction

# IMPORTACIONES A LA CAPA DE SERVICIOS
from services.services import BackupService
from services.services_extra import UsuarioService
from core.exceptions import DinamoBaseError

# =============================================================================
# DIÁLOGO CREAR/EDITAR USUARIO
# =============================================================================
class UsuarioFormDialog(QDialog):
    def __init__(self, parent=None, datos_usuario=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Usuario")
        self.setFixedSize(450, 500)
        self.datos_usuario = datos_usuario or {}

        self._setup_ui()
        if self.datos_usuario:
            self.cargar_datos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.txt_nombre = QLineEdit()
        self.txt_username = QLineEdit()
        self.txt_email = QLineEdit()

        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems(["Administrador", "Operador", "Supervisor", "Mecánico"])

        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["Activo", "Inactivo"])

        form_layout.addRow("Nombre Completo:", self.txt_nombre)
        form_layout.addRow("Usuario (Login):", self.txt_username)
        form_layout.addRow("Email:", self.txt_email)
        form_layout.addRow("Rol / Perfil:", self.cmb_rol)
        form_layout.addRow("Estado:", self.cmb_estado)
        layout.addLayout(form_layout)

        # SECCIÓN CONTRASEÑA
        group_pass = QGroupBox("Seguridad")
        lay_pass = QFormLayout()

        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setPlaceholderText("Dejar vacío para no cambiar" if self.datos_usuario else "Nueva contraseña")

        self.txt_confirm = QLineEdit()
        self.txt_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_confirm.setPlaceholderText("Repetir contraseña")

        lay_pass.addRow("Contraseña:", self.txt_pass)
        lay_pass.addRow("Confirmar:", self.txt_confirm)
        group_pass.setLayout(lay_pass)
        layout.addWidget(group_pass)

        # BOTONES
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Guardar Usuario")
        btn_save.setStyleSheet("background-color: #004aad; color: white; padding: 10px; font-weight: bold;")
        btn_save.clicked.connect(self.guardar)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def cargar_datos(self):
        d = self.datos_usuario
        self.txt_nombre.setText(str(d.get('nombre', '')))
        self.txt_username.setText(str(d.get('username', '')))
        self.txt_username.setEnabled(False)  # El username no se debe cambiar
        self.txt_email.setText(str(d.get('email', '')))
        self.cmb_rol.setCurrentText(str(d.get('rol', 'Operador')))

        activo = d.get('activo', 1)
        self.cmb_estado.setCurrentIndex(0 if activo == 1 else 1)

    def guardar(self):
        pwd = self.txt_pass.text()
        pwd2 = self.txt_confirm.text()

        if pwd and pwd != pwd2:
            return QMessageBox.warning(self, "Error", "Las contraseñas no coinciden.")

        estado = 1 if self.cmb_estado.currentIndex() == 0 else 0

        datos = {
            "username": self.txt_username.text().strip(),
            "nombre": self.txt_nombre.text().strip(),
            "rol": self.cmb_rol.currentText(),
            "email": self.txt_email.text().strip(),
            "activo": estado,
            "password_raw": pwd  # El servicio se encarga de hashear esto
        }

        try:
            if self.datos_usuario:
                UsuarioService.actualizar(datos)
            else:
                UsuarioService.crear(datos)

            QMessageBox.information(self, "Éxito", "Usuario guardado correctamente.")
            self.accept()
        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", str(e))


# =============================================================================
# WIDGET PRINCIPAL DE USUARIOS
# =============================================================================
class UsuariosWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Header
        top = QHBoxLayout()
        lbl = QLabel("Administración de Usuarios")
        lbl.setStyleSheet("font-size: 20px; font-weight: bold;")

        btn_new = QPushButton("+ Crear Usuario")
        btn_new.setStyleSheet("background-color: green; color: white; padding: 8px; font-weight: bold;")
        btn_new.clicked.connect(self.nuevo_usuario)

        btn_backup = QPushButton("💾 Crear Backup Manual")
        btn_backup.setStyleSheet("background-color: #ef6c00; color: white; font-weight: bold; padding: 8px;")
        btn_backup.clicked.connect(self.hacer_backup)

        btn_ref = QPushButton("Actualizar")
        btn_ref.clicked.connect(self.cargar_usuarios)

        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(btn_ref)
        top.addWidget(btn_new)
        top.addWidget(btn_backup)
        layout.addLayout(top)

        # Tabla
        self.tabla = QTableWidget()
        self.configurar_tabla()
        layout.addWidget(self.tabla)

        self.lista_usuarios = []
        self.cargar_usuarios()

    def configurar_tabla(self):
        cols = ["Usuario", "Nombre Completo", "Rol", "Email", "Estado", "Último Acceso"]
        self.tabla.setColumnCount(len(cols))
        self.tabla.setHorizontalHeaderLabels(cols)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.cellDoubleClicked.connect(self.editar_usuario)
        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self.mostrar_menu)

    def cargar_usuarios(self):
        self.tabla.setRowCount(0)
        self.lista_usuarios.clear()

        try:
            usuarios = UsuarioService.listar()

            for i, u in enumerate(usuarios):
                self.tabla.insertRow(i)
                self.lista_usuarios.append(u)

                estado = "Activo" if u.get('activo') == 1 else "Inactivo"

                display_name = u.get('nombre') or ''
                items = [
                    u.get('username', ''),
                    display_name,
                    u.get('rol', ''),
                    u.get('email', ''),
                    estado,
                    u.get('ultimo_acceso', '') or 'Nunca'
                ]

                for j, val in enumerate(items):
                    it = QTableWidgetItem(str(val))
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tabla.setItem(i, j, it)

                    if j == 4:  # Columna de Estado
                        if estado == "Activo":
                            it.setForeground(QBrush(QColor("green")))
                        else:
                            it.setForeground(QBrush(QColor("red")))

        except DinamoBaseError as e:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los usuarios: {e}")

    def nuevo_usuario(self):
        dlg = UsuarioFormDialog(self)
        if dlg.exec():
            self.cargar_usuarios()

    def editar_usuario(self, row, col):
        datos = self.lista_usuarios[row]
        dlg = UsuarioFormDialog(self, datos)
        if dlg.exec():
            self.cargar_usuarios()

    def mostrar_menu(self, pos):
        item = self.tabla.itemAt(pos)
        if not item:
            return

        row = item.row()
        username = self.tabla.item(row, 0).text()

        menu = QMenu(self)
        ac_del = QAction("❌ Eliminar Usuario", self)
        ac_del.triggered.connect(lambda: self.eliminar(username))
        menu.addAction(ac_del)
        menu.exec(QCursor.pos())

    def eliminar(self, username):
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar usuario '{username}'?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                UsuarioService.eliminar(username)
                QMessageBox.information(self, "Éxito", "Usuario eliminado.")
                self.cargar_usuarios()
            except DinamoBaseError as e:
                QMessageBox.warning(self, "Error", str(e))

    def hacer_backup(self):
        btn = self.sender()
        btn.setEnabled(False)
        btn.setText("Guardando...")

        # Llamar al servicio de Backup
        ok, msg = BackupService.crear()

        if ok:
            QMessageBox.information(self, "Respaldo Exitoso", msg)
        else:
            QMessageBox.critical(self, "Error", msg)

        btn.setEnabled(True)
        btn.setText("💾 Crear Backup Manual")