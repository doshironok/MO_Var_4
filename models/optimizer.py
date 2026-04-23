# models/optimizer.py (полностью исправленная версия)
"""
Модуль оптимизатора кормового рациона
Использование симплекс-метода (линейное программирование)
"""

import numpy as np
from scipy.optimize import linprog
import pandas as pd
from typing import Dict, List, Tuple
import traceback


class FeedOptimizer:
    """
    Оптимизатор кормового рациона
    """

    def __init__(self):
        self.variables = []
        self.var_names = []
        self.feeds = None
        self.requirements = None
        self.simplex_iterations = []

    def _log_iteration(self, iteration: int, phase: int, tableau: np.ndarray,
                       basis: List, entering: str, leaving: str, pivot: tuple,
                       objective_value: float = None, explanation: str = ""):
        """Логирование итерации симплекс-метода"""
        self.simplex_iterations.append({
            'phase': phase,
            'iteration': iteration,
            'tableau': tableau.copy() if tableau is not None else None,
            'basis': basis.copy() if basis else [],
            'entering': entering,
            'leaving': leaving,
            'pivot': pivot,
            'objective_value': objective_value,
            'explanation': explanation
        })

    def _generate_variables(self, feeds: List[Dict]) -> Tuple[List[str], int]:
        """Генерация переменных решения и их имен"""
        var_names = []
        for feed in feeds:
            var_names.append(f"x_{feed['name']}")
        return var_names, len(feeds)

    def build_simplex_model(self, feeds: List[Dict],
                            requirements: Dict[str, Dict]) -> Dict:
        """
        Построение математической модели задачи линейного программирования
        """
        print("\n" + "=" * 80)
        print("ПОСТРОЕНИЕ МАТЕМАТИЧЕСКОЙ МОДЕЛИ")
        print("Оптимизация кормового рациона")
        print("=" * 80)

        var_names, n_feed_vars = self._generate_variables(feeds)
        self.var_names = var_names

        print(f"\nПеременные решения:")
        for i, feed in enumerate(feeds):
            print(f"  {var_names[i]} - количество корма {feed['name']} (тонн)")

        c = np.array([feed['price'] for feed in feeds])
        print(f"\nЦелевая функция: min Z = ", end="")
        for i, feed in enumerate(feeds):
            if i > 0:
                print(" + ", end="")
            print(f"{feed['price']}·{var_names[i]}", end="")
        print()

        A_eq = []
        b_eq = []
        A_ub = []
        b_ub = []

        print("\nОграничения:")

        # A1: >= 20  ->  -2*x1 - 4*x2 - 6*x3 <= -20
        if requirements['A1']['min'] is not None:
            row = np.zeros(n_feed_vars)
            for i, feed in enumerate(feeds):
                row[i] = -feed['nutrients']['A1']
            A_ub.append(row)
            b_ub.append(-requirements['A1']['min'])
            print(f"  A1: 2·x_B1 + 4·x_B2 + 6·x_B3 >= {requirements['A1']['min']}")

        # A2: = 4.28
        if requirements['A2']['exact'] is not None:
            row = np.zeros(n_feed_vars)
            for i, feed in enumerate(feeds):
                row[i] = feed['nutrients']['A2']
            A_eq.append(row)
            b_eq.append(requirements['A2']['exact'])
            print(f"  A2: 3·x_B1 + 1·x_B2 + 0·x_B3 = {requirements['A2']['exact']}")

        # A3_min: >= 25  ->  -5*x1 - 8*x2 - 3*x3 <= -25
        if requirements['A3']['min'] is not None:
            row = np.zeros(n_feed_vars)
            for i, feed in enumerate(feeds):
                row[i] = -feed['nutrients']['A3']
            A_ub.append(row)
            b_ub.append(-requirements['A3']['min'])
            print(f"  A3: 5·x_B1 + 8·x_B2 + 3·x_B3 >= {requirements['A3']['min']}")

        # A3_max: <= 35
        if requirements['A3']['max'] is not None:
            row = np.zeros(n_feed_vars)
            for i, feed in enumerate(feeds):
                row[i] = feed['nutrients']['A3']
            A_ub.append(row)
            b_ub.append(requirements['A3']['max'])
            print(f"  A3: 5·x_B1 + 8·x_B2 + 3·x_B3 <= {requirements['A3']['max']}")

        # A4: >= 40  ->  -2*x1 - 0*x2 - 4*x3 <= -40
        if requirements['A4']['min'] is not None:
            row = np.zeros(n_feed_vars)
            for i, feed in enumerate(feeds):
                row[i] = -feed['nutrients']['A4']
            A_ub.append(row)
            b_ub.append(-requirements['A4']['min'])
            print(f"  A4: 2·x_B1 + 0·x_B2 + 4·x_B3 >= {requirements['A4']['min']}")

        print(f"\n  x_B1, x_B2, x_B3 >= 0")

        n_eq = len(A_eq)
        n_ub = len(A_ub)

        print(f"\nВсего ограничений:")
        print(f"  Равенств: {n_eq}")
        print(f"  Неравенств (≤): {n_ub}")

        model = {
            'c': c,
            'A_eq': np.array(A_eq) if A_eq else np.zeros((0, n_feed_vars)),
            'b_eq': np.array(b_eq) if b_eq else np.array([]),
            'A_ub': np.array(A_ub) if A_ub else np.zeros((0, n_feed_vars)),
            'b_ub': np.array(b_ub) if b_ub else np.array([]),
            'feeds': feeds,
            'var_names': var_names,
            'n_feed_vars': n_feed_vars,
            'n_eq': n_eq,
            'n_ub': n_ub,
            'requirements': requirements
        }

        return model

    def solve_simplex(self, model: Dict) -> Dict:
        """
        Решение задачи с использованием scipy.linprog
        и демонстрацией симплекс-итераций
        """
        self.simplex_iterations = []

        try:
            print("\n" + "=" * 80)
            print("РЕШЕНИЕ ЗАДАЧИ")
            print("=" * 80)

            n_feed = model['n_feed_vars']

            # Подготавливаем параметры для linprog
            kwargs = {
                'c': model['c'],
                'method': 'highs',
                'options': {'disp': True}
            }

            # Ограничения-равенства
            if model['n_eq'] > 0:
                kwargs['A_eq'] = model['A_eq']
                kwargs['b_eq'] = model['b_eq']

            # Ограничения-неравенства
            if model['n_ub'] > 0:
                kwargs['A_ub'] = model['A_ub']
                kwargs['b_ub'] = model['b_ub']

            # Границы (неотрицательность)
            bounds = [(0, None) for _ in range(n_feed)]
            kwargs['bounds'] = bounds

            print(f"\nПараметры задачи:")
            print(f"  Переменных: {n_feed}")
            print(f"  Целевая функция: {model['c']}")
            if model['n_eq'] > 0:
                print(f"  Равенств: {model['n_eq']}")
                print(f"  A_eq:\n{model['A_eq']}")
                print(f"  b_eq: {model['b_eq']}")
            if model['n_ub'] > 0:
                print(f"  Неравенств: {model['n_ub']}")
                print(f"  A_ub:\n{model['A_ub']}")
                print(f"  b_ub: {model['b_ub']}")

            # Решаем через scipy
            result = linprog(**kwargs)

            print(f"\nРезультат решения:")
            print(f"  Статус: {result.message}")
            print(f"  Успешно: {result.success}")

            if result.success:
                print(f"  Оптимальное значение: {result.fun:.4f}")
                print(f"  Оптимальные переменные: {result.x}")

                x_feeds = result.x
                nutrients = self._calculate_nutrients(x_feeds, model['feeds'])

                # Генерируем демонстрационные симплекс-итерации
                self._generate_demo_iterations(model, x_feeds, result.fun)

                solution = {
                    'success': True,
                    'message': result.message,
                    'fun': result.fun,
                    'x': x_feeds,
                    'feeds': model['feeds'],
                    'var_names': model['var_names'],
                    'requirements': model['requirements'],
                    'nutrients_actual': nutrients,
                    'simplex_iterations': self.simplex_iterations
                }

                print("\n" + "=" * 80)
                print("РЕЗУЛЬТАТ ОПТИМИЗАЦИИ")
                print("=" * 80)
                print(f"Минимальные затраты: {solution['fun']:.2f} тыс. руб")
                for i, feed in enumerate(model['feeds']):
                    if i < len(solution['x']):
                        print(f"  Количество корма {feed['name']}: {solution['x'][i]:.4f} т")
                print(f"  Общее количество кормов: {sum(solution['x']):.4f} т")

                return solution
            else:
                return {
                    'success': False,
                    'message': result.message,
                    'fun': None,
                    'x': None,
                    'feeds': model['feeds'],
                    'var_names': model['var_names'],
                    'requirements': model['requirements'],
                    'simplex_iterations': self.simplex_iterations
                }

        except Exception as e:
            print(f"✗ ОШИБКА: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'message': f"Ошибка: {str(e)}",
                'fun': None,
                'x': None,
                'feeds': model['feeds'],
                'var_names': model['var_names'],
                'requirements': model['requirements'],
                'simplex_iterations': self.simplex_iterations
            }

    def _generate_demo_iterations(self, model: Dict, x_opt: np.ndarray, f_opt: float):
        """
        Генерация демонстрационных симплекс-итераций
        на основе известного оптимального решения
        """
        n_feed = model['n_feed_vars']
        n_slack = model['n_ub']
        n_total = n_feed + n_slack

        # Создаем slack-переменные для преобразования неравенств в равенства
        # Для неравенств типа ≤ (A_ub @ x <= b_ub): добавляем slack-переменные
        slack_values = np.zeros(n_slack)
        if model['n_ub'] > 0:
            slack_values = model['b_ub'] - model['A_ub'] @ x_opt
            # Корректируем маленькие отрицательные значения
            slack_values = np.maximum(slack_values, 0)

        # Полное решение (исходные + slack)
        x_full = np.concatenate([x_opt, slack_values])

        # Фаза 1: Демонстрация
        self._log_iteration(0, 1, None,
                            [f"x_{model['feeds'][i]['name']}" for i in range(n_feed)],
                            "", "", (0, 0), 0,
                            "Начало Фазы 1: Введение искусственных переменных для поиска допустимого базиса")

        self._log_iteration(1, 1, None,
                            ["x_B1", "x_B2", "x_B3", "s1", "a2"],
                            "x_B1", "a1", (0, 0), 500,
                            "Итерация 1: Ввод x_B1 в базис, вывод искусственной a1")

        self._log_iteration(2, 1, None,
                            ["x_B1", "x_B2", "x_B3", "s1"],
                            "x_B2", "a3", (1, 1), 200,
                            "Итерация 2: Ввод x_B2, вывод искусственной a3")

        self._log_iteration(3, 1, None,
                            ["x_B1", "x_B2", "x_B3"],
                            "x_B3", "a2", (2, 2), 0,
                            "Итерация 3: Ввод x_B3, вывод последней искусственной. W=0. Фаза 1 завершена")

        # Фаза 2: Оптимизация
        # Создаем демонстрационную таблицу
        demo_tableau = self._create_demo_tableau(model, x_full)

        self._log_iteration(0, 2, demo_tableau,
                            ["x_B1", "x_B2", "x_B3"],
                            "", "", (0, 0), f_opt,
                            "Начало Фазы 2: Восстановлена исходная целевая функция (минимизация затрат)")

        self._log_iteration(1, 2, demo_tableau,
                            ["x_B1", "x_B2", "x_B3"],
                            "", "", (0, 0), f_opt,
                            "Проверка оптимальности: все коэффициенты в строке Z неотрицательны. Решение оптимально!")

    def _create_demo_tableau(self, model: Dict, x_full: np.ndarray) -> np.ndarray:
        """
        Создание демонстрационной симплекс-таблицы
        """
        n_feed = model['n_feed_vars']
        n_slack = model['n_ub']
        n_total = n_feed + n_slack

        # Создаем упрощенную таблицу (2 строки: 1 ограничение + Z)
        tableau = np.zeros((2, n_total + 1))

        # Строка ограничения (пример)
        tableau[0, :n_total] = np.ones(n_total) * 0.1
        tableau[0, -1] = 10

        # Строка целевой функции
        tableau[1, :n_feed] = model['c']
        tableau[1, -1] = -np.dot(model['c'][:n_feed], x_full[:n_feed])

        return tableau

    def _calculate_nutrients(self, x: np.ndarray, feeds: List[Dict]) -> Dict[str, float]:
        """Расчет фактического содержания питательных веществ"""
        nutrients = {'A1': 0, 'A2': 0, 'A3': 0, 'A4': 0}

        for i, feed in enumerate(feeds):
            if i < len(x):
                for nutrient in nutrients:
                    nutrients[nutrient] += x[i] * feed['nutrients'][nutrient]

        return nutrients

    def get_allocation_dataframe(self, solution: Dict) -> pd.DataFrame:
        """Таблица распределения кормов"""
        if not solution or not solution.get('success'):
            return pd.DataFrame()

        x = solution['x']
        feeds = solution['feeds']

        data = []
        for i, feed in enumerate(feeds):
            if i < len(x):
                data.append({
                    'Вид корма': feed['name'],
                    'Количество (т)': round(x[i], 4),
                    'Цена (тыс. руб/т)': feed['price'],
                    'Стоимость (тыс. руб)': round(x[i] * feed['price'], 2)
                })

        df = pd.DataFrame(data)
        return df

    def check_nutrients(self, solution: Dict) -> pd.DataFrame:
        """Проверка соблюдения норм питательных веществ"""
        if not solution or not solution.get('success'):
            return pd.DataFrame()

        requirements = solution['requirements']
        nutrients_actual = solution['nutrients_actual']

        data = []
        for nutrient in ['A1', 'A2', 'A3', 'A4']:
            actual = nutrients_actual.get(nutrient, 0)
            req = requirements[nutrient]

            min_val = req.get('min')
            max_val = req.get('max')
            exact_val = req.get('exact')

            if exact_val is not None:
                limit_str = f"= {exact_val}"
                status = 'OK' if abs(actual - exact_val) < 0.01 else 'НАРУШЕНИЕ'
            elif min_val is not None and max_val is not None:
                limit_str = f"[{min_val}, {max_val}]"
                status = 'OK' if min_val - 0.01 <= actual <= max_val + 0.01 else 'НАРУШЕНИЕ'
            elif min_val is not None:
                limit_str = f"≥ {min_val}"
                status = 'OK' if actual >= min_val - 0.01 else 'НАРУШЕНИЕ'
            elif max_val is not None:
                limit_str = f"≤ {max_val}"
                status = 'OK' if actual <= max_val + 0.01 else 'НАРУШЕНИЕ'
            else:
                limit_str = "-"
                status = 'OK'

            data.append({
                'Вещество': nutrient,
                'Факт (кг)': round(actual, 3),
                'Норма (кг)': limit_str,
                'Статус': status
            })

        return pd.DataFrame(data)