
from app.config import (COLOR_ACCENT, COLOR_ACCENT_DIM, COLOR_BG,
                        COLOR_BG_ALT, COLOR_ERROR, COLOR_TEXT,
                        COLOR_TEXT_DIM)

APP_STYLE = f"""
* {{ font-family: "Segoe UI", "Segoe UI Emoji"; }}

QWidget {{
    background-color: transparent;
    color: {COLOR_TEXT};
    font-size: 13px;
}}

#panel {{
    background-color: rgba(17, 21, 17, 225);
    border: 1px solid {COLOR_ACCENT_DIM};
    border-radius: 10px;
}}

#title {{
    color: {COLOR_ACCENT};
    font-size: 30px;
    font-weight: 800;
    letter-spacing: 2px;
}}

#subtitle {{
    color: {COLOR_TEXT_DIM};
    font-size: 12px;
}}

#phaseLabel {{
    color: {COLOR_ACCENT};
    font-size: 15px;
    font-weight: 600;
}}

QListWidget {{
    background-color: rgba(13, 13, 13, 190);
    border: 1px solid {COLOR_ACCENT_DIM};
    border-radius: 8px;
    padding: 6px;
    outline: none;
}}
QListWidget::item {{
    padding: 7px 10px;
    border-radius: 6px;
    margin: 2px;
}}
QListWidget::item:hover {{ background-color: rgba(0, 255, 0, 20); }}
QListWidget::item:selected {{ background-color: rgba(0, 255, 0, 35); }}

QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {COLOR_ACCENT_DIM};
    border-radius: 4px;
    background: {COLOR_BG};
}}
QCheckBox::indicator:checked {{
    background: {COLOR_ACCENT};
    border: 1px solid {COLOR_ACCENT};
    image: none;
}}

QPushButton {{
    background-color: rgba(0, 255, 0, 18);
    color: {COLOR_ACCENT};
    border: 1px solid {COLOR_ACCENT};
    border-radius: 8px;
    padding: 10px 22px;
    font-weight: 700;
}}
QPushButton:hover {{ background-color: rgba(0, 255, 0, 45); }}
QPushButton:pressed {{ background-color: rgba(0, 255, 0, 80); color: {COLOR_BG}; }}
QPushButton:disabled {{
    color: {COLOR_TEXT_DIM};
    border-color: {COLOR_ACCENT_DIM};
    background: transparent;
}}

#startButton {{
    font-size: 17px;
    padding: 14px 34px;
}}

QProgressBar {{
    background-color: {COLOR_BG};
    border: 1px solid {COLOR_ACCENT_DIM};
    border-radius: 7px;
    height: 14px;
    text-align: center;
    color: {COLOR_BG};
    font-weight: 700;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00aa00, stop:1 {COLOR_ACCENT});
    border-radius: 6px;
}}

#logView {{
    background-color: rgba(8, 10, 8, 235);
    border: 1px solid {COLOR_ACCENT_DIM};
    border-radius: 8px;
    font-family: "Consolas", "Cascadia Mono", monospace;
    font-size: 12px;
    padding: 8px;
}}

QScrollBar:vertical {{
    background: {COLOR_BG};
    width: 9px;
    margin: 2px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_ACCENT_DIM};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {COLOR_ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QLineEdit {{
    background-color: rgba(13, 13, 13, 220);
    border: 1px solid {COLOR_ACCENT_DIM};
    border-radius: 7px;
    padding: 8px 12px;
    color: {COLOR_TEXT};
    font-size: 12px;
    selection-background-color: {COLOR_ACCENT};
    selection-color: {COLOR_BG};
}}
QLineEdit:focus {{ border: 1px solid {COLOR_ACCENT}; }}

QToolTip {{
    background-color: {COLOR_BG_ALT};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_ACCENT};
}}

#titleBar {{
    background-color: rgba(17, 21, 17, 245);
    border-bottom: 1px solid {COLOR_ACCENT_DIM};
}}

#titleBtn {{
    background-color: transparent;
    color: {COLOR_TEXT_DIM};
    border: none;
    border-radius: 13px;
    padding: 0;
    font-size: 14px;
    font-weight: 700;
}}
#titleBtn:hover {{ color: {COLOR_ACCENT}; background-color: rgba(0, 255, 0, 30); }}
#titleBtn:pressed {{ color: {COLOR_BG}; background-color: {COLOR_ACCENT}; }}

#badgeOk {{ color: {COLOR_ACCENT}; font-weight: 700; }}
#badgeWarn {{ color: {COLOR_ERROR}; font-weight: 700; }}
#statValue {{ color: {COLOR_ACCENT}; font-size: 20px; font-weight: 800; }}
#statName {{ color: {COLOR_TEXT_DIM}; font-size: 11px; }}
#footer {{ color: {COLOR_TEXT_DIM}; font-size: 11px; }}
"""
