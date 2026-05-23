# Mejoras de Seguridad - Dinamo Rent ERP

Este documento describe las mejoras de seguridad implementadas en el sistema.

## Fecha de Implementación: 19 Abril 2026

---

## 1. Rate Limiting por IP

### Problema Anterior
El sistema solo rastreaba intentos de login por nombre de usuario, lo que podría ser insuficiente contra ataques distribuidos desde múltiples IPs.

### Solución Implementada
Se agregó `IPRateLimiter` en `core/security.py` que:

- **Limita intentos por IP**: Máximo 20 intentos por minuto desde una misma IP
- **Bloqueo temporal de IP**: Las IPs que excedan el límite son bloqueadas por 5 minutos
- **Monitoreo separado**: Tracking independente por usuario e IP

### Código reference:
- `core/security.py`: clase `IPRateLimiter`
- `services/auth_service.py`: método `login()` ahora acepta parámetro `ip`

---

## 2. CredentialManager con Codificación Base64

### Problema Anterior
Las contraseñas se almacenaban en texto plano en `_credentials`, lo que podría ser leído directamente en memoria.

### Solución Implementada
`core/security_utils.py` ahora codifica las contraseñas en Base64:

```python
# Antes (inseguro)
cls._credentials[service] = {'username': u, 'password': pwd}

# Ahora (mejorado)
encoded = base64.b64encode(password.encode())
cls._credentials[service] = {'username': u, 'password': encoded.decode(), '_encrypted': True}
```

**Nota**: Esto no es encriptación robusta, pero dificulta la lectura directa. Para producción, se recomienda usar un vault de secretos.

---

## 3. logs sin Exposición de Contraseñas

### Problema Anterior
`main_qt.py` escribía la contraseña temporal del admin en los logs:
```python
log.warning(f"Contraseña temporal de admin: {new_password}")
```

### Solución Implementada
Se cambió a un mensaje genérico:
```python
log.warning("Contraseña temporal generada (no almacenar, cambiarla en primer inicio)")
```

La contraseña sigue disponible en memoria para mostrarla al usuario, pero no se persiste en logs.

---

## 4. Auditoría Mejorada de Login

### Mejoras
Los logs de auditoría ahora incluyen:
- Dirección IP del cliente
- Timestamp preciso
- Tracking de intentos fallidos por IP

### Código reference:
- `services/auth_service.py`: `audit.info()` con más contexto

---

## 5. Autenticación con IP en Login

### Implementación
El método `login()` ahora acepta un parámetro `ip` opcional:
```python
def login(username: str, password: str, ip: str = None) -> dict:
```

La ventana de login obtiene la IP automáticamente y la pasa al servicio de autenticación.

---

## Tabla Resumen de Mejoras

| Mejora | Archivo | Severidad | Estado |
|-------|---------|-----------|--------|
| Rate limiting por IP | core/security.py | Alta | ✅ Implementado |
| Base64 encoding | core/security_utils.py | Media | ✅ Implementado |
| logs sin contraseñas | main_qt.py | Alta | ✅ Implementado |
| Auditoría mejorada | services/auth_service.py | Media | ✅ Implementado |
| Login con IP | main_qt.py | Media | ✅ Implementado |

---

## Recomendaciones Adicionales

### Alta Prioridad
1. **Migrar a Argon2**: Considerar migrar de PBKDF2 a Argon2 para hashing
2. **2FA**: Implementar autenticación de dos factores para administradores
3. **Vault de Secretos**: Usar HashiCorp Vault o similar para credenciales

### Media Prioridad
4. **Rate limiting en API**: Agregar headers `RateLimit-*` para debugging
5. **Notificaciones de seguridad**: Alertar al admin de intentos inusuales
6. **Políticas de contraseña**: Forzar cambio periódico de contraseñas

### Baja Prioridad
7. **SSO/SAML**: Integrar con directorio activo
8. **Certificados TLS**: Configurar TLS para conexiones

---

## Testing Recomendado

Para verificar las mejoras, ejecutar:

```bash
# Verificar sintaxis
python -m py_compile core/security.py
python -m py_compile services/auth_service.py
python -m py_compile main_qt.py

# Probar login con múltiples intentos
# (verificar que el rate limiting funcione)
```

---

## Contacto

Para preguntas sobre estas mejoras, contactar al equipo de desarrollo.