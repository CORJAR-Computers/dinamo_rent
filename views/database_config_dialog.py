"""
database_config_dialog.py — Diálogo de Configuración de Base de Datos en Caliente.
Permite alternar entre SQLite y MySQL, probar la conexión y recargar el motor en memoria.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QFormLayout, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from sqlalchemy import create_engine, text

from core.config import (
    guardar_configuracion, DB_ENGINE, DB_PATH, DB_MYSQL
)
from views.styles import (
    input_field, input_combo, btn_primary, btn_default, dialog_background, apply_shadow
)
import core.config
import core.database_sa
import importlib


class DatabaseConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Base de Datos")
        self.setMinimumSize(460, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Aplicar estilos base
        dialog_background(self)

        self._connection_ok = False
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Título y descripción
        lbl_title = QLabel("Configurar Base de Datos")
        lbl_title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #1e3a8a;")
        lbl_desc = QLabel("Seleccione el motor de base de datos e ingrese los parámetros de conexión.")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #64748b; font-size: 10pt;")

        main_layout.addWidget(lbl_title)
        main_layout.addWidget(lbl_desc)

        # Card del Formulario
        self.form_card = QFrame()
        self.form_card.setObjectName("formCard")
        self.form_card.setStyleSheet("QFrame#formCard { background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; }")
        apply_shadow(self.form_card)

        card_layout = QVBoxLayout(self.form_card)
        card_layout.setContentsMargins(15, 15, 15, 15)

        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(10)
        self.form_layout.setVerticalSpacing(10)
        self.form_layout.setHorizontalSpacing(15)

        # Selector de Motor
        self.cmb_engine = QComboBox()
        self.cmb_engine.addItems(["sqlite", "mysql"])
        input_combo(self.cmb_engine)
        self.cmb_engine.currentTextChanged.connect(self._toggle_engine_fields)
        self.form_layout.addRow("Motor de BD:", self.cmb_engine)

        # Campos de SQLite
        self.txt_path = QLineEdit()
        input_field(self.txt_path)
        self.lbl_path = QLabel("Ruta del archivo:")
        self.form_layout.addRow(self.lbl_path, self.txt_path)

        # Campos de MySQL
        self.txt_host = QLineEdit()
        self.txt_port = QLineEdit()
        self.txt_user = QLineEdit()
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_db = QLineEdit()

        for widget in (self.txt_host, self.txt_port, self.txt_user, self.txt_pass, self.txt_db):
            input_field(widget)

        self.lbl_host = QLabel("Host:")
        self.lbl_port = QLabel("Puerto:")
        self.lbl_user = QLabel("Usuario:")
        self.lbl_pass = QLabel("Contraseña:")
        self.lbl_db = QLabel("Base de Datos:")

        self.form_layout.addRow(self.lbl_host, self.txt_host)
        self.form_layout.addRow(self.lbl_port, self.txt_port)
        self.form_layout.addRow(self.lbl_user, self.txt_user)
        self.form_layout.addRow(self.lbl_pass, self.txt_pass)
        self.form_layout.addRow(self.lbl_db, self.txt_db)

        card_layout.addLayout(self.form_layout)
        main_layout.addWidget(self.form_card)

        # Cargar valores actuales en los campos
        self._load_current_values()

        # Botón de Probar Conexión e Indicador de Estado
        hbox_test = QHBoxLayout()
        self.btn_test = QPushButton("Probar Conexión")
        btn_default(self.btn_test)
        self.btn_test.clicked.connect(self._test_connection)

        self.lbl_status = QLabel("Sin comprobar")
        self.lbl_status.setStyleSheet("color: #64748b; font-weight: bold;")

        hbox_test.addWidget(self.btn_test)
        hbox_test.addWidget(self.lbl_status)
        hbox_test.addStretch()
        main_layout.addLayout(hbox_test)

        # Botones de Aceptar / Cancelar
        hbox_buttons = QHBoxLayout()
        self.btn_save = QPushButton("Guardar y Aplicar")
        btn_primary(self.btn_save)
        self.btn_save.clicked.connect(self._save_and_apply)

        self.btn_cancel = QPushButton("Cancelar")
        btn_default(self.btn_cancel)
        self.btn_cancel.clicked.connect(self.reject)

        hbox_buttons.addStretch()
        hbox_buttons.addWidget(self.btn_cancel)
        hbox_buttons.addWidget(self.btn_save)
        main_layout.addLayout(hbox_buttons)

        # Inicializar visibilidad de campos
        self._toggle_engine_fields(self.cmb_engine.currentText())

    def _load_current_values(self):
        # Seleccionar motor actual
        self.cmb_engine.setCurrentText(DB_ENGINE)

        # Cargar SQLite
        import os
        db_name = core.config._cfg.get("database", "path", "dinamo_rent_v3.db")
        self.txt_path.setText(db_name)

        # Cargar MySQL
        self.txt_host.setText(DB_MYSQL.get("host", "localhost"))
        self.txt_port.setText(str(DB_MYSQL.get("port", 3306)))
        self.txt_user.setText(DB_MYSQL.get("user", "root"))
        self.txt_pass.setText(DB_MYSQL.get("password", ""))
        self.txt_db.setText(DB_MYSQL.get("database", "dinamo_rent"))

    def _toggle_engine_fields(self, engine):
        is_mysql = (engine == "mysql")
        is_sqlite = (engine == "sqlite")

        # Alternar campos SQLite
        self.lbl_path.setVisible(is_sqlite)
        self.txt_path.setVisible(is_sqlite)

        # Alternar campos MySQL
        for widget in (self.lbl_host, self.txt_host, self.lbl_port, self.txt_port,
                       self.lbl_user, self.txt_user, self.lbl_pass, self.txt_pass,
                       self.lbl_db, self.txt_db):
            widget.setVisible(is_mysql)

        self._connection_ok = False
        self.lbl_status.setText("Sin comprobar")
        self.lbl_status.setStyleSheet("color: #64748b; font-weight: bold;")

    def _test_connection(self):
        engine_type = self.cmb_engine.currentText()

        if engine_type == "sqlite":
            path = self.txt_path.text().strip()
            if not path:
                self._set_status(False, "Ruta vacía")
                return
            self._set_status(True, "✅ SQLite listo")
            return

        # MySQL
        host = self.txt_host.text().strip()
        port = self.txt_port.text().strip()
        user = self.txt_user.text().strip()
        password = self.txt_pass.text()
        db = self.txt_db.text().strip()

        if not all([host, port, user, db]):
            self._set_status(False, "Campos obligatorios vacíos")
            return

        self.lbl_status.setText("Conectando…")
        self.lbl_status.setStyleSheet("color: #3b82f6; font-weight: bold;")
        self.repaint()

        try:
            # Intentar conexión con timeout bajo
            url = f"mysql+pymysql://{user}:{password}@{host}:{port}/"
            test_engine = create_engine(url, connect_args={"connect_timeout": 5})
            with test_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db}"))

            # Validar acceso a la BD directamente
            url_db = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
            test_engine_db = create_engine(url_db, connect_args={"connect_timeout": 5})
            with test_engine_db.connect() as conn:
                conn.execute(text("SELECT 1"))

            self._set_status(True, "✅ Conexión Exitosa")
        except Exception as e:
            self._set_status(False, f"❌ Error: {str(e)[:40]}")

    def _set_status(self, ok: bool, text: str):
        self._connection_ok = ok
        self.lbl_status.setText(text)
        if ok:
            self.lbl_status.setStyleSheet("color: #16a34a; font-weight: bold;")
        else:
            self.lbl_status.setStyleSheet("color: #dc2626; font-weight: bold;")

    def _save_and_apply(self):
        if not self._connection_ok:
            # Advertir al usuario si no ha probado la conexión
            ret = QMessageBox.question(
                self, "Conexión no verificada",
                "No ha verificado exitosamente la conexión. ¿Desea guardar de todos modos?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if ret == QMessageBox.StandardButton.No:
                return

        engine_type = self.cmb_engine.currentText()
        db_config = {"engine": engine_type}

        if engine_type == "sqlite":
            db_config["path"] = self.txt_path.text().strip()
        else:
            db_config["host"] = self.txt_host.text().strip()
            db_config["port"] = self.txt_port.text().strip()
            db_config["user"] = self.txt_user.text().strip()
            db_config["password"] = self.txt_pass.text()
            db_config["database"] = self.txt_db.text().strip()

        try:
            # 1. Guardar en config.ini
            guardar_configuracion("database", db_config)

            # 2. Recargar configuración global en caliente
            importlib.reload(core.config)

            # 3. Disponer e invalidar la conexión antigua de base de datos
            core.database_sa.reset_database_connection()

            # 4. Inicializar las tablas y migraciones sobre el nuevo motor
            core.database_sa.init_db()

            QMessageBox.information(
                self, "Éxito",
                f"Configuración de Base de Datos actualizada a {engine_type.upper()} exitosamente en caliente.",
                QMessageBox.StandardButton.Ok
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Error al Inicializar",
                f"Se guardó la configuración pero falló la inicialización del motor:\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
