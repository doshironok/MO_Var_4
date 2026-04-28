# views/input_tab.py (исправленный)
"""
Модуль вкладки ввода данных
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from utils.constants import FEEDS, NUTRIENT_REQUIREMENTS


class InputTab(QWidget):
    """Вкладка для ввода исходных данных"""

    calculationRequested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.feeds = [feed.copy() for feed in FEEDS]  # глубокое копирование
        # Копируем nutrients для каждого корма
        for feed in self.feeds:
            feed['nutrients'] = feed['nutrients'].copy()
        self.requirements = {
            k: v.copy() for k, v in NUTRIENT_REQUIREMENTS.items()
        }
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Группа характеристик кормов
        feeds_group = QGroupBox("Характеристики кормов")
        feeds_layout = QVBoxLayout()

        self.feeds_table = QTableWidget()
        self.feeds_table.setColumnCount(6)
        self.feeds_table.setHorizontalHeaderLabels(
            ["Корм", "A1 (кг/т)", "A2 (кг/т)", "A3 (кг/т)", "A4 (кг/т)", "Цена (тыс. руб/т)"]
        )
        self.feeds_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Подключаем сигнал изменения ячеек
        self.feeds_table.cellChanged.connect(self._on_feeds_changed)

        self._update_feeds_table()
        feeds_layout.addWidget(self.feeds_table)

        reset_btn = QPushButton("Сбросить к значениям по умолчанию")
        reset_btn.clicked.connect(self.reset_to_defaults)
        feeds_layout.addWidget(reset_btn)

        feeds_group.setLayout(feeds_layout)
        layout.addWidget(feeds_group)

        # Группа норм питательных веществ
        nutrients_group = QGroupBox("Нормы содержания питательных веществ")
        nutrients_layout = QVBoxLayout()

        self.nutrients_table = QTableWidget()
        self.nutrients_table.setColumnCount(4)
        self.nutrients_table.setHorizontalHeaderLabels(
            ["Вещество", "Мин (кг)", "Макс (кг)", "Точно (кг)"]
        )
        self.nutrients_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Подключаем сигнал изменения ячеек
        self.nutrients_table.cellChanged.connect(self._on_nutrients_changed)

        self._update_nutrients_table()
        nutrients_layout.addWidget(self.nutrients_table)

        nutrients_group.setLayout(nutrients_layout)
        layout.addWidget(nutrients_group)

        # Группа управления
        control_group = QGroupBox("Управление расчетом")
        control_layout = QHBoxLayout()

        self.calc_btn = QPushButton("Выполнить расчет")
        self.calc_btn.setMinimumHeight(45)
        self.calc_btn.clicked.connect(lambda: self.calculationRequested.emit('solve'))
        control_layout.addWidget(self.calc_btn)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        self.status_label = QLabel("Введите данные и нажмите 'Выполнить расчет'")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.setLayout(layout)

    def _on_feeds_changed(self, row: int, col: int):
        """Обработчик изменения данных в таблице кормов"""
        try:
            item = self.feeds_table.item(row, col)
            if item is None:
                return
            text = item.text().strip()
            if not text or text == '-':
                return

            value = float(text.replace(',', '.'))

            if col == 0:  # Название корма
                self.feeds[row]['name'] = text
            elif 1 <= col <= 4:  # Питательные вещества A1-A4
                nutrient_key = f'A{col}'
                self.feeds[row]['nutrients'][nutrient_key] = value
            elif col == 5:  # Цена
                self.feeds[row]['price'] = value

            self.status_label.setText(f"Данные корма {self.feeds[row]['name']} обновлены")
        except ValueError:
            pass  # Игнорируем некорректный ввод

    def _on_nutrients_changed(self, row: int, col: int):
        """Обработчик изменения данных в таблице норм"""
        try:
            item = self.nutrients_table.item(row, col)
            if item is None:
                return
            text = item.text().strip()

            nutrient_keys = list(self.requirements.keys())
            if row >= len(nutrient_keys):
                return
            nutrient = nutrient_keys[row]

            if not text or text == '-':
                if col == 1:
                    self.requirements[nutrient]['min'] = None
                elif col == 2:
                    self.requirements[nutrient]['max'] = None
                elif col == 3:
                    self.requirements[nutrient]['exact'] = None
            else:
                value = float(text.replace(',', '.'))
                if col == 1:
                    self.requirements[nutrient]['min'] = value
                elif col == 2:
                    self.requirements[nutrient]['max'] = value
                elif col == 3:
                    self.requirements[nutrient]['exact'] = value

            self.status_label.setText(f"Норма для {nutrient} обновлена")
        except ValueError:
            pass

    def _update_feeds_table(self):
        """Обновление таблицы кормов"""
        self.feeds_table.blockSignals(True)  # Блокируем сигналы при обновлении
        self.feeds_table.setRowCount(len(self.feeds))

        for i, feed in enumerate(self.feeds):
            name_item = QTableWidgetItem(feed['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Нельзя редактировать имя
            self.feeds_table.setItem(i, 0, name_item)

            self.feeds_table.setItem(i, 1, QTableWidgetItem(str(feed['nutrients']['A1'])))
            self.feeds_table.setItem(i, 2, QTableWidgetItem(str(feed['nutrients']['A2'])))
            self.feeds_table.setItem(i, 3, QTableWidgetItem(str(feed['nutrients']['A3'])))
            self.feeds_table.setItem(i, 4, QTableWidgetItem(str(feed['nutrients']['A4'])))
            self.feeds_table.setItem(i, 5, QTableWidgetItem(str(feed['price'])))

        self.feeds_table.blockSignals(False)

    def _update_nutrients_table(self):
        """Обновление таблицы норм"""
        self.nutrients_table.blockSignals(True)
        self.nutrients_table.setRowCount(len(self.requirements))

        for i, (nutrient, req) in enumerate(self.requirements.items()):
            name_item = QTableWidgetItem(nutrient)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.nutrients_table.setItem(i, 0, name_item)

            self.nutrients_table.setItem(i, 1, QTableWidgetItem(
                str(req['min']) if req['min'] is not None else "-"))
            self.nutrients_table.setItem(i, 2, QTableWidgetItem(
                str(req['max']) if req['max'] is not None else "-"))
            self.nutrients_table.setItem(i, 3, QTableWidgetItem(
                str(req['exact']) if req['exact'] is not None else "-"))

        self.nutrients_table.blockSignals(False)

    def get_input_data(self) -> dict:
        """Получение введенных данных"""
        try:
            return {
                'feeds': self.feeds,
                'requirements': self.requirements,
                'success': True
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def reset_to_defaults(self):
        """Сброс к значениям по умолчанию"""
        self.feeds = [feed.copy() for feed in FEEDS]
        for feed in self.feeds:
            feed['nutrients'] = feed['nutrients'].copy()
        self.requirements = {k: v.copy() for k, v in NUTRIENT_REQUIREMENTS.items()}
        self._update_feeds_table()
        self._update_nutrients_table()
        self.status_label.setText("Значения сброшены к исходным")

    def set_data(self, data: dict):
        """Установка данных из файла"""
        try:
            if 'feeds' in data:
                self.feeds = data['feeds']
                self._update_feeds_table()
            if 'requirements' in data:
                self.requirements = data['requirements']
                self._update_nutrients_table()
            self.status_label.setText("Данные загружены")
        except Exception as e:
            self.status_label.setText(f"Ошибка: {str(e)}")