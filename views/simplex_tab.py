# views/simplex_tab.py
"""
Модуль вкладки отображения симплекс-итераций
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import numpy as np
import traceback


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
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("📐 Симплекс-метод: пошаговое решение")
        title_label.setProperty("role", "heading")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Выбор фазы и итерации
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background-color: #F1F8F1;
                border: 1px solid #C8E6C9;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        control_layout = QHBoxLayout(control_frame)
        control_layout.setSpacing(15)

        control_layout.addWidget(QLabel("Фаза:"))
        self.phase_combo = QComboBox()
        self.phase_combo.setMinimumWidth(250)
        self.phase_combo.currentIndexChanged.connect(self.on_phase_changed)
        control_layout.addWidget(self.phase_combo)

        control_layout.addSpacing(20)

        control_layout.addWidget(QLabel("Итерация:"))
        self.iteration_combo = QComboBox()
        self.iteration_combo.setMinimumWidth(150)
        self.iteration_combo.currentIndexChanged.connect(self.on_iteration_changed)
        control_layout.addWidget(self.iteration_combo)

        control_layout.addStretch()

        self.show_all_btn = QPushButton("📋 Показать все итерации")
        self.show_all_btn.clicked.connect(self.show_all_iterations)
        control_layout.addWidget(self.show_all_btn)

        layout.addWidget(control_frame)

        # Информация о текущей итерации
        info_group = QGroupBox("📊 Информация о текущей итерации")
        info_layout = QGridLayout()
        info_layout.setSpacing(10)

        info_layout.addWidget(QLabel("Вводимая переменная:"), 0, 0)
        self.entering_label = QLabel("—")
        self.entering_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 11pt;")
        info_layout.addWidget(self.entering_label, 0, 1)

        info_layout.addWidget(QLabel("Выводимая переменная:"), 1, 0)
        self.leaving_label = QLabel("—")
        self.leaving_label.setStyleSheet("font-weight: bold; color: #E74C3C; font-size: 11pt;")
        info_layout.addWidget(self.leaving_label, 1, 1)

        info_layout.addWidget(QLabel("Значение целевой функции:"), 2, 0)
        self.objective_label = QLabel("—")
        self.objective_label.setStyleSheet("font-weight: bold; color: #2E7D32; font-size: 11pt;")
        info_layout.addWidget(self.objective_label, 2, 1)

        info_layout.addWidget(QLabel("Ведущий элемент:"), 3, 0)
        self.pivot_label = QLabel("—")
        self.pivot_label.setStyleSheet("font-weight: bold; color: #FF9800; font-size: 11pt;")
        info_layout.addWidget(self.pivot_label, 3, 1)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Симплекс-таблица
        table_group = QGroupBox("📋 Симплекс-таблица")
        table_layout = QVBoxLayout()

        table_scroll = QScrollArea()
        table_scroll.setWidgetResizable(True)
        table_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table_scroll.setMinimumHeight(350)

        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setStyleSheet("""
            QTableWidget {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
            }
        """)
        self.table_widget.horizontalHeader().setMinimumSectionSize(70)

        table_scroll.setWidget(self.table_widget)
        table_layout.addWidget(table_scroll)

        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # Навигация
        nav_frame = QFrame()
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setSpacing(10)

        self.prev_btn = QPushButton("◀ Предыдущая итерация")
        self.prev_btn.setMinimumHeight(35)
        self.prev_btn.clicked.connect(self.on_prev_iteration)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Следующая итерация ▶")
        self.next_btn.setMinimumHeight(35)
        self.next_btn.clicked.connect(self.on_next_iteration)
        nav_layout.addWidget(self.next_btn)

        nav_layout.addStretch()

        self.copy_table_btn = QPushButton("📋 Копировать таблицу")
        self.copy_table_btn.setMinimumHeight(35)
        self.copy_table_btn.clicked.connect(self.copy_table_to_clipboard)
        nav_layout.addWidget(self.copy_table_btn)

        layout.addWidget(nav_frame)

        # Пояснения
        explanation_group = QGroupBox("💡 Пояснения")
        explanation_layout = QVBoxLayout()

        self.explanation_text = QTextEdit()
        self.explanation_text.setReadOnly(True)
        self.explanation_text.setMaximumHeight(150)
        self.explanation_text.setMinimumHeight(120)
        explanation_layout.addWidget(self.explanation_text)

        explanation_group.setLayout(explanation_layout)
        layout.addWidget(explanation_group)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def set_iterations(self, iterations: list, mode: str = ""):
        """Установка данных итераций"""
        self.simplex_iterations = iterations if iterations else []

        if not self.simplex_iterations:
            self._show_no_data()
            return

        self.phase1_iterations = [it for it in self.simplex_iterations if it.get('phase') == 1]
        self.phase2_iterations = [it for it in self.simplex_iterations if it.get('phase') == 2]

        self.phase_combo.blockSignals(True)
        self.iteration_combo.blockSignals(True)

        self.phase_combo.clear()
        if self.phase1_iterations:
            self.phase_combo.addItem("Фаза 1 (поиск допустимого базиса)")
        if self.phase2_iterations:
            self.phase_combo.addItem("Фаза 2 (оптимизация)")

        if self.phase1_iterations:
            self.phase_combo.setCurrentIndex(0)
            self._update_iteration_combo()
            self.iteration_combo.setCurrentIndex(len(self.phase1_iterations) - 1)
            self.display_iteration(len(self.phase1_iterations) - 1, 1)
        elif self.phase2_iterations:
            self.phase_combo.setCurrentIndex(0)
            self._update_iteration_combo()
            self.iteration_combo.setCurrentIndex(len(self.phase2_iterations) - 1)
            self.display_iteration(len(self.phase2_iterations) - 1, 2)

        self.phase_combo.blockSignals(False)
        self.iteration_combo.blockSignals(False)
        self._update_nav_buttons()

    def _update_iteration_combo(self):
        """Обновление списка итераций"""
        self.iteration_combo.clear()
        current_phase = self.phase_combo.currentText()

        if "Фаза 1" in current_phase:
            iterations = self.phase1_iterations
        else:
            iterations = self.phase2_iterations

        for i, it in enumerate(iterations):
            self.iteration_combo.addItem(f"Итерация {it.get('iteration', i)}")

    def on_phase_changed(self, idx: int):
        """Смена фазы"""
        if idx >= 0:
            self._update_iteration_combo()
            if self.iteration_combo.count() > 0:
                self.iteration_combo.setCurrentIndex(0)
                phase = 1 if "Фаза 1" in self.phase_combo.currentText() else 2
                self.display_iteration(0, phase)
        self._update_nav_buttons()

    def on_iteration_changed(self, idx: int):
        """Смена итерации"""
        if idx >= 0:
            phase = 1 if "Фаза 1" in self.phase_combo.currentText() else 2
            self.display_iteration(idx, phase)
        self._update_nav_buttons()

    def on_prev_iteration(self):
        """Предыдущая итерация"""
        current_idx = self.iteration_combo.currentIndex()
        if current_idx > 0:
            self.iteration_combo.setCurrentIndex(current_idx - 1)
        elif self.phase_combo.currentIndex() > 0:
            self.phase_combo.setCurrentIndex(0)
            self.iteration_combo.setCurrentIndex(self.iteration_combo.count() - 1)

    def on_next_iteration(self):
        """Следующая итерация"""
        current_idx = self.iteration_combo.currentIndex()
        if current_idx < self.iteration_combo.count() - 1:
            self.iteration_combo.setCurrentIndex(current_idx + 1)
        elif self.phase_combo.currentIndex() < self.phase_combo.count() - 1:
            self.phase_combo.setCurrentIndex(1)
            self.iteration_combo.setCurrentIndex(0)

    def _update_nav_buttons(self):
        """Обновление кнопок навигации"""
        phase_idx = self.phase_combo.currentIndex()
        iter_idx = self.iteration_combo.currentIndex()

        self.prev_btn.setEnabled(iter_idx > 0 or phase_idx > 0)
        self.next_btn.setEnabled(
            iter_idx < self.iteration_combo.count() - 1 or
            phase_idx < self.phase_combo.count() - 1
        )

    def display_iteration(self, iter_idx: int, phase: int):
        """Отображение итерации"""
        if phase == 1:
            if iter_idx >= len(self.phase1_iterations):
                return
            iteration_data = self.phase1_iterations[iter_idx]
        else:
            if iter_idx >= len(self.phase2_iterations):
                return
            iteration_data = self.phase2_iterations[iter_idx]

        entering = iteration_data.get('entering', '')
        leaving = iteration_data.get('leaving', '')
        pivot = iteration_data.get('pivot', (0, 0))
        tableau = iteration_data.get('tableau')

        self.entering_label.setText(entering if entering else "—")
        self.leaving_label.setText(leaving if leaving else "—")

        if pivot and len(pivot) == 2:
            self.pivot_label.setText(f"строка {pivot[0]}, столбец {pivot[1]}")
        else:
            self.pivot_label.setText("—")

        obj_value = iteration_data.get('objective_value')
        if obj_value is not None:
            if phase == 1:
                self.objective_label.setText(f"W = {obj_value:.4f}")
            else:
                self.objective_label.setText(f"Z = {obj_value:.4f}")
        else:
            self.objective_label.setText("—")

        basis = iteration_data.get('basis', [])
        if tableau is not None:
            self._display_tableau(tableau, basis, phase, iter_idx, iteration_data)

        self._generate_explanation(iteration_data, phase, iter_idx)

    def _display_tableau(self, tableau: np.ndarray, basis: list, phase: int,
                         iter_idx: int, iteration_data: dict):
        """Отображение симплекс-таблицы"""
        try:
            m, n = tableau.shape
            n_vars = n - 1

            self.table_widget.setRowCount(m)
            self.table_widget.setColumnCount(n_vars + 2)

            headers = ["Базис"]
            for j in range(n_vars):
                if j < 3:
                    headers.append(f"x_B{j + 1}")
                elif j < 8:
                    headers.append(f"s{j - 2}")
                else:
                    headers.append(f"a{j - 7}")
            headers.append("RHS")
            self.table_widget.setHorizontalHeaderLabels(headers)

            pivot = iteration_data.get('pivot', (-1, -1))

            for i in range(m):
                # Базисная переменная
                if i < m - 1:
                    if i < len(basis):
                        basis_item = QTableWidgetItem(str(basis[i]))
                    else:
                        basis_item = QTableWidgetItem("—")
                    basis_item.setBackground(QBrush(QColor("#F1F8F1")))
                    basis_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_widget.setItem(i, 0, basis_item)
                else:
                    obj_item = QTableWidgetItem("W" if phase == 1 else "Z")
                    obj_item.setBackground(QBrush(QColor("#E8F5E9")))
                    obj_item.setFont(QFont("Segoe UI", weight=QFont.Weight.Bold))
                    obj_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_widget.setItem(i, 0, obj_item)

                for j in range(n):
                    value = tableau[i, j]

                    if abs(value) < 1e-10:
                        display_text = "0"
                    elif abs(value) > 1000:
                        display_text = f"{value:.2f}"
                    elif abs(value) < 0.01:
                        display_text = f"{value:.6f}"
                    else:
                        display_text = f"{value:.4f}"

                    item = QTableWidgetItem(display_text)

                    if i == pivot[0] and j == pivot[1]:
                        item.setBackground(QBrush(QColor("#4CAF50")))
                        item.setForeground(QBrush(Qt.GlobalColor.white))
                        item.setFont(QFont("Segoe UI", weight=QFont.Weight.Bold))
                    elif i == m - 1:
                        item.setBackground(QBrush(QColor("#F9FDF9")))

                    if i == m - 1 and value < -1e-10:
                        item.setForeground(QBrush(QColor("#E74C3C")))

                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table_widget.setItem(i, j + 1, item)

            self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            for j in range(1, n + 1):
                self.table_widget.horizontalHeader().setSectionResizeMode(j, QHeaderView.ResizeMode.ResizeToContents)
                if self.table_widget.columnWidth(j) < 65:
                    self.table_widget.setColumnWidth(j, 65)

        except Exception as e:
            print(f"Ошибка при отображении таблицы: {e}")

    def _generate_explanation(self, iteration_data: dict, phase: int, iter_idx: int):
        """Генерация пояснений"""
        text = ""
        iter_num = iteration_data.get('iteration', iter_idx)
        entering = iteration_data.get('entering', '')
        leaving = iteration_data.get('leaving', '')

        if phase == 1:
            if iter_idx == 0:
                text = "🔵 НАЧАЛО ФАЗЫ 1: Поиск допустимого базиса\n\n"
                text += "Введены искусственные переменные для формирования начального базиса.\n"
                text += "Цель: минимизировать сумму искусственных переменных (W → 0)."
            else:
                text = f"🔄 ИТЕРАЦИЯ {iter_num} ФАЗЫ 1:\n\n"
                text += f"• В базис вводится {entering}\n"
                text += f"• Из базиса выводится {leaving}\n"
                text += f"• Выполнено жорданово исключение"

                obj_value = iteration_data.get('objective_value')
                if obj_value is not None and abs(obj_value) < 1e-8:
                    text += "\n\n✅ ФАЗА 1 ЗАВЕРШЕНА: Допустимый базис найден!"
        else:
            if iter_idx == 0:
                text = "🟢 НАЧАЛО ФАЗЫ 2: Оптимизация целевой функции\n\n"
                text += "Искусственные переменные удалены.\n"
                text += "Цель: минимизировать затраты на корма."
            else:
                text = f"🔄 ИТЕРАЦИЯ {iter_num} ФАЗЫ 2:\n\n"
                text += f"• В базис вводится {entering}\n"
                text += f"• Из базиса выводится {leaving}\n"
                text += f"• Выполнено жорданово исключение"

        self.explanation_text.setText(text)

    def copy_table_to_clipboard(self):
        """Копирование таблицы в буфер обмена"""
        if self.table_widget.rowCount() == 0:
            QMessageBox.information(self, "Информация", "Нет данных для копирования")
            return

        text = ""
        headers = []
        for j in range(self.table_widget.columnCount()):
            headers.append(self.table_widget.horizontalHeaderItem(j).text())
        text += "\t".join(headers) + "\n"

        for i in range(self.table_widget.rowCount()):
            row_data = []
            for j in range(self.table_widget.columnCount()):
                item = self.table_widget.item(i, j)
                row_data.append(item.text() if item else "")
            text += "\t".join(row_data) + "\n"

        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Успешно", "Таблица скопирована в буфер обмена")

    def show_all_iterations(self):
        """Показать сводку всех итераций"""
        if not self.simplex_iterations:
            QMessageBox.information(self, "Информация", "Нет данных об итерациях")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Сводка всех итераций симплекс-метода")
        dialog.resize(700, 500)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 10))

        text = "📐 СВОДКА ВСЕХ ИТЕРАЦИЙ СИМПЛЕКС-МЕТОДА\n"
        text += "=" * 60 + "\n\n"

        if self.phase1_iterations:
            text += "ФАЗА 1 (поиск допустимого базиса):\n"
            text += "-" * 40 + "\n"
            for it in self.phase1_iterations:
                iter_num = it.get('iteration', 0)
                entering = it.get('entering', '')
                leaving = it.get('leaving', '')
                obj = it.get('objective_value', 0)

                if iter_num == 0:
                    text += f"  Начало: W = {obj:.4f}\n"
                else:
                    text += f"  Итер. {iter_num}: ввод {entering:6s}, вывод {leaving:6s}, W = {obj:.4f}\n"
            text += f"\n  Всего итераций в Фазе 1: {len(self.phase1_iterations)}\n"

        if self.phase2_iterations:
            text += "\nФАЗА 2 (оптимизация):\n"
            text += "-" * 40 + "\n"
            for it in self.phase2_iterations:
                iter_num = it.get('iteration', 0)
                entering = it.get('entering', '')
                leaving = it.get('leaving', '')
                obj = it.get('objective_value', 0)

                if iter_num == 0:
                    text += f"  Начало: Z = {abs(obj):.4f}\n"
                else:
                    text += f"  Итер. {iter_num}: ввод {entering:6s}, вывод {leaving:6s}, Z = {abs(obj):.4f}\n"
            text += f"\n  Всего итераций в Фазе 2: {len(self.phase2_iterations)}\n"

        if self.phase2_iterations:
            final_obj = self.phase2_iterations[-1].get('objective_value', 0)
            text += f"\n✅ ОПТИМАЛЬНОЕ РЕШЕНИЕ: Z = {abs(final_obj):.4f} тыс. руб\n"

        text_edit.setText(text)
        layout.addWidget(text_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn_box.accepted.connect(dialog.accept)
        copy_btn = QPushButton("📋 Копировать")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(text))
        btn_box.addButton(copy_btn, QDialogButtonBox.ButtonRole.ActionRole)
        layout.addWidget(btn_box)

        dialog.exec()

    def _show_no_data(self):
        """Отображение при отсутствии данных"""
        self.entering_label.setText("—")
        self.leaving_label.setText("—")
        self.objective_label.setText("—")
        self.pivot_label.setText("—")
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(1)
        self.table_widget.setHorizontalHeaderLabels(["Нет данных"])
        self.explanation_text.setText(
            "Нет данных о симплекс-итерациях.\n\n"
            "Выполните расчет для просмотра пошагового решения."
        )
        self.phase_combo.setEnabled(False)
        self.iteration_combo.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)