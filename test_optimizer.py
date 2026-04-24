# tests/test_optimizer.py
"""
Модульные тесты для проверки корректности работы оптимизатора кормового рациона
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pytest
from models.optimizer import FeedOptimizer
from utils.constants import FEEDS, NUTRIENT_REQUIREMENTS


class TestFeedOptimizer:
    """Тесты класса FeedOptimizer"""

    @pytest.fixture
    def optimizer(self):
        """Фикстура для создания экземпляра оптимизатора"""
        return FeedOptimizer()

    @pytest.fixture
    def model(self, optimizer):
        """Фикстура для построения математической модели"""
        return optimizer.build_simplex_model(FEEDS, NUTRIENT_REQUIREMENTS)

    @pytest.fixture
    def solution(self, optimizer, model):
        """Фикстура для получения оптимального решения"""
        return optimizer.solve_simplex(model)

    # ==================== Тест 1: Построение модели ====================
    def test_build_model_dimensions(self, model):
        """Проверка размерностей матриц модели"""
        assert model['A_eq'].shape == (1, 3), (
            f"Ожидалось A_eq: (1, 3), получено {model['A_eq'].shape}"
        )
        assert model['A_ub'].shape == (4, 3), (
            f"Ожидалось A_ub: (4, 3), получено {model['A_ub'].shape}"
        )
        assert len(model['c']) == 3, (
            f"Ожидалось c: 3 элемента, получено {len(model['c'])}"
        )

    def test_build_model_coefficients(self, model):
        """Проверка коэффициентов целевой функции"""
        expected_c = np.array([400, 200, 300])
        assert np.array_equal(model['c'], expected_c), (
            f"Ожидалось c = [400, 200, 300], получено {model['c']}"
        )

    def test_build_model_eq_constraints(self, model):
        """Проверка ограничения-равенства A2: 3x1 + x2 = 4.28"""
        assert model['A_eq'][0, 0] == 3.0, "Коэффициент при x1 в A_eq"
        assert model['A_eq'][0, 1] == 1.0, "Коэффициент при x2 в A_eq"
        assert model['A_eq'][0, 2] == 0.0, "Коэффициент при x3 в A_eq"
        assert model['b_eq'][0] == 4.28, "Правая часть A_eq"

    def test_build_model_ub_constraints(self, model):
        """Проверка ограничений-неравенств"""
        # A3_max: 5x1 + 8x2 + 3x3 <= 35
        assert model['A_ub'][0, 0] == 5.0
        assert model['A_ub'][0, 1] == 8.0
        assert model['A_ub'][0, 2] == 3.0
        assert model['b_ub'][0] == 35.0

        # A1_min: -2x1 - 4x2 - 6x3 <= -20
        assert model['A_ub'][1, 0] == -2.0
        assert model['A_ub'][1, 1] == -4.0
        assert model['A_ub'][1, 2] == -6.0
        assert model['b_ub'][1] == -20.0

        # A4_min: -2x1 - 4x3 <= -40
        assert model['A_ub'][3, 0] == -2.0
        assert model['A_ub'][3, 1] == 0.0
        assert model['A_ub'][3, 2] == -4.0
        assert model['b_ub'][3] == -40.0

    # ==================== Тест 2: Решение задачи ====================
    def test_solution_success(self, solution):
        """Проверка успешности решения"""
        assert solution['success'] is True, (
            f"Решение не найдено: {solution.get('message', '')}"
        )

    def test_solution_fun_value(self, solution):
        """Проверка значения целевой функции"""
        assert 3300 <= solution['fun'] <= 3400, (
            f"Z_min должно быть в диапазоне [3300, 3400], получено {solution['fun']:.2f}"
        )

    def test_solution_x_values(self, solution):
        """Проверка оптимальных значений переменных"""
        x = solution['x']
        assert x[0] > 0, f"x1 должно быть > 0, получено {x[0]:.6f}"
        assert x[2] > 0, f"x3 должно быть > 0, получено {x[2]:.6f}"

    # ==================== Тест 3: Проверка ограничения A2 ====================
    def test_constraint_a2_equality(self, solution):
        """Проверка выполнения A2: 3x1 + x2 = 4.28"""
        x = solution['x']
        left_side = 3 * x[0] + x[1]
        assert abs(left_side - 4.28) < 0.01, (
            f"A2 нарушено: 3*x1 + x2 = {left_side:.4f} != 4.28"
        )

    # ==================== Тест 4: Проверка ограничения A1 ====================
    def test_constraint_a1_min(self, solution):
        """Проверка A1: 2x1 + 4x2 + 6x3 >= 20"""
        x = solution['x']
        actual = 2 * x[0] + 4 * x[1] + 6 * x[2]
        assert actual >= 20 - 0.01, (
            f"A1 нарушено: 2*x1 + 4*x2 + 6*x3 = {actual:.4f} < 20"
        )

    # ==================== Тест 5: Проверка ограничения A3 ====================
    def test_constraint_a3_min(self, solution):
        """Проверка A3_min: 5x1 + 8x2 + 3x3 >= 25"""
        x = solution['x']
        actual = 5 * x[0] + 8 * x[1] + 3 * x[2]
        assert actual >= 25 - 0.01, (
            f"A3_min нарушено: 5*x1 + 8*x2 + 3*x3 = {actual:.4f} < 25"
        )

    def test_constraint_a3_max(self, solution):
        """Проверка A3_max: 5x1 + 8x2 + 3x3 <= 35"""
        x = solution['x']
        actual = 5 * x[0] + 8 * x[1] + 3 * x[2]
        assert actual <= 35 + 0.01, (
            f"A3_max нарушено: 5*x1 + 8*x2 + 3*x3 = {actual:.4f} > 35"
        )

    # ==================== Тест 6: Проверка ограничения A4 ====================
    def test_constraint_a4_min(self, solution):
        """Проверка A4: 2x1 + 4x3 >= 40"""
        x = solution['x']
        actual = 2 * x[0] + 4 * x[2]
        assert actual >= 40 - 0.01, (
            f"A4 нарушено: 2*x1 + 4*x3 = {actual:.4f} < 40"
        )

    # ==================== Тест 7: Наличие B2 ====================
    def test_b2_presence(self, solution):
        """Проверка присутствия корма B2 в решении"""
        assert solution['x'][1] > 0, (
            f"B2 отсутствует в решении: x2 = {solution['x'][1]:.6f}"
        )

    # ==================== Тест 8: Неотрицательность ====================
    def test_non_negativity(self, solution):
        """Проверка неотрицательности всех переменных"""
        for i, xi in enumerate(solution['x']):
            assert xi >= -1e-10, (
                f"Переменная x{i+1} = {xi:.10f} отрицательна"
            )

    # ==================== Тест 9: Симплекс-итерации ====================
    def test_simplex_iterations_exist(self, solution):
        """Проверка наличия симплекс-итераций"""
        iterations = solution.get('simplex_iterations', [])
        assert len(iterations) > 0, "Симплекс-итерации отсутствуют"

    def test_simplex_phase1_exists(self, solution):
        """Проверка наличия итераций Фазы 1"""
        iterations = solution.get('simplex_iterations', [])
        phase1 = [it for it in iterations if it.get('phase') == 1]
        assert len(phase1) > 0, "Итерации Фазы 1 отсутствуют"

    def test_simplex_phase2_exists(self, solution):
        """Проверка наличия итераций Фазы 2"""
        iterations = solution.get('simplex_iterations', [])
        phase2 = [it for it in iterations if it.get('phase') == 2]
        assert len(phase2) > 0, "Итерации Фазы 2 отсутствуют"

    # ==================== Тест: Проверка питательных веществ ====================
    def test_nutrients_check(self, solution):
        """Проверка таблицы питательных веществ"""
        optimizer = FeedOptimizer()
        nutrients_df = optimizer.check_nutrients(solution)
        assert not nutrients_df.empty, "Таблица питательных веществ пуста"
        assert len(nutrients_df) == 4, "Должно быть 4 питательных вещества"
        assert all(status == 'OK' for status in nutrients_df['Статус']), (
            "Все статусы должны быть OK"
        )

    # ==================== Тест: Таблица распределения ====================
    def test_allocation_dataframe(self, solution):
        """Проверка таблицы распределения кормов"""
        optimizer = FeedOptimizer()
        allocation_df = optimizer.get_allocation_dataframe(solution)
        assert not allocation_df.empty, "Таблица распределения пуста"
        assert 'Вид корма' in allocation_df.columns
        assert 'Количество (т)' in allocation_df.columns
        assert 'Стоимость (тыс. руб)' in allocation_df.columns

    # ==================== Тест: Граничные значения ====================
    def test_find_max_x2(self, optimizer):
        """Проверка аналитического расчета максимального x2"""
        x2_max = optimizer._find_max_x2()
        assert x2_max > 0, "Максимальное x2 должно быть > 0"
        assert x2_max < 0.01, f"Максимальное x2 должно быть < 0.01, получено {x2_max:.6f}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])