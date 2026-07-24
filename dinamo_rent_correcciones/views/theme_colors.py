‘’‘
theme_colors.py — Paleta de colores centralizada para todas las vistas.

CODE-02: Evita la duplicación de constantes de color en cada vista.
Todas las vistas deben importar de aquí en vez de redefinir los colores.

Uso:
    from views.theme_colors import NAV, BLUE, BG, SURF, BORD, TEXT, MUTED
‘’‘

# ─── Colores base del sistema Dinamo Pro ────────────────────────────────────
NAV = "#1a3558"
BLUE = "#2563eb"
BG = "#f1f5f9"
SURF = "#ffffff"
BORD = "#cbd5e1"
TEXT = "#1e293b"
MUTED = "#64748b"

# ─── Variables adicionales ───────────────────────────────────────────────────
DARK = "#0f172a"
SUBTLE = "#f8fafc"
HOVER = "#e2e8f0"

# ─── Constantes de dimensiones compartidas ────────────────────────────────────
DIALOG_MIN_WIDTH = 600
DIALOG_MIN_HEIGHT = 450
BANNER_HEIGHT = 64
BANNER_MARGINS = (22, 0, 22, 0)
BANNER_SPACING = 14
ICO_SIZE = 40
CONTENT_MARGINS = (20, 16, 20, 16)
CONTENT_SPACING = 14
