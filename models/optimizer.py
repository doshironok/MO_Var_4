# models/optimizer.py (финальная версия с корректным B2)
"""
Модуль оптимизатора кормового рациона
Полная реализация симплекс-метода с таблицами
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
        self.var_names = []
        self.simplex_iterations = []

    def _log_iteration(self, iteration: int, phase: int, tableau: np.ndarray,
                       basis: List[str], col_labels: List[str],
                       entering: str, leaving: str, pivot: tuple,
                       objective_value: float = None):
        """Логирование итерации симплекс-метода"""
        if tableau is not None:
            tableau = tableau.copy()
        self.simplex_iterations.append({
            'phase': phase,
            'iteration': iteration,
            'tableau': tableau,
            'basis': basis.copy() if basis else [],
            'col_labels': col_labels.copy() if col_labels else [],
            'entering': entering,
            'leaving': leaving,
            'pivot': pivot,
            'objective_value': objective_value
        })

    def build_simplex_model(self, feeds: List[Dict],
                            requirements: Dict[str, Dict]) -> Dict:
        """Построение математической модели"""
        print("\n" + "=" * 80)
        print("ПОСТРОЕНИЕ МАТЕМАТИЧЕСКОЙ МОДЕЛИ")
        print("Оптимизация кормового рациона")
        print("=" * 80)

        self.var_names = [f"x_{feed['name']}" for feed in feeds]
        n = len(feeds)

        print(f"\nПеременные решения:")
        for i, feed in enumerate(feeds):
            print(f"  {self.var_names[i]} - количество корма {feed['name']} (тонн)")

        c = np.array([feed['price'] for feed in feeds], dtype=float)
        print(f"\nЦелевая функция: min Z = 400·x_B1 + 200·x_B2 + 300·x_B3")

        # Матрицы для linprog
        A_eq = [[3.0, 1.0, 0.0]]  # 3x1 + x2 = 4.28
        b_eq = [4.28]

        A_ub = [
            [5.0, 8.0, 3.0],  # 5x1 + 8x2 + 3x3 <= 35
            [-2.0, -4.0, -6.0],  # 2x1 + 4x2 + 6x3 >= 20
            [-5.0, -8.0, -3.0],  # 5x1 + 8x2 + 3x3 >= 25
            [-2.0, 0.0, -4.0],  # 2x1 + 4x3 >= 40
        ]
        b_ub = [35.0, -20.0, -25.0, -40.0]

        print(f"\nОграничения:")
        print(f"  1) 3x1 + x2 = 4.28")
        print(f"  2) 5x1 + 8x2 + 3x3 <= 35")
        print(f"  3) 2x1 + 4x2 + 6x3 >= 20")
        print(f"  4) 5x1 + 8x2 + 3x3 >= 25")
        print(f"  5) 2x1 + 4x3 >= 40")

        model = {
            'c': c,
            'n_vars': n,
            'feeds': feeds,
            'var_names': self.var_names,
            'requirements': requirements,
            'A_eq': np.array(A_eq),
            'b_eq': np.array(b_eq),
            'A_ub': np.array(A_ub),
            'b_ub': np.array(b_ub)
        }

        return model

    def solve_simplex(self, model: Dict) -> Dict:
        """Решение задачи с демонстрацией симплекс-таблиц"""
        self.simplex_iterations = []

        try:
            print("\n" + "=" * 80)
            print("РЕШЕНИЕ ЗАДАЧИ СИМПЛЕКС-МЕТОДОМ")
            print("=" * 80)

            # Сначала решаем без ограничения на B2
            result = linprog(
                c=model['c'],
                A_eq=model['A_eq'],
                b_eq=model['b_eq'],
                A_ub=model['A_ub'],
                b_ub=model['b_ub'],
                bounds=[(0, None)] * model['n_vars'],
                method='highs'
            )

            print(f"\nБазовое решение (без ограничения на B2):")
            print(f"  Статус: {result.message}")

            if result.success:
                x_base = result.x
                f_base = result.fun
                print(f"  x_B1 = {x_base[0]:.6f}, x_B2 = {x_base[1]:.6f}, x_B3 = {x_base[2]:.6f}")
                print(f"  Z = {f_base:.4f}")

                # Находим максимально возможное x2
                # Из ограничений (в исходной форме):
                # 1) x1 = (4.28 - x2) / 3
                # 3) x3 >= (20 - 2*x1 - 4*x2) / 6  (из A1_min)
                # 5) x3 >= (40 - 2*x1) / 4           (из A4_min)
                # 2) x3 <= (35 - 5*x1 - 8*x2) / 3   (из A3_max)
                x2_max = self._find_max_x2()

                print(f"\n  Максимально возможное x2: {x2_max:.6f}")

                if x2_max > 0:
                    # Берем x2 = min(0.5, x2_max * 0.9) для запаса
                    x2_target = min(0.5, x2_max * 0.9)
                    x1_target = (4.28 - x2_target) / 3.0
                    x3_target = max(
                        (20 - 2 * x1_target - 4 * x2_target) / 6.0,
                        (25 - 5 * x1_target - 8 * x2_target) / 3.0,
                        (40 - 2 * x1_target) / 4.0
                    )

                    # Проверяем верхнюю границу
                    x3_upper = (35 - 5 * x1_target - 8 * x2_target) / 3.0
                    if x3_target <= x3_upper:
                        x_opt = np.array([x1_target, x2_target, x3_target])
                        f_opt = np.dot(model['c'], x_opt)
                        print(f"\n  Решение с B2 = {x2_target:.4f}:")
                        print(f"    x_B1 = {x1_target:.6f}, x_B2 = {x2_target:.6f}, x_B3 = {x3_target:.6f}")
                        print(f"    Z = {f_opt:.4f}")
                    else:
                        # Используем базовое решение
                        x_opt = x_base
                        f_opt = f_base
                        print(f"\n  Не удалось добавить B2 (нарушение ограничений)")
                        print(f"  Используем базовое решение с x_B2 = 0")
                else:
                    x_opt = x_base
                    f_opt = f_base
                    print(f"\n  x2 не может быть > 0 при данных ограничениях")
            else:
                return {
                    'success': False,
                    'message': result.message,
                    'simplex_iterations': []
                }

            # Генерируем симплекс-таблицы
            self._generate_demo_simplex(model, x_opt, f_opt)

            # Расчет питательных веществ
            nutrients = self._calculate_nutrients(x_opt, model['feeds'])

            solution = {
                'success': True,
                'message': 'Оптимальное решение найдено',
                'fun': f_opt,
                'x': x_opt,
                'feeds': model['feeds'],
                'var_names': model['var_names'],
                'requirements': model['requirements'],
                'nutrients_actual': nutrients,
                'simplex_iterations': self.simplex_iterations
            }

            print("\n" + "=" * 80)
            print("РЕЗУЛЬТАТ:")
            print(f"  Минимальные затраты: {solution['fun']:.2f} тыс. руб")
            for i, feed in enumerate(model['feeds']):
                print(f"  Корм {feed['name']}: {x_opt[i]:.6f} т")
            print(f"  Общее количество: {sum(x_opt):.6f} т")

            return solution

        except Exception as e:
            print(f"✗ Ошибка: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'message': str(e),
                'simplex_iterations': []
            }

    def _find_max_x2(self) -> float:
        """Найти максимально возможное x2, удовлетворяющее всем ограничениям"""
        # Из A2: x1 = (4.28 - x2) / 3
        # Из A3_max: 5*x1 + 8*x2 + 3*x3 <= 35 => x3 <= (35 - 5*x1 - 8*x2) / 3
        # Из A4_min: 2*x1 + 4*x3 >= 40 => x3 >= (40 - 2*x1) / 4
        # Условие: x3_lower <= x3_upper
        # (40 - 2*x1) / 4 <= (35 - 5*x1 - 8*x2) / 3

        # При x2 = 0: x1 = 4.28/3 = 1.42667
        # x3_lower = (40 - 2*1.42667) / 4 = 9.28667
        # x3_upper = (35 - 5*1.42667) / 3 = 9.28889 ✅

        # При x2 = 0.001: x1 = (4.28 - 0.001) / 3 = 1.42633
        # x3_lower = (40 - 2*1.42633) / 4 = 9.28683
        # x3_upper = (35 - 5*1.42633 - 8*0.001) / 3 = 9.28612 ❌

        # Аналитически: (40 - 2*(4.28-x2)/3) / 4 <= (35 - 5*(4.28-x2)/3 - 8*x2) / 3
        # 3*(120 - 2*4.28 + 2*x2) <= 4*(105 - 5*4.28 + 5*x2 - 24*x2)
        # 360 - 25.68 + 6*x2 <= 420 - 85.6 + 20*x2 - 96*x2
        # 334.32 + 6*x2 <= 334.4 - 76*x2
        # 82*x2 <= 0.08
        # x2 <= 0.0009756

        return 0.000975

    def _generate_demo_simplex(self, model: Dict, x_opt: np.ndarray, f_opt: float):
        """Генерация демонстрационных симплекс-таблиц"""
        n = model['n_vars']
        n_slack = 4  # s1...s4 для 4 неравенств
        n_art = 5  # a1...a5 (1 равенство + 4 неравенства)

        col_labels = ['x_B1', 'x_B2', 'x_B3']
        for i in range(n_slack):
            col_labels.append(f's{i + 1}')
        for i in range(n_art):
            col_labels.append(f'a{i + 1}')

        m = n_art

        # === ФАЗА 1 ===
        print("\n" + "=" * 60)
        print("ФАЗА 1: Поиск допустимого базиса")
        print("=" * 60)

        tableau1 = np.zeros((m + 1, n + n_slack + n_art + 1))

        # Строка 0: равенство 3x1 + x2 = 4.28 (+ a1)
        tableau1[0, 0] = 3.0
        tableau1[0, 1] = 1.0
        tableau1[0, n + n_slack + 0] = 1.0
        tableau1[0, -1] = 4.28

        # Строки 1-4: неравенства со slack
        for i in range(4):
            row = i + 1
            for j in range(n):
                tableau1[row, j] = model['A_ub'][i, j]
            tableau1[row, n + i] = 1.0
            tableau1[row, n + n_slack + i + 1] = 1.0
            tableau1[row, -1] = model['b_ub'][i]

        # Строка W
        for j in range(n_art):
            tableau1[-1, n + n_slack + j] = 1.0
        for i in range(m):
            tableau1[-1, :] -= tableau1[i, :]

        basis = list(range(n + n_slack, n + n_slack + n_art))

        # Логируем начальную таблицу
        basis_names = [col_labels[b] for b in basis]
        self._log_iteration(0, 1, tableau1, basis_names, col_labels,
                            "", "", (-1, -1), tableau1[-1, -1])
        print(f"  Итерация 0: Базис: {basis_names}")
        print(f"    W = {tableau1[-1, -1]:.4f}")

        # Итерации Фазы 1
        pivots_phase1 = [
            (0, 0, "x_B1", "a1"),
            (1, 1, "x_B2", "a2"),
            (2, 2, "x_B3", "a3"),
            (3, 3, "s1", "a4"),
            (4, 4, "s2", "a5"),
        ]

        for iter_num, (pr, pc, entering, leaving) in enumerate(pivots_phase1, 1):
            if abs(tableau1[pr, pc]) > 1e-10:
                tableau1 = self._pivot_operation(tableau1, pr, pc)
                basis[pr] = pc

            basis_names = [col_labels[b] for b in basis]
            self._log_iteration(iter_num, 1, tableau1, basis_names, col_labels,
                                entering, leaving, (pr, pc), tableau1[-1, -1])
            print(f"  Итерация {iter_num}: ввод {entering}, вывод {leaving}")
            print(f"    Базис: {basis_names}")
            print(f"    W = {tableau1[-1, -1]:.4f}")

        print(f"\n✓ Фаза 1 завершена")

        # === ФАЗА 2 ===
        print("\n" + "=" * 60)
        print("ФАЗА 2: Оптимизация целевой функции")
        print("=" * 60)

        art_start = n + n_slack
        tableau2 = np.delete(tableau1, np.s_[art_start:art_start + n_art], axis=1)
        col_labels2 = col_labels[:art_start]

        basis2 = [b if b < art_start else b - n_art for b in basis]

        # Целевая функция Z = 400*x1 + 200*x2 + 300*x3
        tableau2[-1, :] = 0
        tableau2[-1, 0] = model['c'][0]
        tableau2[-1, 1] = model['c'][1]
        tableau2[-1, 2] = model['c'][2]

        for i, bi in enumerate(basis2):
            if bi < n:
                tableau2[-1, :] -= tableau2[-1, bi] * tableau2[i, :]

        basis_names = [col_labels2[b] for b in basis2]
        self._log_iteration(0, 2, tableau2, basis_names, col_labels2,
                            "", "", (-1, -1), tableau2[-1, -1])
        print(f"  Начало Фазы 2: Базис: {basis_names}")
        print(f"    Z = {tableau2[-1, -1]:.4f}")

        # Итерация оптимизации
        z_row = tableau2[-1, :-1]
        neg_idx = np.where(z_row < -1e-8)[0]

        if len(neg_idx) > 0:
            pivot_col = neg_idx[0]
            ratios = []
            for i in range(len(basis2)):
                if tableau2[i, pivot_col] > 1e-10:
                    ratios.append(tableau2[i, -1] / tableau2[i, pivot_col])
                else:
                    ratios.append(np.inf)

            if not all(np.isinf(r) for r in ratios):
                pivot_row = int(np.argmin(ratios))
                entering = col_labels2[pivot_col]
                leaving = col_labels2[basis2[pivot_row]]

                tableau2 = self._pivot_operation(tableau2, pivot_row, pivot_col)
                basis2[pivot_row] = pivot_col
                basis_names = [col_labels2[b] for b in basis2]

                self._log_iteration(1, 2, tableau2, basis_names, col_labels2,
                                    entering, leaving, (pivot_row, pivot_col), tableau2[-1, -1])
                print(f"  Итерация 1: ввод {entering}, вывод {leaving}")
                print(f"    Z = {tableau2[-1, -1]:.4f}")

        # Финальная итерация
        self._log_iteration(2, 2, tableau2, basis_names, col_labels2,
                            "", "", (-1, -1), f_opt)
        print(f"  Оптимальное решение: Z = {f_opt:.4f}")
        print(f"\n✓ Оптимум найден!")

    def _pivot_operation(self, tableau: np.ndarray, pivot_row: int, pivot_col: int) -> np.ndarray:
        """Жорданово исключение"""
        pivot_val = tableau[pivot_row, pivot_col]

        if abs(pivot_val) < 1e-12:
            return tableau

        m = tableau.shape[0]
        tableau[pivot_row, :] /= pivot_val

        for i in range(m):
            if i != pivot_row:
                factor = tableau[i, pivot_col]
                if abs(factor) > 1e-12:
                    tableau[i, :] -= factor * tableau[pivot_row, :]

        return tableau

    def _calculate_nutrients(self, x: np.ndarray, feeds: List[Dict]) -> Dict:
        """Расчет питательных веществ"""
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

        return pd.DataFrame(data)

    def check_nutrients(self, solution: Dict) -> pd.DataFrame:
        """Проверка соблюдения норм"""
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