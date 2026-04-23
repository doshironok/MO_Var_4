# views/main_window.py
"""
Модуль главного окна приложения
"""
import traceback

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from views.input_tab import InputTab
from views.results_tab import ResultsTab
from views.charts_tab import ChartsTab
from views.analysis_tab import AnalysisTab
from views.simplex_tab import SimplexTab
from models.optimizer import FeedOptimizer
from controllers.file_manager import FileManager
from controllers.export_manager import ExportManager
from utils.constants import APP_NAME, APP_WIDTH, APP_HEIGHT


class MainWindow(QMainWindow):
    """
    Главное окно приложения "Оптимизатор кормового рациона"
    """

    def __init__(self):
        super().__init__()
        self.optimizer = FeedOptimizer()
        self.file_manager = FileManager(self)
        self.export_manager = ExportManager(self)
        self.current_solution = None
        self.current_nutrients_df = None
        self.current_allocation_df = None

        self.init_ui()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle(APP_NAME)
        self.setGeometry(100, 100, APP_WIDTH, APP_HEIGHT)

        # Центральный виджет с вкладками
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Создание вкладок
        self.input_tab = InputTab()
        self.results_tab = ResultsTab()
        self.charts_tab = ChartsTab()
        self.analysis_tab = AnalysisTab()
        self.simplex_tab = SimplexTab()

        # Подключение сигналов
        self.input_tab.calculationRequested.connect(self.run_calculation)

        # Добавление вкладок
        self.tab_widget.addTab(self.input_tab, "📝 Ввод данных")
        self.tab_widget.addTab(self.results_tab, "📊 Результаты")
        self.tab_widget.addTab(self.charts_tab, "📈 Графики")
        self.tab_widget.addTab(self.analysis_tab, "🔍 Анализ")
        self.tab_widget.addTab(self.simplex_tab, "📐 Симплекс-метод")

        # Создание меню
        self.create_menu()

        # Создание панели инструментов
        self.create_toolbar()

        # Строка состояния
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе | Оптимизатор кормового рациона")

    def create_menu(self):
        """Создание меню приложения"""
        menubar = self.menuBar()

        # Меню Файл
        file_menu = menubar.addMenu("Файл")

        new_action = QAction("Новый расчет", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_calculation)
        file_menu.addAction(new_action)

        open_action = QAction("Открыть проект", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)

        save_action = QAction("Сохранить проект", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        export_pdf_action = QAction("Экспорт в PDF", self)
        export_pdf_action.setShortcut(QKeySequence("Ctrl+P"))
        export_pdf_action.triggered.connect(self.export_pdf)
        file_menu.addAction(export_pdf_action)

        export_excel_action = QAction("Экспорт в Excel", self)
        export_excel_action.setShortcut(QKeySequence("Ctrl+E"))
        export_excel_action.triggered.connect(self.export_excel)
        file_menu.addAction(export_excel_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню Расчет
        calc_menu = menubar.addMenu("Расчет")

        solve_action = QAction("Выполнить расчет", self)
        solve_action.setShortcut(QKeySequence("F5"))
        solve_action.triggered.connect(lambda: self.run_calculation('solve'))
        calc_menu.addAction(solve_action)

        # Меню Справка
        help_menu = menubar.addMenu("Справка")

        about_action = QAction("О программе", self)
        about_action.setShortcut(QKeySequence("F1"))
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        guide_action = QAction("Руководство пользователя", self)
        guide_action.triggered.connect(self.show_guide)
        help_menu.addAction(guide_action)

    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = self.addToolBar("Инструменты")
        toolbar.setMovable(False)

        solve_btn = QAction("🚀 Расчет", self)
        solve_btn.setToolTip("Выполнить расчет (F5)")
        solve_btn.triggered.connect(lambda: self.run_calculation('solve'))
        toolbar.addAction(solve_btn)

        toolbar.addSeparator()

        save_btn = QAction("💾 Сохранить", self)
        save_btn.setToolTip("Сохранить проект (Ctrl+S)")
        save_btn.triggered.connect(self.save_project)
        toolbar.addAction(save_btn)

        export_btn = QAction("📊 Экспорт", self)
        export_btn.setToolTip("Экспорт в Excel (Ctrl+E)")
        export_btn.triggered.connect(self.export_excel)
        toolbar.addAction(export_btn)

    def run_calculation(self, mode: str):
        """Запуск расчета"""
        try:
            self.status_bar.showMessage("Выполняется расчет...")
            QApplication.processEvents()

            input_data = self.input_tab.get_input_data()

            if not input_data['success']:
                QMessageBox.warning(self, "Ошибка ввода",
                                   input_data.get('error', 'Неизвестная ошибка'))
                self.status_bar.showMessage("Ошибка ввода данных")
                return

            print(f"\n{'='*80}")
            print(f"ЗАПУСК РАСЧЕТА ОПТИМИЗАЦИИ КОРМОВОГО РАЦИОНА")
            print(f"{'='*80}")

            # Построение модели
            model = self.optimizer.build_simplex_model(
                feeds=input_data['feeds'],
                requirements=input_data['requirements']
            )

            # Решение симплекс-методом
            solution = self.optimizer.solve_simplex(model)

            self.current_solution = solution
            self.current_nutrients_df = self.optimizer.check_nutrients(solution)
            self.current_allocation_df = self.optimizer.get_allocation_dataframe(solution)

            # Отображение результатов
            self.results_tab.display_results(
                solution,
                self.current_nutrients_df,
                self.current_allocation_df
            )
            self.charts_tab.set_solution(solution)
            self.analysis_tab.set_data(
                solution,
                self.current_nutrients_df,
                self.current_allocation_df
            )

            # Передача итераций симплекс-метода
            simplex_iterations = solution.get('simplex_iterations', [])
            self.simplex_tab.set_iterations(simplex_iterations, mode)

            # Переключение на вкладку результатов
            self.tab_widget.setCurrentIndex(1)

            if solution.get('success', False):
                fun_value = solution.get('fun', 0)
                iterations_count = len(simplex_iterations)
                self.status_bar.showMessage(
                    f"✅ Расчет выполнен успешно. "
                    f"Мин. затраты = {fun_value:.2f} тыс. руб. "
                    f"Итераций симплекс-метода: {iterations_count}"
                )
            else:
                self.status_bar.showMessage(
                    f"❌ Ошибка: {solution.get('message', 'Неизвестная ошибка')}"
                )

        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Критическая ошибка: {str(e)}")
            self.status_bar.showMessage(f"❌ Ошибка: {str(e)[:50]}")

    def new_calculation(self):
        """Начать новый расчет"""
        reply = QMessageBox.question(
            self, "Новый расчет",
            "Начать новый расчет? Несохраненные данные будут потеряны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.input_tab.reset_to_defaults()
            self.results_tab.clear()
            self.charts_tab.set_solution(None)
            self.analysis_tab.set_data(None, None, None)
            self.simplex_tab.set_iterations([], "")
            self.current_solution = None
            self.tab_widget.setCurrentIndex(0)
            self.status_bar.showMessage("Новый расчет")

    def save_project(self):
        """Сохранение проекта"""
        if not self.current_solution:
            QMessageBox.warning(self, "Предупреждение", "Нет данных для сохранения")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить проект", "", "JSON файлы (*.json)"
        )

        if filename:
            input_data = self.input_tab.get_input_data()
            data = {
                'input': input_data,
                'solution': {
                    'fun': float(self.current_solution['fun']) if self.current_solution['fun'] else None,
                    'success': self.current_solution['success'],
                    'message': self.current_solution['message'],
                    'x': [float(v) for v in self.current_solution.get('x', [])]
                }
            }

            if self.file_manager.save_project(data, filename):
                self.status_bar.showMessage(f"Проект сохранен: {filename}")

    def open_project(self):
        """Загрузка проекта"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Открыть проект", "", "JSON файлы (*.json)"
        )

        if filename:
            data = self.file_manager.load_project(filename)
            if data and 'input' in data:
                self.input_tab.set_data(data['input'])
                self.status_bar.showMessage(f"Проект загружен: {filename}")

    def export_pdf(self):
        """Экспорт в PDF"""
        if not self.current_solution or not self.current_solution.get('success'):
            QMessageBox.warning(self, "Предупреждение", "Нет успешного решения для экспорта")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Экспорт в PDF", "", "PDF файлы (*.pdf)"
        )

        if filename:
            if self.export_manager.export_to_pdf(
                self.current_solution,
                self.current_nutrients_df,
                self.current_allocation_df,
                filename
            ):
                self.status_bar.showMessage(f"Отчет сохранен: {filename}")

    def export_excel(self):
        """Экспорт в Excel"""
        if not self.current_solution or not self.current_solution.get('success'):
            QMessageBox.warning(self, "Предупреждение", "Нет успешного решения для экспорта")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Экспорт в Excel", "", "Excel файлы (*.xlsx)"
        )

        if filename:
            if self.export_manager.export_to_excel(
                self.current_solution,
                self.current_nutrients_df,
                self.current_allocation_df,
                filename
            ):
                self.status_bar.showMessage(f"Отчет сохранен: {filename}")

    def show_about(self):
        """О программе"""
        dialog = AboutDialog(self)
        dialog.exec()

    def show_guide(self):
        """Руководство пользователя"""
        dialog = GuideDialog(self)
        dialog.exec()


class AboutDialog(QDialog):
    """Диалог 'О программе'"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.resize(800, 500)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml("""
        <div style='text-align: center; font-family: Segoe UI, Arial, sans-serif;'>
            <h2 style='color: #2E7D32; margin: 20px 0; font-size: 24px;'>🌾 Оптимизатор кормового рациона</h2>
            <p style='font-size: 18px; color: #666; margin: 15px 0;'>Версия 1.0.0</p>
            <hr style='border: 2px solid #2E7D32; width: 95%; margin: 25px auto;'>

            <div style='text-align: left; margin: 25px 35px;'>
                <p style='margin: 20px 0; font-size: 12px; line-height: 1.8;'>
                <b>Назначение:</b> Решение задачи оптимизации кормового рациона 
                методом линейного программирования (симплекс-метод)</p>

                <p style='margin: 20px 0; font-size: 12px; line-height: 1.8;'>
                <b>Суть задачи:</b> Определение оптимального количества кормов трех видов 
                (B1, B2, B3) для обеспечения необходимого содержания питательных веществ 
                (A1, A2, A3, A4) при минимальных затратах.</p>
            </div>

            <div style='background-color: #F1F8F1; padding: 25px; border-radius: 10px; margin: 25px 35px; text-align: left;'>
                <p style='margin: 15px 0; font-size: 12px;'><b>Разработчик:</b> Зубенко Диана Сергеевна</p>
                <p style='margin: 15px 0; font-size: 12px;'><b>Учебное заведение:</b> ФГБОУ ВО «КубГТУ»</p>
                <p style='margin: 15px 0; font-size: 12px;'><b>Факультет:</b> Информационных технологий и кибербезопасности</p>
                <p style='margin: 15px 0; font-size: 12px;'><b>Кафедра:</b> Информационных систем и программирования</p>
                <p style='margin: 15px 0; font-size: 12px;'><b>Группа:</b> 23-КБ-ПР1</p>
                <p style='margin: 15px 0; font-size: 12px;'><b>Год:</b> 2026</p>
            </div>

            <hr style='border: 2px solid #2E7D32; width: 95%; margin: 25px auto;'>
            <p style='color: #999; margin: 20px 0; font-size: 16px;'>© 2026 КубГТУ, кафедра ИСП</p>
        </div>
        """)

        layout.addWidget(text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)


class GuideDialog(QDialog):
    """Диалог 'Руководство пользователя'"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Руководство пользователя")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Segoe UI", 12))
        text_edit.setHtml("""
        <div style='font-family: Segoe UI, Arial, sans-serif; margin: 20px;'>
            <h2 style='color: #2E7D32; text-align: center; margin: 25px 0 35px 0; font-size: 28px;'>
            📖 Руководство пользователя</h2>

            <div style='margin: 35px 30px;'>
                <h3 style='color: #2E7D32; margin: 25px 0 20px 0; font-size: 22px;'>
                1. Ввод исходных данных</h3>
                <p style='margin: 12px 0 12px 35px; font-size: 14px; line-height: 1.8;'>
                • Просмотрите характеристики кормов (содержание питательных веществ A1-A4 и цены)</p>
                <p style='margin: 12px 0 12px 35px; font-size: 14px; line-height: 1.8;'>
                • Проверьте нормы содержания питательных веществ в рационе</p>
                <p style='margin: 12px 0 12px 35px; font-size: 14px; line-height: 1.8;'>
                • При необходимости измените данные или сбросьте к значениям по умолчанию</p>
            </div>

            <div style='margin: 35px 30px;'>
                <h3 style='color: #2E7D32; margin: 25px 0 20px 0; font-size: 22px;'>
                2. Выполнение расчета</h3>
                <p style='margin: 12px 0 12px 35px; font-size: 14px; line-height: 1.8;'>
                • Нажмите кнопку "Выполнить расчет" или используйте меню Расчет</p>
                <p style='margin: 12px 0 12px 35px; font-size: 14px; line-height: 1.8;'>
                • Система автоматически построит математическую модель и решит задачу симплекс-методом</p>
            </div>

            <div style='margin: 35px 30px;'>
                <h3 style='color: #2E7D32; margin: 25px 0 20px 0; font-size: 22px;'>
                3. Просмотр результатов</h3>
                <p style='margin: 12px 0 12px 35px; font-size: 14px; line-height: 1.8;'>
                • <b>Вкладка "Результаты"</b> - основные показатели и распределение кормов</p>
                <p style='margin: 12px 0 12px 35px; font-size: 14px; line-height: 1.8;'>
                • <b>Вкладка "Графики"</b> - визуализация структуры рациона и затрат</p>
                <p style='margin: 12px 0 12px 35px; font-size: 14px; line-height: 1.8;'>
                • <b>Вкладка "Анализ"</b> - детальная проверка норм питательных веществ</p>
                <p style='margin: 12px 0 12px 35px; font-size: 14px; line-height: 1.8;'>
                • <b>Вкладка "Симплекс-метод"</b> - пошаговое решение с таблицами</p>
            </div>

            <div style='margin: 35px 30px;'>
                <h3 style='color: #2E7D32; margin: 25px 0 20px 0; font-size: 22px;'>
                4. Сохранение и экспорт</h3>
                <p style='margin: 12px 0 12px 35px; font-size: 14px; line-height: 1.8;'>
                • <b>Сохранить проект (JSON)</b> - для последующей загрузки и редактирования</p>
                <p style='margin: 12px 0 12px 35px; font-size: 14px; line-height: 1.8;'>
                • <b>Экспорт в Excel</b> - полный отчет с таблицами распределения и анализа</p>
                <p style='margin: 12px 0 12px 35px; font-size: 14px; line-height: 1.8;'>
                • <b>Экспорт в PDF</b> - форматированный отчет для печати</p>
            </div>

            <div style='background-color: #F1F8F1; padding: 30px; border-radius: 10px; margin: 35px 30px;'>
                <h3 style='color: #2E7D32; margin: 0 0 20px 0; font-size: 22px;'>
                ❓ Ответы на вопросы задания</h3>
                <p style='margin: 15px 0; font-size: 14px;'>
                Программа автоматически определяет:</p>
                <p style='margin: 10px 0 10px 35px; font-size: 14px;'>
                • Количество корма вида B2 для закупки</p>
                <p style='margin: 10px 0 10px 35px; font-size: 14px;'>
                • Общее количество всех кормов</p>
                <p style='margin: 10px 0 10px 35px; font-size: 14px;'>
                • Минимальные затраты на покупку кормов</p>
            </div>
        </div>
        """)

        layout.addWidget(text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Закрыть")
        ok_button.setMinimumWidth(150)
        ok_button.setMinimumHeight(40)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)