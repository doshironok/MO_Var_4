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
        """Инициализация интерфейса с увеличенными полями"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Главный сплиттер для разделения таблицы и пояснений
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # === Верхняя часть: управление + информация + таблица ===
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setSpacing(8)
        top_layout.setContentsMargins(10, 10, 10, 5)

        # Заголовок
        title = QLabel("📐 Симплекс-метод: пошаговое решение")
        title.setProperty("role", "heading")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(title)

        # Управление (компактное)
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background-color: #F1F8F1;
                border: 1px solid #C8E6C9;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        ctrl = QHBoxLayout(control_frame)
        ctrl.setSpacing(10)
        ctrl.setContentsMargins(8, 4, 8, 4)

        ctrl.addWidget(QLabel("Фаза:"))
        self.phase_combo = QComboBox()
        self.phase_combo.setMinimumWidth(220)
        self.phase_combo.currentIndexChanged.connect(self.on_phase_changed)
        ctrl.addWidget(self.phase_combo)

        ctrl.addWidget(QLabel("Итерация:"))
        self.iter_combo = QComboBox()
        self.iter_combo.setMinimumWidth(130)
        self.iter_combo.currentIndexChanged.connect(self.on_iter_changed)
        ctrl.addWidget(self.iter_combo)

        ctrl.addStretch()

        self.show_all_btn = QPushButton("📋 Все итерации")
        self.show_all_btn.clicked.connect(self.show_all)
        ctrl.addWidget(self.show_all_btn)

        top_layout.addWidget(control_frame)

        # Информация об итерации (компактная)
        info_group = QGroupBox("📊 Текущая итерация")
        info_layout = QGridLayout()
        info_layout.setSpacing(5)
        info_layout.setContentsMargins(8, 8, 8, 8)

        info_layout.addWidget(QLabel("Вводимая:"), 0, 0)
        self.entering_lbl = QLabel("—")
        self.entering_lbl.setStyleSheet("font-weight: bold; color: #4CAF50;")
        info_layout.addWidget(self.entering_lbl, 0, 1)

        info_layout.addWidget(QLabel("Выводимая:"), 0, 2)
        self.leaving_lbl = QLabel("—")
        self.leaving_lbl.setStyleSheet("font-weight: bold; color: #E74C3C;")
        info_layout.addWidget(self.leaving_lbl, 0, 3)

        info_layout.addWidget(QLabel("Целевая функция:"), 1, 0)
        self.obj_lbl = QLabel("—")
        self.obj_lbl.setStyleSheet("font-weight: bold; color: #2E7D32;")
        info_layout.addWidget(self.obj_lbl, 1, 1)

        info_layout.addWidget(QLabel("Ведущий элемент:"), 1, 2)
        self.pivot_lbl = QLabel("—")
        self.pivot_lbl.setStyleSheet("font-weight: bold; color: #FF9800;")
        info_layout.addWidget(self.pivot_lbl, 1, 3)

        info_group.setLayout(info_layout)
        top_layout.addWidget(info_group)

        # Симплекс-таблица (с прокруткой)
        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setMinimumHeight(250)
        self.table_widget.setStyleSheet("""
            QTableWidget {
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #E8F5E9;
                padding: 4px;
                font-weight: bold;
                font-size: 9pt;
            }
        """)
        top_layout.addWidget(self.table_widget, 1)  # stretch factor 1

        # Навигация
        nav = QHBoxLayout()
        nav.setSpacing(8)
        self.prev_btn = QPushButton("◀ Предыдущая")
        self.prev_btn.clicked.connect(self.on_prev)
        nav.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Следующая ▶")
        self.next_btn.clicked.connect(self.on_next)
        nav.addWidget(self.next_btn)

        nav.addStretch()

        copy_btn = QPushButton("📋 Копировать таблицу")
        copy_btn.clicked.connect(self.copy_table)
        nav.addWidget(copy_btn)

        top_layout.addLayout(nav)

        # === Нижняя часть: пояснения ===
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setSpacing(5)
        bottom_layout.setContentsMargins(10, 5, 10, 10)

        expl_group = QGroupBox("💡 Пояснения и вычисления")
        expl_inner = QVBoxLayout()
        expl_inner.setContentsMargins(5, 5, 5, 5)

        self.expl_text = QTextEdit()
        self.expl_text.setReadOnly(True)
        self.expl_text.setMinimumHeight(200)
        self.expl_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Segoe UI', 'Consolas', monospace;
                font-size: 10pt;
                background-color: #FAFDFA;
                border: 1px solid #C8E6C9;
                border-radius: 4px;
                padding: 10px;
                line-height: 1.6;
            }
        """)
        expl_inner.addWidget(self.expl_text)

        expl_group.setLayout(expl_inner)
        bottom_layout.addWidget(expl_group)

        # Добавляем в сплиттер
        main_splitter.addWidget(top_widget)
        main_splitter.addWidget(bottom_widget)
        main_splitter.setStretchFactor(0, 3)  # таблица — 3 части
        main_splitter.setStretchFactor(1, 2)  # пояснения — 2 части

        main_layout.addWidget(main_splitter)
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
        """Отображение симплекс-таблицы с выделением ведущей строки и столбца"""
        m, n = tableau.shape
        n_vars = n - 1

        # Блокируем сигналы на время обновления
        self.table_widget.blockSignals(True)
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(0)

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

        # Подсветка заголовка ведущего столбца
        if pivot[1] >= 0 and pivot[1] < n_vars:
            header_item = QTableWidgetItem(headers[pivot[1] + 1])
            header_item.setBackground(QBrush(QColor("#FFE0B2")))
            self.table_widget.setHorizontalHeaderItem(pivot[1] + 1, header_item)

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

            # Подсветка строки целевой функции
            if i == m - 1:
                item.setBackground(QBrush(QColor("#E8F5E9")))
                f = item.font()
                f.setBold(True)
                item.setFont(f)
            # Подсветка выводимой строки
            elif i == pivot[0] and pivot[0] >= 0:
                item.setBackground(QBrush(QColor("#FFCDD2")))
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

                # Подсветка ведущего столбца
                if j == pivot[1] and pivot[1] >= 0:
                    item.setBackground(QBrush(QColor("#FFF3E0")))

                # Подсветка ведущей строки (поверх столбца)
                if i == pivot[0] and pivot[0] >= 0:
                    item.setBackground(QBrush(QColor("#FFEBEE")))

                # Подсветка ведущего элемента (поверх всего)
                if i == pivot[0] and j == pivot[1] and pivot[0] >= 0:
                    item.setBackground(QBrush(QColor("#4CAF50")))
                    item.setForeground(QBrush(Qt.GlobalColor.white))
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)

                # Подсветка положительных коэффициентов в Z/W
                if i == m - 1 and val > 1e-10:
                    item.setForeground(QBrush(QColor("#E74C3C")))

                self.table_widget.setItem(i, j + 1, item)

        self.table_widget.resizeColumnsToContents()
        self.table_widget.blockSignals(False)

    def _show_explanation(self, it: dict, phase: int, idx: int):
        """Пояснения к итерации с полными вычислениями"""
        entering = it.get('entering', '')
        leaving = it.get('leaving', '')
        tableau = it.get('tableau')
        pivot = it.get('pivot', (-1, -1))
        basis = it.get('basis', [])
        col_labels = it.get('col_labels', [])
        obj_value = it.get('objective_value')

        if tableau is None:
            self.expl_text.setText("Нет данных")
            return

        m, n = tableau.shape
        n_vars = n - 1

        text = ""

        # === Начальные итерации ===
        if idx == 0:
            if phase == 1:
                text += "🔵 НАЧАЛО ФАЗЫ 1: Поиск допустимого базиса\n"
                text += "═" * 60 + "\n\n"
                text += "📌 Цель фазы 1:\n"
                text += "   Минимизировать сумму искусственных переменных:\n"
                text += "   W = a₁ + a₂ + ... + aₘ → 0\n\n"
                text += "📌 Начальный базис:\n"
                text += "   Все искусственные переменные a₁, a₂, ..., aₘ\n\n"
                text += "📌 Строка W построена как:\n"
                text += "   W = Σ aᵢ, затем выражена через небазисные переменные\n"
                text += "   путём вычитания всех строк ограничений\n\n"
                text += "📌 Критерий оптимальности Фазы 1:\n"
                text += "   Все коэффициенты в W ≤ 0 (W = 0)\n"
                text += "   Если W > 0 — допустимого решения нет"
            else:
                text += "🟢 НАЧАЛО ФАЗЫ 2: Оптимизация целевой функции\n"
                text += "═" * 60 + "\n\n"
                text += "📌 Цель фазы 2:\n"
                text += "   Минимизировать Z = c₁x₁ + c₂x₂ + ... + cₙxₙ\n\n"
                text += "📌 Подготовка:\n"
                text += "   • Искусственные переменные удалены (W = 0)\n"
                text += "   • Восстановлена исходная целевая функция Z\n"
                text += "   • Коэффициенты при базисных переменных обнулены\n\n"
                text += "📌 Критерий оптимальности Фазы 2:\n"
                text += "   Все коэффициенты в Z ≤ 0 (нет переменных,\n"
                text += "   ввод которых уменьшит Z)\n\n"
                text += "📌 Текущий базис:\n"
                if basis:
                    for i, b in enumerate(basis):
                        if i < m - 1 and i < len(basis):
                            text += f"   Строка {i}: {b}"
                            if i < tableau.shape[0] - 1:
                                text += f" = {tableau[i, -1]:.6f}"
                            text += "\n"
                text += f"\n📌 Значение Z: {obj_value:.6f}" if obj_value is not None else ""

        # === Промежуточные итерации ===
        else:
            if phase == 1:
                text += f"🔄 ФАЗА 1 — ИТЕРАЦИЯ {idx}\n"
                text += "═" * 60 + "\n\n"
            else:
                text += f"🔄 ФАЗА 2 — ИТЕРАЦИЯ {idx}\n"
                text += "═" * 60 + "\n\n"

            # ----- Шаг 1: Выбор вводимой переменной -----
            text += "📌 ШАГ 1: Выбор вводимой переменной\n"
            text += "─" * 50 + "\n"

            obj_row = tableau[-1, :-1]
            obj_name = "W" if phase == 1 else "Z"

            pos_coeffs = []
            for j in range(n_vars):
                if obj_row[j] > 1e-10:
                    label = col_labels[j] if j < len(col_labels) else f"x{j + 1}"
                    pos_coeffs.append((label, j, obj_row[j]))

            if pos_coeffs:
                text += f"   В строке {obj_name} найдены положительные коэффициенты:\n\n"
                for label, j, coeff in pos_coeffs:
                    text += f"      {label}: {coeff:+.4f}\n"

                pos_coeffs.sort(key=lambda x: x[2], reverse=True)
                text += f"\n   ▶ Выбран наибольший: {pos_coeffs[0][0]} = {pos_coeffs[0][2]:.4f}\n"
                text += f"   ▶ Вводимая переменная: {entering}\n\n"

                # Пояснение выбора
                text += f"   Обоснование: ввод {entering} в базис даёт наибольшее\n"
                text += f"   уменьшение {obj_name} на единицу переменной.\n"
            else:
                text += f"   В строке {obj_name} нет положительных коэффициентов\n"
                text += f"   ▶ Критерий оптимальности выполнен\n"

            # ----- Шаг 2: Выбор выводимой переменной -----
            text += f"\n📌 ШАГ 2: Выбор выводимой переменной\n"
            text += "─" * 50 + "\n"

            if pivot[1] >= 0 and pivot[1] < n_vars:
                text += f"   Для столбца {entering} вычисляем отношения θ = RHS / aᵢⱼ\n"
                text += f"   (рассматриваются только строки с aᵢⱼ > 0)\n\n"
                text += f"   {'Строка':<8s} {'Базис':<10s} {'aᵢⱼ':>10s} {'RHS':>12s} {'θ = RHS/aᵢⱼ':>16s}\n"
                text += f"   {'─' * 8:<8s} {'─' * 10:<10s} {'─' * 10:<10s} {'─' * 12:<12s} {'─' * 16:<16s}\n"

                ratios = []
                for i in range(m - 1):
                    a_ij = tableau[i, pivot[1]]
                    rhs = tableau[i, -1]
                    row_basis = basis[i] if i < len(basis) else "?"

                    if a_ij > 1e-10:
                        ratio = rhs / a_ij
                        ratios.append((i, row_basis, a_ij, rhs, ratio))
                        text += f"   {i:<8d} {row_basis:<10s} {a_ij:>10.4f} {rhs:>12.4f} {ratio:>16.4f}\n"
                    else:
                        text += f"   {i:<8d} {row_basis:<10s} {a_ij:>10.4f} {rhs:>12.4f} {'— (aᵢⱼ ≤ 0)':>16s}\n"

                if ratios:
                    ratios.sort(key=lambda x: x[4])
                    text += f"\n   ▶ Минимальное отношение θ = {ratios[0][4]:.4f}\n"
                    text += f"   ▶ Выводимая переменная: {leaving} (строка {ratios[0][0]})\n\n"

                    # Пояснение выбора
                    text += f"   Обоснование: правило минимального отношения гарантирует,\n"
                    text += f"   что новая базисная переменная не нарушит условие\n"
                    text += f"   неотрицательности правых частей.\n"
            else:
                text += f"   Нет данных о ведущем столбце\n"

            # ----- Шаг 3: Жорданово исключение -----
            if pivot[0] >= 0 and pivot[1] >= 0:
                text += f"\n📌 ШАГ 3: Жорданово исключение\n"
                text += "─" * 50 + "\n"

                tableau_before = it.get('tableau_before')
                pivot_val_before = it.get('pivot_val_before', tableau[pivot[0], pivot[1]])

                text += f"   Ведущий элемент: a[{pivot[0]},{pivot[1]}] = {pivot_val_before:.6f}\n\n"

                # ========== ДЕЙСТВИЕ 1 ==========
                text += f"   ▸ ДЕЙСТВИЕ 1: Нормализация ведущей строки {pivot[0]}\n"
                text += f"     Делим строку {pivot[0]} на {pivot_val_before:.6f}\n\n"

                if tableau_before is not None:
                    leading_before = tableau_before[pivot[0]]
                    text += "     Строка ДО деления:\n     "
                    parts = []
                    for j in range(n_vars):
                        if abs(leading_before[j]) > 1e-10:
                            label = col_labels[j] if j < len(col_labels) else f"x{j + 1}"
                            parts.append(f"{leading_before[j]:+.4f}·{label}")
                    text += " + ".join(parts) if parts else "0"
                    text += f" = {leading_before[-1]:.6f}\n\n"

                text += "     Строка ПОСЛЕ деления:\n     "
                parts = []
                for j in range(n_vars):
                    new_val = tableau[pivot[0], j]
                    if abs(new_val) > 1e-10:
                        label = col_labels[j] if j < len(col_labels) else f"x{j + 1}"
                        if abs(new_val - 1.0) < 1e-10:
                            parts.append(f"{label}")
                        elif abs(new_val + 1.0) < 1e-10:
                            parts.append(f"-{label}")
                        else:
                            parts.append(f"{new_val:+.4f}·{label}")
                text += " + ".join(parts) if parts else "0"
                text += f" = {tableau[pivot[0], -1]:.6f}\n\n"

                # ========== ДЕЙСТВИЕ 2 ==========
                text += f"   ▸ ДЕЙСТВИЕ 2: Обнуление столбца '{entering}' во ВСЕХ остальных строках\n"
                text += f"     Формула: новая_строка = старая_строка − a[i,{pivot[1]}] × ведущая_строка\n\n"

                for i in range(m):
                    if i == pivot[0]:
                        continue

                    # Получаем коэффициент из СТАРОЙ таблицы
                    if tableau_before is not None:
                        factor = tableau_before[i, pivot[1]]
                    else:
                        factor = tableau[i, pivot[1]]

                    if abs(factor) < 1e-12:
                        continue

                    row_label = basis[i] if i < len(basis) else f"Стр{i}"
                    if i == m - 1:
                        row_label = obj_name

                    text += f"     {'─' * 50}\n"
                    text += f"     СТРОКА {i} ({row_label}):\n"
                    text += f"     Множитель a[{i},{pivot[1]}] = {factor:+.6f}\n\n"

                    if tableau_before is not None:
                        # Строка ДО
                        text += "     Строка ДО преобразования:\n     "
                        parts = []
                        for j in range(n_vars):
                            if abs(tableau_before[i, j]) > 1e-10:
                                label = col_labels[j] if j < len(col_labels) else f"x{j + 1}"
                                parts.append(f"{tableau_before[i, j]:+.4f}·{label}")
                        text += " + ".join(parts) if parts else "0"
                        text += f" = {tableau_before[i, -1]:.6f}\n\n"

                        # Вычисления для КАЖДОГО столбца
                        text += "     Вычисления по столбцам:\n"
                        for j in range(n_vars):
                            old_val = tableau_before[i, j]
                            lead_val = leading_before[j] / pivot_val_before if abs(pivot_val_before) > 1e-12 else 0
                            new_val = tableau[i, j]
                            if abs(old_val) > 1e-10 or abs(new_val) > 1e-10:
                                label = col_labels[j] if j < len(col_labels) else f"x{j + 1}"
                                text += f"       {label:>6s}: {old_val:>10.6f} − ({factor:+.6f}) × ({lead_val:+.6f}) = {new_val:>10.6f}\n"

                        # RHS
                        old_rhs = tableau_before[i, -1]
                        lead_rhs = leading_before[-1] / pivot_val_before if abs(pivot_val_before) > 1e-12 else 0
                        new_rhs = tableau[i, -1]
                        text += f"       {'RHS':>6s}: {old_rhs:>10.6f} − ({factor:+.6f}) × ({lead_rhs:+.6f}) = {new_rhs:>10.6f}\n"

                    # Строка ПОСЛЕ
                    text += "\n     Строка ПОСЛЕ преобразования:\n     "
                    parts = []
                    for j in range(n_vars):
                        new_val = tableau[i, j]
                        if abs(new_val) > 1e-10:
                            label = col_labels[j] if j < len(col_labels) else f"x{j + 1}"
                            if abs(new_val - 1.0) < 1e-10:
                                parts.append(f"{label}")
                            elif abs(new_val + 1.0) < 1e-10:
                                parts.append(f"-{label}")
                            else:
                                parts.append(f"{new_val:+.4f}·{label}")
                    text += " + ".join(parts) if parts else "0"
                    text += f" = {tableau[i, -1]:.6f}\n\n"

            # ----- Шаг 4: Результат -----
            text += f"📌 РЕЗУЛЬТАТ ИТЕРАЦИИ {idx}\n"
            text += "─" * 50 + "\n"

            if obj_value is not None:
                if phase == 1:
                    text += f"   W = {obj_value:.6f}\n"
                    if abs(obj_value) < 1e-8:
                        text += "   ✅ Все искусственные переменные выведены (W = 0)\n"
                        text += "   ✅ Фаза 1 завершена — получен допустимый базис\n"
                    else:
                        remaining_art = sum(1 for b in basis if 'a' in str(b))
                        text += f"   ⏳ Осталось вывести искусственных переменных: {remaining_art}\n"
                else:
                    text += f"   Z = {obj_value:.6f}\n"
                    remaining_pos = sum(1 for j in range(n_vars) if tableau[-1, j] > 1e-10)
                    if remaining_pos == 0:
                        text += "   ✅ Все коэффициенты в Z ≤ 0\n"
                        text += "   ✅ Оптимальное решение найдено\n"
                    else:
                        text += f"   ⏳ Осталось положительных коэффициентов в Z: {remaining_pos}\n"
                text += "\n"

            if basis:
                text += f"   Текущий базис:\n"
                for i, b in enumerate(basis):
                    if i < m - 1:
                        text += f"   • {b} = {tableau[i, -1]:.6f}\n"

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