# views/analysis_tab.py
"""
Модуль вкладки анализа
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pandas as pd
import traceback


class AnalysisTab(QWidget):
    """Вкладка для детального анализа результатов"""

    def __init__(self):
        super().__init__()
        self.current_solution = None
        self.nutrients_df = None
        self.allocation_df = None
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса вкладки"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("Детальный анализ")
        title_label.setProperty("role", "heading")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Информация о решении
        info_group = QGroupBox("ℹ️ Информация о решении")
        info_layout = QGridLayout()

        info_layout.addWidget(QLabel("Статус:"), 0, 0)
        self.status_label = QLabel("—")
        info_layout.addWidget(self.status_label, 0, 1)

        info_layout.addWidget(QLabel("Метод:"), 1, 0)
        self.method_label = QLabel("Симплекс-метод")
        info_layout.addWidget(self.method_label, 1, 1)

        info_layout.addWidget(QLabel("Сообщение:"), 2, 0)
        self.message_label = QLabel("—")
        self.message_label.setWordWrap(True)
        info_layout.addWidget(self.message_label, 2, 1)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Анализ питательных веществ
        nutrients_group = QGroupBox("🔬 Проверка норм питательных веществ")
        nutrients_layout = QVBoxLayout()

        self.nutrients_table = QTableWidget()
        self.nutrients_table.setColumnCount(4)
        self.nutrients_table.setHorizontalHeaderLabels(
            ["Вещество", "Факт (кг)", "Норма (кг)", "Статус"]
        )
        self.nutrients_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        nutrients_layout.addWidget(self.nutrients_table)

        nutrients_group.setLayout(nutrients_layout)
        layout.addWidget(nutrients_group)

        # Выводы
        conclusions_group = QGroupBox("💡 Выводы и рекомендации")
        conclusions_layout = QVBoxLayout()

        self.conclusions_text = QTextEdit()
        self.conclusions_text.setReadOnly(True)
        self.conclusions_text.setMaximumHeight(200)
        conclusions_layout.addWidget(self.conclusions_text)

        conclusions_group.setLayout(conclusions_layout)
        layout.addWidget(conclusions_group)

        self.setLayout(layout)

    def set_data(self, solution: dict, nutrients_df: pd.DataFrame, allocation_df: pd.DataFrame):
        """Установка данных для анализа"""
        try:
            self.current_solution = solution
            self.nutrients_df = nutrients_df
            self.allocation_df = allocation_df
            self.update_display()
        except Exception as e:
            print(f"❌ ОШИБКА В SET_DATA: {e}")
            traceback.print_exc()

    def update_display(self):
        """Обновление отображения"""
        try:
            if not self.current_solution:
                return

            success = self.current_solution.get('success', False)
            self.status_label.setText("✅ Успешно" if success else "❌ Ошибка")
            self.message_label.setText(self.current_solution.get('message', '—'))

            # Таблица питательных веществ
            if self.nutrients_df is not None and not self.nutrients_df.empty:
                self.nutrients_table.setRowCount(len(self.nutrients_df))
                for i in range(len(self.nutrients_df)):
                    row = self.nutrients_df.iloc[i]

                    self.nutrients_table.setItem(i, 0, QTableWidgetItem(str(row.get('Вещество', ''))))
                    self.nutrients_table.setItem(i, 1, QTableWidgetItem(f"{row.get('Факт (кг)', 0):.3f}"))
                    self.nutrients_table.setItem(i, 2, QTableWidgetItem(str(row.get('Норма (кг)', ''))))

                    status_item = QTableWidgetItem(str(row.get('Статус', '')))
                    if row.get('Статус') == 'НАРУШЕНИЕ':
                        status_item.setForeground(QBrush(Qt.GlobalColor.red))
                    else:
                        status_item.setForeground(QBrush(Qt.GlobalColor.darkGreen))
                    self.nutrients_table.setItem(i, 3, status_item)

            # Выводы
            self._generate_conclusions()

        except Exception as e:
            print(f"❌ ОШИБКА В UPDATE_DISPLAY: {e}")
            traceback.print_exc()

    def _generate_conclusions(self):
        """Формирование выводов"""
        if not self.current_solution or not self.current_solution.get('success'):
            self.conclusions_text.setText("❌ Нет данных для формирования выводов")
            return

        text = "📊 РЕЗУЛЬТАТЫ ОПТИМИЗАЦИИ\n"
        text += "=" * 50 + "\n\n"

        x = self.current_solution.get('x', [])
        feeds = self.current_solution.get('feeds', [])
        cost = self.current_solution.get('fun', 0)

        text += f"💰 Минимальные затраты: {cost:.2f} тыс. руб\n\n"

        text += "📋 ОПТИМАЛЬНЫЙ РАЦИОН:\n"
        text += "-" * 30 + "\n"
        for i, feed in enumerate(feeds):
            if i < len(x) and x[i] > 1e-6:
                text += f"• Корм {feed['name']}: {x[i]:.4f} т "
                text += f"(стоимость: {x[i] * feed['price']:.2f} тыс. руб)\n"

        text += f"\n• Общее количество: {sum(x):.4f} т\n"
        text += f"• Корма B2: {x[1]:.4f} т\n\n"

        # Ответы на вопросы
        text += "❓ ОТВЕТЫ НА ВОПРОСЫ:\n"
        text += "-" * 30 + "\n"
        text += f"1. Количество корма B2: {x[1]:.4f} тонн\n"
        text += f"2. Общее количество кормов: {sum(x):.4f} тонн\n"
        text += f"3. Минимальные затраты: {cost:.2f} тыс. руб\n"

        self.conclusions_text.setText(text)