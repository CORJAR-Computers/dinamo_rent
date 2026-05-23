"""
setup_wizard.py — Asistente de Configuración Inicial (Producción)
Guía al usuario para configurar la Base de Datos, Administrador y Preferencias.
"""

from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QFormLayout, QCheckBox, QPushButton, QMessageBox, QDialog
)
from PySide6.QtCore import Qt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.security import SecurityManager
from core.models import Base, Usuario
from core.config import guardar_configuracion
from views.styles import input_field, dialog_background


class DbSetupPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Paso 1: Configuración de Base de Datos")
        self.setSubTitle("Seleccione el motor y configure la conexión a la base de datos.")

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.cmb_engine = QComboBox()
        self.cmb_engine.addItems(["sqlite", "mysql"])
        self.cmb_engine.currentTextChanged.connect(self._toggle_mysql_fields)
        form.addRow("Motor:", self.cmb_engine)

        self.txt_host = QLineEdit("localhost")
        self.txt_port = QLineEdit("3306")
        self.txt_user = QLineEdit("root")
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_db = QLineEdit("dinamo_rent")

        for w in (self.cmb_engine, self.txt_host, self.txt_port, self.txt_user, self.txt_pass, self.txt_db):
            if isinstance(w, QLineEdit):
                input_field(w)

        self.lbl_host = QLabel("Host:")
        self.lbl_port = QLabel("Puerto:")
        self.lbl_user = QLabel("Usuario:")
        self.lbl_pass = QLabel("Contraseña:")
        self.lbl_db = QLabel("Base de Datos:")

        form.addRow(self.lbl_host, self.txt_host)
        form.addRow(self.lbl_port, self.txt_port)
        form.addRow(self.lbl_user, self.txt_user)
        form.addRow(self.lbl_pass, self.txt_pass)
        form.addRow(self.lbl_db, self.txt_db)

        layout.addLayout(form)

        self.btn_test = QPushButton("Probar Conexión")
        self.btn_test.clicked.connect(self._test_connection)

        self.lbl_status = QLabel()

        hbox = QHBoxLayout()
        hbox.addWidget(self.btn_test)
        hbox.addWidget(self.lbl_status)
        hbox.addStretch()
        layout.addLayout(hbox)

        self._toggle_mysql_fields("sqlite")

        # Registramos el campo engine para usarlo en otras páginas
        self.registerField("db_engine", self.cmb_engine)
        self.registerField("db_host", self.txt_host)
        self.registerField("db_port", self.txt_port)
        self.registerField("db_user", self.txt_user)
        self.registerField("db_pass", self.txt_pass)
        self.registerField("db_name", self.txt_db)

        self._connection_ok = False

    def _toggle_mysql_fields(self, text):
        is_mysql = (text == "mysql")
        self.lbl_host.setVisible(is_mysql)
        self.txt_host.setVisible(is_mysql)
        self.lbl_port.setVisible(is_mysql)
        self.txt_port.setVisible(is_mysql)
        self.lbl_user.setVisible(is_mysql)
        self.txt_user.setVisible(is_mysql)
        self.lbl_pass.setVisible(is_mysql)
        self.txt_pass.setVisible(is_mysql)
        self.lbl_db.setVisible(is_mysql)
        self.txt_db.setVisible(is_mysql)

        # Reset connection ok status
        self._connection_ok = False
        self.completeChanged.emit()

    def _test_connection(self):
        if self.cmb_engine.currentText() == "sqlite":
            self._connection_ok = True
            self.lbl_status.setText("✅ SQLite (Local) OK")
            self.lbl_status.setStyleSheet("color: green;")
            self.completeChanged.emit()
            return

        # MySQL
        try:
            url = f"mysql+pymysql://{self.txt_user.text()}:{self.txt_pass.text()}@{self.txt_host.text()}:{self.txt_port.text()}/"
            engine = create_engine(url)
            with engine.connect() as conn:
                # Intentar crear BD si no existe
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {self.txt_db.text()}"))

            self._connection_ok = True
            self.lbl_status.setText("✅ Conexión Exitosa")
            self.lbl_status.setStyleSheet("color: green;")
        except Exception as e:
            self._connection_ok = False
            self.lbl_status.setText(f"❌ Error: {str(e)[:50]}")
            self.lbl_status.setStyleSheet("color: red;")

        self.completeChanged.emit()

    def isComplete(self):
        return self._connection_ok


class AdminSetupPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Paso 2: Cuenta de Administrador")
        self.setSubTitle("Cree el usuario administrador principal.")

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.txt_user = QLineEdit("admin")
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_nombre = QLineEdit("Administrador Principal")

        input_field(self.txt_user)
        input_field(self.txt_pass)
        input_field(self.txt_nombre)

        form.addRow("Usuario:", self.txt_user)
        form.addRow("Contraseña:", self.txt_pass)
        form.addRow("Nombre:", self.txt_nombre)

        layout.addLayout(form)

        self.registerField("admin_user*", self.txt_user)
        self.registerField("admin_pass*", self.txt_pass)
        self.registerField("admin_name*", self.txt_nombre)

        self.lbl_warning = QLabel()
        self.lbl_warning.setStyleSheet("color: red;")
        layout.addWidget(self.lbl_warning)

        self.txt_pass.textChanged.connect(self.completeChanged)

    def isComplete(self):
        if len(self.txt_pass.text()) < 6:
            self.lbl_warning.setText("La contraseña debe tener al menos 6 caracteres")
            return False
        self.lbl_warning.setText("")
        return super().isComplete()


class PreferencesSetupPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Paso 3: Preferencias del Sistema")
        self.setSubTitle("Configuraciones generales de la empresa.")

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.txt_empresa = QLineEdit("Dinamo Rent")
        self.cmb_moneda = QComboBox()
        self.cmb_moneda.addItems(["$", "€", "£", "¥"])

        self.chk_encrypt = QCheckBox("Habilitar encriptación de Backups")
        self.txt_encrypt_pass = QLineEdit()
        self.txt_encrypt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_encrypt_pass.setEnabled(False)

        self.chk_encrypt.stateChanged.connect(lambda state: self.txt_encrypt_pass.setEnabled(state == Qt.CheckState.Checked.value))

        input_field(self.txt_empresa)
        input_field(self.txt_encrypt_pass)

        form.addRow("Nombre Empresa:", self.txt_empresa)
        form.addRow("Moneda:", self.cmb_moneda)
        form.addRow("", self.chk_encrypt)
        form.addRow("Clave Backups:", self.txt_encrypt_pass)

        layout.addLayout(form)

        self.registerField("pref_empresa*", self.txt_empresa)
        self.registerField("pref_moneda", self.cmb_moneda, "currentText")
        self.registerField("pref_encrypt", self.chk_encrypt)
        self.registerField("pref_encrypt_pass", self.txt_encrypt_pass)


class SetupWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asistente de Configuración - Dinamo Rent ERP")
        self.setMinimumSize(600, 450)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        dialog_background(self)

        self.addPage(DbSetupPage())
        self.addPage(AdminSetupPage())
        self.addPage(PreferencesSetupPage())

    def accept(self):
        try:
            self._save_configuration()
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error de Configuración", f"Ocurrió un error guardando la configuración:\\n{str(e)}")

    def _save_configuration(self):
        engine_type = self.field("db_engine")

        db_config = {"engine": engine_type}
        if engine_type == "mysql":
            db_config["host"] = self.field("db_host")
            db_config["port"] = self.field("db_port")
            db_config["user"] = self.field("db_user")
            db_config["password"] = self.field("db_pass")
            db_config["database"] = self.field("db_name")

            url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        else:
            url = "sqlite:///data/dinamo_rent.db"

        # 1. Crear Base de Datos temporalmente e insertar admin
        import os
        if engine_type == "sqlite":
            os.makedirs("data", exist_ok=True)

        engine = create_engine(url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        with Session() as session:
            admin_user = self.field("admin_user")
            if not session.query(Usuario).filter(Usuario.username == admin_user).first():
                admin = Usuario(
                    username=admin_user,
                    password=SecurityManager.hash_password(self.field("admin_pass")),
                    nombre=self.field("admin_name"),
                    rol="Administrador",
                    activo=1,
                    debe_cambiar_password=0
                )
                session.add(admin)
                session.commit()

        # 2. Guardar config.ini
        guardar_configuracion("database", db_config)

        app_config = {
            "production_mode": "true",
            "setup_completed": "true",
            "company_name": self.field("pref_empresa"),
            "currency_symbol": self.field("pref_moneda")
        }
        guardar_configuracion("app", app_config)

        backup_config = {
            "encryption_enabled": "true" if self.field("pref_encrypt") else "false",
            "encryption_password": self.field("pref_encrypt_pass")
        }
        guardar_configuracion("backup", backup_config)

def run_setup_wizard():
    """Lanza el asistente de configuración."""
    wizard = SetupWizard()
    if wizard.exec() == QDialog.DialogCode.Accepted:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Configuración Completada")
        msg.setText("El sistema se ha configurado exitosamente.\\nLa aplicación se cerrará para aplicar los cambios.\\nPor favor, vuelva a abrirla.")
        msg.exec()
        return True
    return False
