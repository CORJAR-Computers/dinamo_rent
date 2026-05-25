import pytest
from core.models import Usuario
from core.security import SecurityManager
from core.database_sa import get_session
import main_qt

def test_inicializar_base_datos_dev_mode(db_session, monkeypatch):
    """En modo desarrollo (PRODUCTION_MODE = False), el admin debe tener la contraseña Admin123!"""
    monkeypatch.setattr(main_qt, "PRODUCTION_MODE", False)
    
    # 1. Ejecutar inicialización
    main_qt.inicializar_base_datos()
    
    # 2. Verificar que se creó y que la contraseña es "Admin123!"
    with get_session() as session:
        admin = session.query(Usuario).filter(Usuario.username == 'admin').first()
        assert admin is not None
        assert admin.activo == 1
        assert SecurityManager.verify_password(admin.password, "Admin123!")
        assert admin.debe_cambiar_password == 0

def test_inicializar_base_datos_dev_mode_restablece_existente(db_session, monkeypatch):
    """En modo desarrollo, si el admin ya existe con otra contraseña, debe restablecerse a Admin123!"""
    monkeypatch.setattr(main_qt, "PRODUCTION_MODE", False)
    
    # 1. Crear usuario admin previamente con contraseña aleatoria/diferente y flag en 1
    with get_session() as session:
        # Asegurar que no hay ningún admin previo
        session.query(Usuario).filter(Usuario.username == 'admin').delete()
        session.commit()
        
        existing_admin = Usuario(
            username='admin',
            password=SecurityManager.hash_password("ContrasenaVieja123!"),
            nombre='Admin',
            rol='Administrador',
            activo=0,  # inactivo para probar que lo activa
            debe_cambiar_password=1
        )
        session.add(existing_admin)
        session.commit()
    
    # 2. Ejecutar inicialización
    main_qt.inicializar_base_datos()
    
    # 3. Verificar que se restableció
    with get_session() as session:
        admin = session.query(Usuario).filter(Usuario.username == 'admin').first()
        assert admin is not None
        assert admin.activo == 1
        assert SecurityManager.verify_password(admin.password, "Admin123!")
        assert admin.debe_cambiar_password == 0
