# views/charts_tab.py
"""
Модуль вкладки визуализации
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import matplotlib

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from utils.constants import COLORS


class MplCanvas(FigureCanvas):
    """Виджет для отображения графиков matplotlib"""

    def __init__(self, parent=None, width=8, height=4.5, dpi=90):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=COLORS.get('background', '#FAFDFA'))
        self.fig.patch.set_facecolor(COLORS.get('background', '#FAFDFA'))
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor(COLORS.get('surface', '#F1F8F1'))
        super().__init__(self.fig)
        self.setParent(parent)
        self.fig.tight_layout(pad=1.5)


class ChartsTab(QWidget):
    """Вкладка для визуализации результатов"""

    def __init__(self):
        super().__init__()
        self.current_solution = None
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса вкладки"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        title_label = QLabel("Визуализация результатов")
        title_label.setProperty("role", "heading")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Панель управления
        control_frame = QFrame()
        control_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.get('surface', '#F1F8F1')};
                border: 1px solid {COLORS.get('border', '#C8E6C9')};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        control_layout = QHBoxLayout(control_frame)
        control_layout.setSpacing(10)

        control_layout.addWidget(QLabel("📊 Тип графика:"))

        self.chart_combo = QComboBox()
        self.chart_combo.addItems([
            "Структура рациона",
            "Затраты по видам кормов",
            "Содержание питательных веществ",
            "Сравнение с нормами"
        ])
        self.chart_combo.setMinimumWidth(200)
        self.chart_combo.currentIndexChanged.connect(self.update_chart)
        control_layout.addWidget(self.chart_combo)

        control_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.update_chart)
        control_layout.addWidget(self.refresh_btn)

        layout.addWidget(control_frame)

        # Область графика
        self.canvas = MplCanvas(self, width=8, height=4.5, dpi=90)
        layout.addWidget(self.canvas)

        # Статус
        self.status_label = QLabel("Выберите тип графика")
        self.status_label.setStyleSheet(f"color: {COLORS.get('text_light', '#6B8B6B')}; font-size: 11px;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def set_solution(self, solution: dict):
        """Установка решения для визуализации"""
        self.current_solution = solution
        self.update_chart()

    def update_chart(self):
        """Обновление графика"""
        if not self.current_solution or not self.current_solution.get('success', False):
            self._show_no_data_message()
            return

        chart_type = self.chart_combo.currentIndex()

        try:
            self.canvas.axes.clear()
            self._setup_axes_style()

            if chart_type == 0:
                self._plot_structure()
            elif chart_type == 1:
                self._plot_costs()
            elif chart_type == 2:
                self._plot_nutrients()
            elif chart_type == 3:
                self._plot_comparison()

            self.canvas.fig.tight_layout(pad=1.2)
            self.canvas.draw()
            self.status_label.setText(f"✓ {self.chart_combo.currentText()}")

        except Exception as e:
            self.status_label.setText(f"❌ Ошибка: {str(e)[:30]}")

    def _setup_axes_style(self):
        """Настройка стиля осей"""
        self.canvas.axes.tick_params(colors=COLORS.get('text', '#1B3A1B'), labelsize=9)
        for spine in self.canvas.axes.spines.values():
            spine.set_color(COLORS.get('border', '#C8E6C9'))
            spine.set_linewidth(0.5)

    def _show_no_data_message(self):
        """Сообщение об отсутствии данных"""
        self.canvas.axes.clear()
        self.canvas.axes.text(0.5, 0.5, 'Нет данных для визуализации',
                              ha='center', va='center', fontsize=11,
                              color=COLORS.get('text_light', '#6B8B6B'),
                              transform=self.canvas.axes.transAxes)
        self.canvas.axes.set_xticks([])
        self.canvas.axes.set_yticks([])
        self.canvas.draw()

    def _plot_structure(self):
        """График структуры рациона (количество кормов)"""
        x = self.current_solution.get('x', [])
        feeds = self.current_solution.get('feeds', [])

        names = [f['name'] for f in feeds]
        values = [max(0, v) for v in x]

        colors = ['#4CAF50', '#81C784', '#A5D6A7']
        bars = self.canvas.axes.bar(names, values, color=colors[:len(names)],
                                    edgecolor='#2E7D32', linewidth=1)

        self.canvas.axes.set_title('Оптимальный рацион (тонны)', fontsize=11, fontweight='bold',
                                   color=COLORS.get('primary', '#2E7D32'))
        self.canvas.axes.set_ylabel('Количество (т)', fontsize=9)
        self.canvas.axes.set_xlabel('Вид корма', fontsize=9)

        for bar, val in zip(bars, values):
            if val > 0:
                self.canvas.axes.text(bar.get_x() + bar.get_width() / 2., bar.get_height(),
                                      f'{val:.2f}',
                                      ha='center', va='bottom', fontsize=9, fontweight='bold')

        self.canvas.axes.grid(True, alpha=0.3, axis='y')

    def _plot_costs(self):
        """График затрат по видам кормов"""
        x = self.current_solution.get('x', [])
        feeds = self.current_solution.get('feeds', [])

        names = [f['name'] for f in feeds]
        costs = [max(0, x[i]) * feeds[i]['price'] for i in range(len(feeds))]

        colors = ['#FF9800', '#FFB74D', '#FFCC80']
        bars = self.canvas.axes.bar(names, costs, color=colors[:len(names)],
                                    edgecolor='#E65100', linewidth=1)

        self.canvas.axes.set_title('Затраты по видам кормов (тыс. руб)', fontsize=11, fontweight='bold',
                                   color=COLORS.get('primary', '#2E7D32'))
        self.canvas.axes.set_ylabel('Стоимость (тыс. руб)', fontsize=9)
        self.canvas.axes.set_xlabel('Вид корма', fontsize=9)

        for bar, cost in zip(bars, costs):
            if cost > 0:
                self.canvas.axes.text(bar.get_x() + bar.get_width() / 2., bar.get_height(),
                                      f'{cost:.1f}',
                                      ha='center', va='bottom', fontsize=9, fontweight='bold')

        self.canvas.axes.grid(True, alpha=0.3, axis='y')

    def _plot_nutrients(self):
        """График содержания питательных веществ"""
        nutrients_actual = self.current_solution.get('nutrients_actual', {})
        requirements = self.current_solution.get('requirements', {})

        nutrients = ['A1', 'A2', 'A3', 'A4']
        actual_values = [nutrients_actual.get(n, 0) for n in nutrients]

        # Подготовка норм для отображения
        min_values = []
        max_values = []
        exact_values = []

        for n in nutrients:
            req = requirements.get(n, {})
            min_values.append(req.get('min', 0) if req.get('min') else 0)
            max_values.append(req.get('max', 0) if req.get('max') else 0)
            exact_values.append(req.get('exact', 0) if req.get('exact') else 0)

        x_pos = np.arange(len(nutrients))
        width = 0.35

        bars = self.canvas.axes.bar(x_pos - width / 2, actual_values, width,
                                    label='Фактически', color='#4CAF50', edgecolor='#2E7D32')

        # Отображаем нормы
        norm_values = []
        for i, n in enumerate(nutrients):
            if exact_values[i] > 0:
                norm_values.append(exact_values[i])
            elif max_values[i] > 0:
                norm_values.append(max_values[i])
            else:
                norm_values.append(min_values[i])

        bars2 = self.canvas.axes.bar(x_pos + width / 2, norm_values, width,
                                     label='Норма', color='#FF9800', edgecolor='#E65100', alpha=0.7)

        self.canvas.axes.set_title('Содержание питательных веществ (кг)', fontsize=11, fontweight='bold',
                                   color=COLORS.get('primary', '#2E7D32'))
        self.canvas.axes.set_xticks(x_pos)
        self.canvas.axes.set_xticklabels(nutrients)
        self.canvas.axes.set_ylabel('Количество (кг)', fontsize=9)
        self.canvas.axes.legend(fontsize=8)
        self.canvas.axes.grid(True, alpha=0.3, axis='y')

    def _plot_comparison(self):
        """Сравнительная диаграмма"""
        x = self.current_solution.get('x', [])
        feeds = self.current_solution.get('feeds', [])

        # Круговая диаграмма затрат
        costs = [max(0, x[i]) * feeds[i]['price'] for i in range(len(feeds))]
        names = [f"{f['name']} ({c:.1f} тыс. руб)" for f, c in zip(feeds, costs)]

        colors = ['#4CAF50', '#FF9800', '#2196F3']
        wedges, texts, autotexts = self.canvas.axes.pie(
            costs, labels=names, colors=colors[:len(names)],
            autopct='%1.1f%%', startangle=90,
            textprops={'fontsize': 8}
        )

        self.canvas.axes.set_title('Структура затрат на корма', fontsize=11, fontweight='bold',
                                   color=COLORS.get('primary', '#2E7D32'))