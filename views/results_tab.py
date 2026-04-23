# views/results_tab.py
"""
Модуль вкладки отображения результатов
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pandas as pd
import traceback
import numpy as np


class ResultsTab(QWidget):
    """
    Вкладка для отображения результатов оптимизации
    """

    def __init__(self):
        super().__init__()
        self.current_solution = None
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса вкладки"""
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

        # Заголовок
        title_label = QLabel("Результаты оптимизации кормового рациона")
        title_label.setProperty("role", "heading")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Группа основных показателей
        summary_group = QGroupBox("📈 Основные показатели")
        summary_layout = QGridLayout()
        summary_layout.setVerticalSpacing(15)
        summary_layout.setHorizontalSpacing(20)

        # Минимальные затраты
        self.cost_label = QLabel("—")
        self.cost_label.setStyleSheet("font-size: 20pt; font-weight: bold; color: #2E7D32;")
        self.cost_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Количество B2
        self.b2_label = QLabel("—")
        self.b2_label.setStyleSheet("font-size: 20pt; font-weight: bold; color: #2E7D32;")
        self.b2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Общее количество кормов
        self.total_label = QLabel("—")
        self.total_label.setStyleSheet("font-size: 20pt; font-weight: bold; color: #2E7D32;")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        summary_layout.addWidget(QLabel("Минимальные затраты:"), 0, 0)
        summary_layout.addWidget(self.cost_label, 0, 1)
        summary_layout.addWidget(QLabel("тыс. руб"), 0, 2)

        summary_layout.addWidget(QLabel("Количество корма B2:"), 1, 0)
        summary_layout.addWidget(self.b2_label, 1, 1)
        summary_layout.addWidget(QLabel("тонн"), 1, 2)

        summary_layout.addWidget(QLabel("Общее количество кормов:"), 2, 0)
        summary_layout.addWidget(self.total_label, 2, 1)
        summary_layout.addWidget(QLabel("тонн"), 2, 2)

        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Группа распределения кормов
        allocation_group = QGroupBox("🌾 Распределение кормов")
        allocation_layout = QVBoxLayout()

        table_scroll = QScrollArea()
        table_scroll.setWidgetResizable(True)
        table_scroll.setMinimumHeight(200)

        self.allocation_table = QTableWidget()
        self.allocation_table.setColumnCount(4)
        self.allocation_table.setHorizontalHeaderLabels(
            ["Вид корма", "Количество (т)", "Цена (тыс. руб/т)", "Стоимость (тыс. руб)"]
        )
        self.allocation_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.allocation_table.setAlternatingRowColors(True)
        self.allocation_table.verticalHeader().setDefaultSectionSize(35)

        table_scroll.setWidget(self.allocation_table)
        allocation_layout.addWidget(table_scroll)

        allocation_group.setLayout(allocation_layout)
        layout.addWidget(allocation_group)

        # Группа анализа питательных веществ
        nutrients_group = QGroupBox("🔬 Содержание питательных веществ")
        nutrients_layout = QVBoxLayout()

        self.nutrients_text = QTextEdit()
        self.nutrients_text.setReadOnly(True)
        self.nutrients_text.setMinimumHeight(250)
        self.nutrients_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
                background-color: #F8FAFE;
                border: 1px solid #C8E6C9;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        nutrients_layout.addWidget(self.nutrients_text)

        nutrients_group.setLayout(nutrients_layout)
        layout.addWidget(nutrients_group)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def format_number(self, value):
        """Форматирование числа"""
        try:
            if value is None:
                return "0.00"
            num_value = float(value)
            return f"{num_value:,.4f}".replace(",", " ")
        except (ValueError, TypeError):
            return str(value)

    def display_results(self, solution: dict, nutrients_df: pd.DataFrame, allocation_df: pd.DataFrame):
        """Отображение результатов"""
        try:
            print("\n=== DISPLAY RESULTS ===")
            self.current_solution = solution

            if not solution or not solution.get('success', False):
                self.cost_label.setText("—")
                self.b2_label.setText("—")
                self.total_label.setText("—")
                self.nutrients_text.setText(
                    f"❌ Решение не найдено\n\n{solution.get('message', '') if solution else ''}")
                self.allocation_table.setRowCount(0)
                return

            # Основные показатели
            cost = solution.get('fun', 0)
            x = solution.get('x', [])
            feeds = solution.get('feeds', [])

            self.cost_label.setText(self.format_number(cost))

            # Количество B2 (индекс 1)
            b2_quantity = x[1] if len(x) > 1 else 0
            self.b2_label.setText(self.format_number(b2_quantity))

            # Общее количество кормов
            total_quantity = sum(x)
            self.total_label.setText(self.format_number(total_quantity))

            # Таблица распределения
            if allocation_df is not None and not allocation_df.empty:
                self.allocation_table.setRowCount(len(allocation_df))
                for i in range(len(allocation_df)):
                    row = allocation_df.iloc[i]

                    self.allocation_table.setItem(i, 0, QTableWidgetItem(str(row.get('Вид корма', ''))))

                    qty = row.get('Количество (т)', 0)
                    item = QTableWidgetItem(self.format_number(qty))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.allocation_table.setItem(i, 1, item)

                    price = row.get('Цена (тыс. руб/т)', 0)
                    item = QTableWidgetItem(str(price))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.allocation_table.setItem(i, 2, item)

                    cost_item = row.get('Стоимость (тыс. руб)', 0)
                    item = QTableWidgetItem(self.format_number(cost_item))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.allocation_table.setItem(i, 3, item)
            else:
                self.allocation_table.setRowCount(0)

            # Анализ питательных веществ
            self._generate_nutrients_analysis(solution, nutrients_df)

            print("=== DISPLAY RESULTS FINISHED ===\n")

        except Exception as e:
            print(f"❌ ОШИБКА В DISPLAY_RESULTS: {e}")
            traceback.print_exc()

    def _generate_nutrients_analysis(self, solution: dict, nutrients_df: pd.DataFrame):
        """Генерация анализа питательных веществ"""
        text = ""
        text += "📊 АНАЛИЗ СОДЕРЖАНИЯ ПИТАТЕЛЬНЫХ ВЕЩЕСТВ\n"
        text += "=" * 70 + "\n\n"

        # Основные результаты
        cost = solution.get('fun', 0)
        x = solution.get('x', [])

        text += f"💰 Минимальные затраты на корма: {self.format_number(cost)} тыс. руб\n\n"

        text += "📋 ОПТИМАЛЬНЫЙ РАЦИОН:\n"
        text += "-" * 50 + "\n"

        feeds = solution.get('feeds', [])
        for i, feed in enumerate(feeds):
            if i < len(x) and x[i] > 1e-6:
                text += f"• Корм {feed['name']}: {self.format_number(x[i])} тонн"
                text += f" (стоимость: {self.format_number(x[i] * feed['price'])} тыс. руб)\n"

        text += f"\n• Общее количество кормов: {self.format_number(sum(x))} тонн\n"
        text += f"• Количество корма B2: {self.format_number(x[1])} тонн\n\n"

        # Проверка питательных веществ
        text += "🔬 ПРОВЕРКА ПИТАТЕЛЬНЫХ ВЕЩЕСТВ:\n"
        text += "-" * 50 + "\n"

        if nutrients_df is not None and not nutrients_df.empty:
            for _, row in nutrients_df.iterrows():
                nutrient = row.get('Вещество', '')
                actual = row.get('Факт (кг)', 0)
                norm = row.get('Норма (кг)', '')
                status = row.get('Статус', '')

                emoji = "✅" if status == 'OK' else "❌"
                text += f"{emoji} {nutrient}: фактически {actual:.3f} кг, норма {norm}\n"
        else:
            text += "Нет данных для проверки\n"

        # Ответы на вопросы задания
        text += "\n❓ ОТВЕТЫ НА ВОПРОСЫ ЗАДАНИЯ\n"
        text += "-" * 50 + "\n"

        if solution.get('success'):
            text += f"1. Количество корма B2: {self.format_number(x[1])} тонн\n"
            text += f"2. Общее количество кормов: {self.format_number(sum(x))} тонн\n"
            text += f"3. Минимальные затраты: {self.format_number(cost)} тыс. руб\n"

        self.nutrients_text.setText(text)

    def clear(self):
        """Очистка результатов"""
        self.cost_label.setText("—")
        self.b2_label.setText("—")
        self.total_label.setText("—")
        self.allocation_table.setRowCount(0)
        self.nutrients_text.clear()
        self.current_solution = None