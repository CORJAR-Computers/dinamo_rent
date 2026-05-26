"""themes.py — Professional color palettes for Dinamo Rent ERP

Each theme dict provides a full set of design tokens for the QSS stylesheet
builder. Tokens cover backgrounds, surfaces, text, borders, interactive
states, badges, and accent colors.

Design philosophy:
- **Light (Dinamo):** Clean, crisp, airy. White cards on a very light cool-gray
  canvas. Borders are defined but delicate. The primary blue (#2563eb) provides
  confident interaction points. The sidebar uses a subtle tint for clear
  visual separation from the content area.
- **Dark (SaaS):** Deep, rich, sophisticated. Layered dark surfaces with subtle
  elevation cues via border lightness. Indigo primary (#818cf8) adds a premium
  feel. Banner gradients bring subdued color personality to the dark canvas.
"""

THEME_DINAMO = {
    # ── Primary ────────────────────────────────────────────────────────
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "primary_light": "rgba(37, 99, 235, 0.10)",
    "primary_dark": "#1e40af",
    # ── Backgrounds ────────────────────────────────────────────────────
    "bg": "#f8fafc",
    "bg_card": "#ffffff",
    "bg_input": "#ffffff",
    "bg_sidebar": "#ffffff",
    "bg_banner_start": "#0f2b4b",
    "bg_banner_end": "#2563eb",
    # ── Text ───────────────────────────────────────────────────────────
    "fg": "#0f172a",
    "fg_muted": "#64748b",
    "fg_on_primary": "#ffffff",
    # ── Borders ────────────────────────────────────────────────────────
    "border": "#d1d9e6",
    "border_focus": "#2563eb",
    # ── Accents ────────────────────────────────────────────────────────
    "accent": "#0ea5e9",
    "accent_light": "rgba(14, 165, 233, 0.12)",
    # ── Semantic ───────────────────────────────────────────────────────
    "success": "#16a34a",
    "success_light": "rgba(22, 163, 74, 0.10)",
    "warning": "#d97706",
    "warning_light": "rgba(217, 119, 6, 0.10)",
    "danger": "#dc2626",
    "danger_hover": "#b91c1c",
    "danger_light": "rgba(220, 38, 38, 0.10)",
    "info": "#2563eb",
    "info_light": "rgba(37, 99, 235, 0.10)",
    # ── Table ──────────────────────────────────────────────────────────
    "table_alt": "#f4f7fb",
    "table_grid": "#e8eef4",
    "table_header_bg": "#f1f5f9",
    # ── Overlay ────────────────────────────────────────────────────────
    "overlay_bg": "rgba(15, 23, 42, 0.65)",
    # ── Scrollbar ──────────────────────────────────────────────────────
    "scrollbar_handle": "#cbd5e1",
    "scrollbar_hover": "#94a3b8",
    # ── Sidebar ────────────────────────────────────────────────────────
    "sidebar_bg": "#f1f5f9",
    "sidebar_item": "#475569",
    "sidebar_item_hover_bg": "rgba(37, 99, 235, 0.08)",
    "sidebar_item_active": "#2563eb",
    "sidebar_item_active_bg": "rgba(37, 99, 235, 0.10)",
    "sidebar_category_bg": "#ecf2f8",
    "sidebar_category_border": "rgba(37, 99, 235, 0.20)",
    "sidebar_footer_bg": "#ecf2f8",
    # ── Progress ───────────────────────────────────────────────────────
    "progress_bg": "#e2e8f0",
    "progress_chunk": "#2563eb",
    # ── Tooltip ────────────────────────────────────────────────────────
    "tooltip_bg": "#1e293b",
    "tooltip_fg": "#f8fafc",
    # ── Calendar Legend ────────────────────────────────────────────────
    "legend_available_bg": "#dbeafe",
    "legend_rented_bg": "#dcfce7",
    "legend_reserved_bg": "#fef3c7",
}

THEME_SAAS = {
    # ── Primary ────────────────────────────────────────────────────────
    "primary": "#818cf8",
    "primary_hover": "#6366f1",
    "primary_light": "rgba(129, 140, 248, 0.12)",
    "primary_dark": "#4f46e5",
    # ── Backgrounds ────────────────────────────────────────────────────
    "bg": "#0c101c",
    "bg_card": "#1a2332",
    "bg_input": "#1a2332",
    "bg_sidebar": "#0a0f18",
    "bg_banner_start": "#0d1b33",
    "bg_banner_end": "#2a3f60",
    # ── Text ───────────────────────────────────────────────────────────
    "fg": "#eef2f8",
    "fg_muted": "#8899b0",
    "fg_on_primary": "#ffffff",
    # ── Borders ────────────────────────────────────────────────────────
    "border": "#2a354a",
    "border_focus": "#818cf8",
    # ── Accents ────────────────────────────────────────────────────────
    "accent": "#22d3ee",
    "accent_light": "rgba(34, 211, 238, 0.12)",
    # ── Semantic ───────────────────────────────────────────────────────
    "success": "#34d399",
    "success_light": "rgba(52, 211, 153, 0.12)",
    "warning": "#fbbf24",
    "warning_light": "rgba(251, 191, 36, 0.12)",
    "danger": "#f87171",
    "danger_hover": "#ef4444",
    "danger_light": "rgba(248, 113, 113, 0.12)",
    "info": "#818cf8",
    "info_light": "rgba(129, 140, 248, 0.12)",
    # ── Table ──────────────────────────────────────────────────────────
    "table_alt": "#141e2e",
    "table_grid": "#1e2a3e",
    "table_header_bg": "#141e2e",
    # ── Overlay ────────────────────────────────────────────────────────
    "overlay_bg": "rgba(8, 12, 22, 0.80)",
    # ── Scrollbar ──────────────────────────────────────────────────────
    "scrollbar_handle": "#2a354a",
    "scrollbar_hover": "#3d4a63",
    # ── Sidebar ────────────────────────────────────────────────────────
    "sidebar_bg": "#0a0f18",
    "sidebar_item": "#8899b0",
    "sidebar_item_hover_bg": "rgba(129, 140, 248, 0.08)",
    "sidebar_item_active": "#818cf8",
    "sidebar_item_active_bg": "rgba(129, 140, 248, 0.12)",
    "sidebar_category_bg": "#101826",
    "sidebar_category_border": "rgba(129, 140, 248, 0.20)",
    "sidebar_footer_bg": "#0d1421",
    # ── Progress ───────────────────────────────────────────────────────
    "progress_bg": "#1a2332",
    "progress_chunk": "#818cf8",
    # ── Tooltip ────────────────────────────────────────────────────────
    "tooltip_bg": "#eef2f8",
    "tooltip_fg": "#0c101c",
    # ── Calendar Legend ────────────────────────────────────────────────
    "legend_available_bg": "#1a2d4a",
    "legend_rented_bg": "#143028",
    "legend_reserved_bg": "#2a2010",
}
