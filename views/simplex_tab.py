# views/simplex_tab.py (финальная версия)
"""
Модуль вкладки отображения симплекс-итераций
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import numpy as np


class SimplexTab(QWidget):
    """Вкладка для отображения пошагового решения симплекс-методом"""

    def __init__(self):
        super().__init__()
        self.simplex_iterations = []
        self.phase1_iterations = []
        self.phase2_iterations = []
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("📐 Симплекс-метод: пошаговое решение")
        title.setProperty("role", "heading")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Управление
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background-color: #F1F8F1;
                border: 1px solid #C8E6C9;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        ctrl = QHBoxLayout(control_frame)
        ctrl.setSpacing(15)

        ctrl.addWidget(QLabel("Фаза:"))
        self.phase_combo = QComboBox()
        self.phase_combo.setMinimumWidth(250)
        self.phase_combo.currentIndexChanged.connect(self.on_phase_changed)
        ctrl.addWidget(self.phase_combo)

        ctrl.addSpacing(20)
        ctrl.addWidget(QLabel("Итерация:"))
        self.iter_combo = QComboBox()
        self.iter_combo.setMinimumWidth(150)
        self.iter_combo.currentIndexChanged.connect(self.on_iter_changed)
        ctrl.addWidget(self.iter_combo)

        ctrl.addStretch()

        self.show_all_btn = QPushButton("📋 Все итерации")
        self.show_all_btn.clicked.connect(self.show_all)
        ctrl.addWidget(self.show_all_btn)

        layout.addWidget(control_frame)

        # Информация об итерации
        info_group = QGroupBox("📊 Текущая итерация")
        info_layout = QGridLayout()
        info_layout.setSpacing(10)

        info_layout.addWidget(QLabel("Вводимая:"), 0, 0)
        self.entering_lbl = QLabel("—")
        self.entering_lbl.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 11pt;")
        info_layout.addWidget(self.entering_lbl, 0, 1)

        info_layout.addWidget(QLabel("Выводимая:"), 1, 0)
        self.leaving_lbl = QLabel("—")
        self.leaving_lbl.setStyleSheet("font-weight: bold; color: #E74C3C; font-size: 11pt;")
        info_layout.addWidget(self.leaving_lbl, 1, 1)

        info_layout.addWidget(QLabel("Целевая функция:"), 2, 0)
        self.obj_lbl = QLabel("—")
        self.obj_lbl.setStyleSheet("font-weight: bold; color: #2E7D32; font-size: 11pt;")
        info_layout.addWidget(self.obj_lbl, 2, 1)

        info_layout.addWidget(QLabel("Ведущий элемент:"), 3, 0)
        self.pivot_lbl = QLabel("—")
        self.pivot_lbl.setStyleSheet("font-weight: bold; color: #FF9800; font-size: 11pt;")
        info_layout.addWidget(self.pivot_lbl, 3, 1)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Симплекс-таблица
        table_group = QGroupBox("📋 Симплекс-таблица")
        table_layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setStyleSheet("""
            QTableWidget {
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #E8F5E9;
                padding: 6px;
                font-weight: bold;
            }
        """)
        table_layout.addWidget(self.table_widget)

        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # Навигация
        nav = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Предыдущая")
        self.prev_btn.clicked.connect(self.on_prev)
        nav.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Следующая ▶")
        self.next_btn.clicked.connect(self.on_next)
        nav.addWidget(self.next_btn)

        nav.addStretch()

        copy_btn = QPushButton("📋 Копировать")
        copy_btn.clicked.connect(self.copy_table)
        nav.addWidget(copy_btn)

        layout.addLayout(nav)

        # Пояснения
        expl_group = QGroupBox("💡 Пояснения")
        expl_layout = QVBoxLayout()

        self.expl_text = QTextEdit()
        self.expl_text.setReadOnly(True)
        self.expl_text.setMaximumHeight(120)
        expl_layout.addWidget(self.expl_text)

        expl_group.setLayout(expl_layout)
        layout.addWidget(expl_group)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def set_iterations(self, iterations: list, mode: str = ""):
        """Установка итераций"""
        self.simplex_iterations = iterations if iterations else []

        if not self.simplex_iterations:
            self._show_no_data()
            return

        self.phase1_iterations = [it for it in self.simplex_iterations if it.get('phase') == 1]
        self.phase2_iterations = [it for it in self.simplex_iterations if it.get('phase') == 2]

        self.phase_combo.blockSignals(True)
        self.phase_combo.clear()
        if self.phase1_iterations:
            self.phase_combo.addItem("Фаза 1 (поиск допустимого базиса)")
        if self.phase2_iterations:
            self.phase_combo.addItem("Фаза 2 (оптимизация)")

        if self.phase_combo.count() > 0:
            self.phase_combo.setCurrentIndex(0)
            self._update_iter_combo()
            if self.iter_combo.count() > 0:
                self.iter_combo.setCurrentIndex(0)
                phase = 1 if "Фаза 1" in self.phase_combo.currentText() else 2
                self._display(0, phase)

        self.phase_combo.blockSignals(False)
        self._update_nav()

    def _update_iter_combo(self):
        """Обновление списка итераций"""
        self.iter_combo.clear()
        current = self.phase_combo.currentText()
        iterations = self.phase1_iterations if "Фаза 1" in current else self.phase2_iterations

        for i in range(len(iterations)):
            self.iter_combo.addItem(f"Итерация {i}")

    def on_phase_changed(self, idx: int):
        """Смена фазы"""
        if idx >= 0:
            self._update_iter_combo()
            if self.iter_combo.count() > 0:
                self.iter_combo.setCurrentIndex(0)
                phase = 1 if "Фаза 1" in self.phase_combo.currentText() else 2
                self._display(0, phase)
        self._update_nav()

    def on_iter_changed(self, idx: int):
        """Смена итерации"""
        if idx >= 0:
            phase = 1 if "Фаза 1" in self.phase_combo.currentText() else 2
            self._display(idx, phase)
        self._update_nav()

    def on_prev(self):
        """Предыдущая итерация"""
        cur = self.iter_combo.currentIndex()
        if cur > 0:
            self.iter_combo.setCurrentIndex(cur - 1)
        elif self.phase_combo.currentIndex() > 0:
            self.phase_combo.setCurrentIndex(0)
            self.iter_combo.setCurrentIndex(self.iter_combo.count() - 1)

    def on_next(self):
        """Следующая итерация"""
        cur = self.iter_combo.currentIndex()
        if cur < self.iter_combo.count() - 1:
            self.iter_combo.setCurrentIndex(cur + 1)
        elif self.phase_combo.currentIndex() < self.phase_combo.count() - 1:
            self.phase_combo.setCurrentIndex(1)
            self.iter_combo.setCurrentIndex(0)

    def _update_nav(self):
        """Обновление кнопок навигации"""
        p = self.phase_combo.currentIndex()
        i = self.iter_combo.currentIndex()
        self.prev_btn.setEnabled(i > 0 or p > 0)
        self.next_btn.setEnabled(i < self.iter_combo.count() - 1 or p < self.phase_combo.count() - 1)

    def _display(self, idx: int, phase: int):
        """Отображение итерации"""
        iterations = self.phase1_iterations if phase == 1 else self.phase2_iterations
        if idx >= len(iterations):
            return

        it = iterations[idx]

        self.entering_lbl.setText(it.get('entering', '—'))
        self.leaving_lbl.setText(it.get('leaving', '—'))

        obj = it.get('objective_value')
        if obj is not None:
            if phase == 1:
                self.obj_lbl.setText(f"W = {obj:.4f}")
            else:
                self.obj_lbl.setText(f"Z = {obj:.4f}")
        else:
            self.obj_lbl.setText("—")

        pivot = it.get('pivot', (-1, -1))
        if pivot[0] >= 0:
            self.pivot_lbl.setText(f"строка {pivot[0]}, столбец {pivot[1]}")
        else:
            self.pivot_lbl.setText("—")

        # Таблица
        tableau = it.get('tableau')
        basis = it.get('basis', [])
        col_labels = it.get('col_labels', [])

        if tableau is not None:
            self._show_tableau(tableau, basis, col_labels, pivot, phase)

        # Пояснения
        self._show_explanation(it, phase, idx)

    def _show_tableau(self, tableau: np.ndarray, basis: list, col_labels: list,
                      pivot: tuple, phase: int):
        """Отображение симплекс-таблицы"""
        m, n = tableau.shape
        n_vars = n - 1

        self.table_widget.setRowCount(m)
        self.table_widget.setColumnCount(n_vars + 2)

        headers = ["Базис"]
        if col_labels and len(col_labels) == n_vars:
            headers.extend(col_labels)
        else:
            for j in range(n_vars):
                headers.append(f"x{j + 1}")
        headers.append("RHS")
        self.table_widget.setHorizontalHeaderLabels(headers)

        for i in range(m):
            # Базис
            if i < m - 1 and i < len(basis):
                txt = str(basis[i])
            elif i == m - 1:
                txt = "W" if phase == 1 else "Z"
            else:
                txt = "—"

            item = QTableWidgetItem(txt)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if i == m - 1:
                item.setBackground(QBrush(QColor("#E8F5E9")))
                item.setFont(QFont("Segoe UI", weight=QFont.Weight.Bold))
            else:
                item.setBackground(QBrush(QColor("#F1F8F1")))
            self.table_widget.setItem(i, 0, item)

            # Значения
            for j in range(n):
                val = tableau[i, j]
                if abs(val) < 1e-10:
                    txt = "0"
                else:
                    txt = f"{val:.4f}"

                item = QTableWidgetItem(txt)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                # Подсветка ведущего элемента
                if i == pivot[0] and j == pivot[1] and pivot[0] >= 0:
                    item.setBackground(QBrush(QColor("#4CAF50")))
                    item.setForeground(QBrush(Qt.GlobalColor.white))

                # Подсветка отрицательных в Z/W
                if i == m - 1 and val < -1e-10:
                    item.setForeground(QBrush(QColor("#E74C3C")))

                self.table_widget.setItem(i, j + 1, item)

        self.table_widget.resizeColumnsToContents()

    def _show_explanation(self, it: dict, phase: int, idx: int):
        """Пояснения к итерации"""
        entering = it.get('entering', '')
        leaving = it.get('leaving', '')

        if idx == 0:
            if phase == 1:
                text = "🔵 НАЧАЛО ФАЗЫ 1\n\n"
                text += "Введены искусственные переменные a1, a2, a3, a4 для ограничений-неравенств.\n"
                text += "Цель: W = a1 + a2 + a3 + a4 → min\n"
                text += "Выводим искусственные переменные из базиса."
            else:
                text = "🟢 НАЧАЛО ФАЗЫ 2\n\n"
                text += "Искусственные переменные удалены (W = 0).\n"
                text += "Восстановлена целевая функция: Z = 400·x1 + 200·x2 + 300·x3 → min\n"
                text += "Ищем оптимальное решение."
        else:
            if phase == 1:
                text = f"🔄 ФАЗА 1, ИТЕРАЦИЯ {idx}\n\n"
                text += f"• В базис вводится {entering}\n"
                text += f"• Из базиса выводится {leaving}\n"
                text += f"• Выполнено жорданово исключение\n"

                obj = it.get('objective_value')
                if obj is not None and abs(obj) < 1e-8:
                    text += "\n✅ Все искусственные переменные выведены!"
            else:
                text = f"🔄 ФАЗА 2, ИТЕРАЦИЯ {idx}\n\n"
                text += f"• В базис вводится {entering}\n"
                text += f"• Из базиса выводится {leaving}\n"
                text += f"• Выполнено жорданово исключение"

        self.expl_text.setText(text)

    def copy_table(self):
        """Копирование таблицы"""
        if self.table_widget.rowCount() == 0:
            return

        text = ""
        for j in range(self.table_widget.columnCount()):
            text += self.table_widget.horizontalHeaderItem(j).text() + "\t"
        text += "\n"

        for i in range(self.table_widget.rowCount()):
            for j in range(self.table_widget.columnCount()):
                item = self.table_widget.item(i, j)
                text += (item.text() if item else "") + "\t"
            text += "\n"

        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Готово", "Таблица скопирована в буфер обмена")

    def show_all(self):
        """Показать все итерации"""
        if not self.simplex_iterations:
            QMessageBox.information(self, "Информация", "Нет данных")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Все итерации симплекс-метода")
        dialog.resize(700, 500)

        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 10))

        text = "📐 СИМПЛЕКС-МЕТОД: ВСЕ ИТЕРАЦИИ\n"
        text += "=" * 60 + "\n\n"

        for phase in [1, 2]:
            iterations = self.phase1_iterations if phase == 1 else self.phase2_iterations
            if not iterations:
                continue

            text += f"ФАЗА {phase}\n" + "-" * 40 + "\n"
            for it in iterations:
                entering = it.get('entering', '')
                leaving = it.get('leaving', '')
                obj = it.get('objective_value', 0)

                if entering and leaving:
                    text += f"  Ввод: {entering:8s}  Вывод: {leaving:8s}  "
                else:
                    text += f"  Начало: "
                text += f"W={obj:.4f}\n" if phase == 1 else f"Z={obj:.4f}\n"
            text += f"  Итераций: {len(iterations)}\n\n"

        text_edit.setText(text)
        layout.addWidget(text_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn_box.accepted.connect(dialog.accept)
        layout.addWidget(btn_box)

        dialog.exec()

    def _show_no_data(self):
        """Нет данных"""
        self.entering_lbl.setText("—")
        self.leaving_lbl.setText("—")
        self.obj_lbl.setText("—")
        self.pivot_lbl.setText("—")
        self.table_widget.setRowCount(1)
        self.table_widget.setColumnCount(1)
        self.table_widget.setHorizontalHeaderLabels(["Нет данных"])
        self.table_widget.setItem(0, 0, QTableWidgetItem("Выполните расчет"))
        self.expl_text.setText("Нет данных о симплекс-итерациях")
        self.phase_combo.setEnabled(False)
        self.iter_combo.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)