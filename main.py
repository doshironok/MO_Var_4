# main.py
# !/usr/bin/env python3
"""
Точка входа в приложение
Оптимизатор кормового рациона - решение задачи линейного программирования
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtCore import Qt
from views.main_window import MainWindow
from utils.constants import COLORS


def apply_modern_style(app):
    """Применение современного стиля к приложению"""

    # Настройка палитры
    palette = QPalette()

    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS['background']))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS['text']))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLORS['surface']))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS['secondary']))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLORS['background']))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(COLORS['text']))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLORS['text']))
    palette.setColor(QPalette.ColorRole.Button, QColor(COLORS['surface']))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS['text']))
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Link, QColor(COLORS['primary']))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS['primary']))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)

    app.setPalette(palette)

    # Таблица стилей CSS
    style_sheet = f"""
    QMainWindow {{
        background-color: {COLORS['background']};
    }}

    QWidget {{
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 10pt;
    }}

    QGroupBox {{
        font-weight: bold;
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 10px;
        background-color: {COLORS['surface']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 8px 0 8px;
        color: {COLORS['primary']};
    }}

    QPushButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 5px;
        padding: 8px 16px;
        font-weight: bold;
        min-width: 80px;
    }}

    QPushButton:hover {{
        background-color: {COLORS['primary_light']};
    }}

    QPushButton:pressed {{
        background-color: {COLORS['primary_dark']};
    }}

    QPushButton:disabled {{
        background-color: {COLORS['border']};
        color: {COLORS['text_light']};
    }}

    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        border: 2px solid {COLORS['border']};
        border-radius: 5px;
        padding: 6px;
        background-color: {COLORS['background']};
        selection-background-color: {COLORS['primary']};
    }}

    QLineEdit:focus, QComboBox:focus {{
        border-color: {COLORS['primary']};
    }}

    QTableWidget {{
        border: 2px solid {COLORS['border']};
        border-radius: 5px;
        background-color: {COLORS['background']};
        gridline-color: {COLORS['border']};
    }}

    QTableWidget::item {{
        padding: 6px;
    }}

    QTableWidget::item:selected {{
        background-color: {COLORS['primary']};
        color: white;
    }}

    QHeaderView::section {{
        background-color: {COLORS['secondary']};
        padding: 8px;
        border: none;
        border-right: 1px solid {COLORS['border']};
        border-bottom: 1px solid {COLORS['border']};
        font-weight: bold;
        color: {COLORS['primary']};
    }}

    QTabWidget::pane {{
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        background-color: {COLORS['background']};
    }}

    QTabBar::tab {{
        background-color: {COLORS['secondary']};
        border: 2px solid {COLORS['border']};
        border-bottom: none;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        padding: 10px 20px;
        margin-right: 2px;
        color: {COLORS['text']};
    }}

    QTabBar::tab:selected {{
        background-color: {COLORS['primary']};
        color: white;
        border-color: {COLORS['primary']};
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {COLORS['hover']};
    }}

    QMenuBar {{
        background-color: {COLORS['surface']};
        border-bottom: 2px solid {COLORS['border']};
    }}

    QMenuBar::item {{
        padding: 8px 12px;
        border-radius: 4px;
    }}

    QMenuBar::item:selected {{
        background-color: {COLORS['secondary']};
    }}

    QMenu {{
        background-color: {COLORS['background']};
        border: 2px solid {COLORS['border']};
        border-radius: 5px;
    }}

    QMenu::item {{
        padding: 6px 24px;
        border-radius: 3px;
    }}

    QMenu::item:selected {{
        background-color: {COLORS['secondary']};
        color: {COLORS['primary']};
    }}

    QStatusBar {{
        background-color: {COLORS['surface']};
        border-top: 2px solid {COLORS['border']};
        color: {COLORS['text_light']};
    }}

    QLabel {{
        color: {COLORS['text']};
    }}

    QLabel[role="heading"] {{
        font-size: 14pt;
        font-weight: bold;
        color: {COLORS['primary']};
        padding: 10px 0;
    }}

    QStatusBar QLabel {{
        color: {COLORS['text_light']};
    }}

    QMessageBox {{
        background-color: {COLORS['background']};
    }}

    QMessageBox QLabel {{
        color: {COLORS['text']};
        min-width: 300px;
    }}

    QMessageBox QPushButton {{
        min-width: 80px;
    }}
    """

    app.setStyleSheet(style_sheet)


def main():
    """Основная функция приложения"""
    app = QApplication(sys.argv)
    app.setApplicationName("Оптимизатор кормового рациона")
    app.setOrganizationName("КубГТУ")

    # Установка шрифта по умолчанию
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Применение стилей
    apply_modern_style(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()