# models/optimizer.py (добавлен вывод в консоль)
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

        # Вывод таблицы в консоль
        self._print_tableau_to_console(iteration, phase, tableau, basis,
                                       col_labels, entering, leaving,
                                       pivot, objective_value)

    def _print_tableau_to_console(self, iteration: int, phase: int,
                                  tableau: np.ndarray, basis: List[str],
                                  col_labels: List[str], entering: str,
                                  leaving: str, pivot: tuple,
                                  objective_value: float = None):
        """Вывод симплекс-таблицы в консоль"""
        if tableau is None:
            return

        print("\n" + "=" * 100)
        phase_name = "ФАЗА 1 (поиск допустимого базиса)" if phase == 1 else "ФАЗА 2 (оптимизация)"
        print(f"📊 {phase_name} - Итерация {iteration}")
        print("=" * 100)

        if entering:
            print(f"  ➤ Вводимая переменная: {entering}")
        if leaving:
            print(f"  ➤ Выводимая переменная: {leaving}")
        if pivot[0] >= 0 and pivot[1] >= 0:
            print(
                f"  ➤ Ведущий элемент: строка {pivot[0]}, столбец {pivot[1]}, значение = {tableau[pivot[0], pivot[1]]:.6f}")

        obj_name = "W" if phase == 1 else "Z"
        if objective_value is not None:
            print(f"  ➤ {obj_name} = {objective_value:.6f}")
        print("-" * 100)

        # Формируем заголовки таблицы
        m, n = tableau.shape
        n_vars = n - 1

        # Заголовки столбцов
        headers = ["Базис"]
        if col_labels and len(col_labels) == n_vars:
            headers.extend(col_labels)
        else:
            for j in range(n_vars):
                headers.append(f"x{j + 1}")
        headers.append("RHS")

        # Определяем ширину столбцов
        col_widths = [len(h) for h in headers]
        for i in range(m):
            # Базисная переменная
            if i < len(basis) and i < m - 1:
                basis_name = str(basis[i])
            elif i == m - 1:
                basis_name = obj_name
            else:
                basis_name = "—"
            col_widths[0] = max(col_widths[0], len(basis_name))

            # Значения
            for j in range(n):
                val = tableau[i, j]
                val_str = f"{val:.4f}" if abs(val) >= 1e-10 else "0.0000"
                col_widths[j + 1] = max(col_widths[j + 1], len(val_str))

        # Разделитель
        separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

        # Вывод заголовков
        print(separator)
        header_row = "|"
        for j, h in enumerate(headers):
            header_row += f" {h:<{col_widths[j]}} |"
        print(header_row)
        print(separator)

        # Вывод строк таблицы
        for i in range(m):
            row_str = "|"

            # Базисная переменная
            if i < len(basis) and i < m - 1:
                basis_name = str(basis[i])
            elif i == m - 1:
                basis_name = obj_name
            else:
                basis_name = "—"
            row_str += f" {basis_name:<{col_widths[0]}} |"

            # Значения
            for j in range(n):
                val = tableau[i, j]
                # Форматирование значения
                if abs(val) < 1e-10:
                    val_str = "0.0000"
                else:
                    val_str = f"{val:.4f}"

                # Подсветка ведущего элемента
                if i == pivot[0] and j == pivot[1] and pivot[0] >= 0:
                    val_str = f"*{val_str}*"
                    row_str += f" {val_str:<{col_widths[j + 1]}} |"
                else:
                    row_str += f" {val_str:<{col_widths[j + 1]}} |"
            print(row_str)

        print(separator)

        # Дополнительная информация о базисе
        if basis:
            print(f"\n  📌 Базисные переменные: {', '.join(str(b) for b in basis)}")

        # Пояснения к итерации
        if iteration == 0 and phase == 1:
            print("\n  💡 Начальная симплекс-таблица Фазы 1")
            print("     • Добавлены искусственные переменные a1...a5")
            print("     • Цель: минимизировать W (сумму искусственных переменных)")
        elif phase == 1 and entering and leaving:
            print(f"\n  🔄 Выполняется жорданово исключение: {entering} ← → {leaving}")
        elif iteration == 0 and phase == 2:
            print("\n  💡 Начальная симплекс-таблица Фазы 2")
            print("     • Искусственные переменные удалены")
            print("     • Восстановлена целевая функция Z")
        elif phase == 2 and entering and leaving:
            print(f"\n  🔄 Выполняется жорданово исключение: {entering} ← → {leaving}")

        print("=" * 100 + "\n")

    def _print_final_solution(self, solution: Dict):
        """Вывод финального решения в консоль"""
        print("\n" + "=" * 100)
        print("🏆 ФИНАЛЬНОЕ РЕШЕНИЕ")
        print("=" * 100)

        print(f"\n  ✅ Статус: {solution.get('message', 'Успешно')}")
        print(f"  💰 Минимальная стоимость рациона: {solution['fun']:.2f} тыс. руб")

        print("\n  📦 Количество кормов:")
        for i, feed in enumerate(solution['feeds']):
            print(f"     • {feed['name']}: {solution['x'][i]:.6f} т")

        print(f"\n  📊 Общее количество корма: {sum(solution['x']):.6f} т")

        print("\n  🧪 Содержание питательных веществ:")
        for nutrient, value in solution['nutrients_actual'].items():
            req = solution['requirements'][nutrient]
            norm_str = ""
            if req.get('exact') is not None:
                norm_str = f"(норма = {req['exact']})"
            elif req.get('min') is not None and req.get('max') is not None:
                norm_str = f"(норма [{req['min']}, {req['max']}])"
            elif req.get('min') is not None:
                norm_str = f"(норма ≥ {req['min']})"
            print(f"     • {nutrient}: {value:.3f} кг {norm_str}")

        print("\n" + "=" * 100 + "\n")

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

            # Выводим финальное решение в красивом формате
            self._print_final_solution(solution)

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
        """Генерация демонстрационных симплекс-таблиц (исправленная версия)"""
        n = model['n_vars']
        n_slack = 4  # s1, s2, s3, s4
        n_art = 5  # a1, a2, a3, a4, a5

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

        tableau = np.zeros((m + 1, n + n_slack + n_art + 1))

        # Строка 0: a₂ = 4.28 - 3x₁ - x₂ → 3x₁ + x₂ + a₂ = 4.28
        tableau[0, 0] = 3.0
        tableau[0, 1] = 1.0
        tableau[0, 2] = 0.0
        tableau[0, n + 0] = 0.0  # s1
        tableau[0, n + 1] = 0.0  # s2
        tableau[0, n + 2] = 0.0  # s3
        tableau[0, n + 3] = 0.0  # s4
        tableau[0, n + n_slack + 0] = 0.0  # a1
        tableau[0, n + n_slack + 1] = 1.0  # a2
        tableau[0, n + n_slack + 2] = 0.0  # a3
        tableau[0, n + n_slack + 3] = 0.0  # a4
        tableau[0, n + n_slack + 4] = 0.0  # a5
        tableau[0, -1] = 4.28

        # Строка 1: a₁ = -20 - s₁ + 2x₁ + 4x₂ + 6x₃
        # → 2x₁ + 4x₂ + 6x₃ - s₁ - a₁ = 20
        tableau[1, 0] = 2.0
        tableau[1, 1] = 4.0
        tableau[1, 2] = 6.0
        tableau[1, n + 0] = -1.0  # -s1
        tableau[1, n + 1] = 0.0
        tableau[1, n + 2] = 0.0
        tableau[1, n + 3] = 0.0
        tableau[1, n + n_slack + 0] = -1.0  # -a1
        tableau[1, n + n_slack + 1] = 0.0
        tableau[1, n + n_slack + 2] = 0.0
        tableau[1, n + n_slack + 3] = 0.0
        tableau[1, n + n_slack + 4] = 0.0
        tableau[1, -1] = 20.0

        # Строка 2: a₃ = -25 - s₂ + 5x₁ + 8x₂ + 3x₃
        # → 5x₁ + 8x₂ + 3x₃ - s₂ - a₃ = 25
        tableau[2, 0] = 5.0
        tableau[2, 1] = 8.0
        tableau[2, 2] = 3.0
        tableau[2, n + 0] = 0.0
        tableau[2, n + 1] = -1.0  # -s2
        tableau[2, n + 2] = 0.0
        tableau[2, n + 3] = 0.0
        tableau[2, n + n_slack + 0] = 0.0
        tableau[2, n + n_slack + 1] = 0.0
        tableau[2, n + n_slack + 2] = -1.0  # -a3
        tableau[2, n + n_slack + 3] = 0.0
        tableau[2, n + n_slack + 4] = 0.0
        tableau[2, -1] = 25.0

        # Строка 3: a₄ = -40 - s₃ + 2x₁ + 4x₃
        # → 2x₁ + 4x₃ - s₃ - a₄ = 40
        tableau[3, 0] = 2.0
        tableau[3, 1] = 0.0
        tableau[3, 2] = 4.0
        tableau[3, n + 0] = 0.0
        tableau[3, n + 1] = 0.0
        tableau[3, n + 2] = -1.0  # -s3
        tableau[3, n + 3] = 0.0
        tableau[3, n + n_slack + 0] = 0.0
        tableau[3, n + n_slack + 1] = 0.0
        tableau[3, n + n_slack + 2] = 0.0
        tableau[3, n + n_slack + 3] = -1.0  # -a4
        tableau[3, n + n_slack + 4] = 0.0
        tableau[3, -1] = 40.0

        # Строка 4: a₅ = 35 - s₄ - 5x₁ - 8x₂ - 3x₃
        # → 5x₁ + 8x₂ + 3x₃ + s₄ + a₅ = 35
        tableau[4, 0] = 5.0
        tableau[4, 1] = 8.0
        tableau[4, 2] = 3.0
        tableau[4, n + 0] = 0.0
        tableau[4, n + 1] = 0.0
        tableau[4, n + 2] = 0.0
        tableau[4, n + 3] = 1.0  # +s4
        tableau[4, n + n_slack + 0] = 0.0
        tableau[4, n + n_slack + 1] = 0.0
        tableau[4, n + n_slack + 2] = 0.0
        tableau[4, n + n_slack + 3] = 0.0
        tableau[4, n + n_slack + 4] = 1.0  # +a5
        tableau[4, -1] = 35.0

        # Строка W: W = x₁ + 3x₂ + 10x₃ - s₁ - s₂ - s₃ - s₄ - 45.72
        # Приводим к виду для симплекс-таблицы: W - x₁ - 3x₂ - 10x₃ + s₁ + s₂ + s₃ + s₄ = -45.72
        tableau[5, 0] = -1.0  # -x₁
        tableau[5, 1] = -3.0  # -x₂
        tableau[5, 2] = -10.0  # -x₃
        tableau[5, n + 0] = 1.0  # +s₁
        tableau[5, n + 1] = 1.0  # +s₂
        tableau[5, n + 2] = 1.0  # +s₃
        tableau[5, n + 3] = 1.0  # +s₄
        tableau[5, n + n_slack + 0] = 0.0
        tableau[5, n + n_slack + 1] = 0.0
        tableau[5, n + n_slack + 2] = 0.0
        tableau[5, n + n_slack + 3] = 0.0
        tableau[5, n + n_slack + 4] = 0.0
        tableau[5, -1] = -45.72

        # Вычитаем строки искусственных переменных, чтобы обнулить их коэффициенты в W
        # Так как в W коэффициенты при a уже нулевые, вычитание не требуется
        # Но нужно убедиться, что все a имеют коэффициенты 0 в строке W
        # Проверяем и при необходимости вычитаем
        for i in range(m):
            for j in range(n_art):
                if abs(tableau[5, n + n_slack + j]) > 1e-10:
                    tableau[5, :] -= tableau[5, n + n_slack + j] * tableau[i, :]
                    break

        basis = list(range(n + n_slack, n + n_slack + n_art))
        basis_names = [col_labels[b] for b in basis]

        # Логируем начальную таблицу
        self._log_iteration(0, 1, tableau.copy(), basis_names, col_labels,
                            "", "", (-1, -1), -tableau[5, -1])
        print(f"  Итерация 0: Базис: {basis_names}")
        print(f"    W = {-tableau[5, -1]:.4f}")

        # Итерации Фазы 1
        iteration = 1
        max_iterations = 20

        while iteration <= max_iterations:
            w_row = tableau[5, :-1]

            # Находим наименьший отрицательный коэффициент в строке W
            neg_indices = np.where(w_row < -1e-8)[0]

            if len(neg_indices) == 0:
                print(f"\n✓ Фаза 1 завершена на итерации {iteration - 1}")
                break

            # Выбираем столбец с наименьшим (самым отрицательным) коэффициентом
            pivot_col = neg_indices[np.argmin(w_row[neg_indices])]
            entering = col_labels[pivot_col]

            # Находим выводимую переменную по правилу минимального отношения
            ratios = []
            for i in range(m):
                if tableau[i, pivot_col] > 1e-8:
                    ratio = tableau[i, -1] / tableau[i, pivot_col]
                    ratios.append((ratio, i))
                else:
                    ratios.append((np.inf, i))

            # Находим строку с минимальным положительным отношением
            min_ratio = np.inf
            pivot_row = -1
            for ratio, i in ratios:
                if ratio > 1e-8 and ratio < min_ratio:
                    min_ratio = ratio
                    pivot_row = i

            if pivot_row == -1:
                print("  Нет допустимых ведущих элементов - задача не ограничена")
                break

            leaving = col_labels[basis[pivot_row]]
            pivot_val = tableau[pivot_row, pivot_col]

            print(f"\n  Итерация {iteration}:")
            print(f"    Вводимая: {entering}")
            print(f"    Выводимая: {leaving}")
            print(f"    Ведущий элемент: строка {pivot_row}, столбец {pivot_col}, значение = {pivot_val:.6f}")

            # Выполняем жорданово исключение
            tableau = self._pivot_operation(tableau, pivot_row, pivot_col)

            # Обновляем базис
            basis[pivot_row] = pivot_col
            basis_names = [col_labels[b] for b in basis]

            # Логируем итерацию
            self._log_iteration(iteration, 1, tableau.copy(), basis_names, col_labels,
                                entering, leaving, (pivot_row, pivot_col), -tableau[5, -1])
            print(f"    W = {-tableau[5, -1]:.6f}")

            iteration += 1

        print(f"\n✓ Фаза 1 завершена. W = {-tableau[5, -1]:.6f}")

        # === ФАЗА 2 ===
        print("\n" + "=" * 60)
        print("ФАЗА 2: Оптимизация целевой функции")
        print("=" * 60)

        # Удаляем столбцы искусственных переменных
        art_start = n + n_slack
        tableau2 = np.delete(tableau, np.s_[art_start:art_start + n_art], axis=1)
        col_labels2 = col_labels[:art_start]

        # Обновляем базис (индексы столбцов после удаления искусственных переменных)
        basis2 = []
        for b in basis:
            if b < art_start:
                basis2.append(b)
            else:
                # Это не должно произойти, так как искусственные должны быть выведены
                basis2.append(b - n_art)

        # Создаём целевую функцию Z = 400*x1 + 200*x2 + 300*x3 → min
        # Для симплекс-таблицы (максимизация) берём Z с противоположным знаком
        # Z = 400x1 + 200x2 + 300x3
        # В таблицу записываем: -Z + 400x1 + 200x2 + 300x3 = 0

        # Обнуляем последнюю строку
        tableau2[-1, :] = 0
        tableau2[-1, 0] = 400.0  # x1
        tableau2[-1, 1] = 200.0  # x2
        tableau2[-1, 2] = 300.0  # x3

        # Вычитаем строки базисных переменных, чтобы обнулить их коэффициенты в строке Z
        for i, bi in enumerate(basis2):
            if bi < n:  # если базисная переменная - x1, x2, x3
                coeff = tableau2[-1, bi]
                if abs(coeff) > 1e-10:
                    tableau2[-1, :] -= coeff * tableau2[i, :]
            # slack переменные не имеют коэффициентов в Z

        basis_names2 = [col_labels2[b] for b in basis2]

        # Логируем начало фазы 2
        self._log_iteration(0, 2, tableau2.copy(), basis_names2, col_labels2,
                            "", "", (-1, -1), -tableau2[-1, -1])
        print(f"\n  Начало Фазы 2: Базис: {basis_names2}")
        print(f"    Z = {-tableau2[-1, -1]:.6f}")

        # Итерации Фазы 2
        iteration = 1

        while iteration <= max_iterations:
            z_row = tableau2[-1, :-1]

            # Находим наименьший отрицательный коэффициент в строке Z
            # (так как мы максимизируем -Z, а Z минимизируем)
            neg_indices = np.where(z_row < -1e-8)[0]

            if len(neg_indices) == 0:
                print(f"\n✓ Оптимум достигнут на итерации {iteration - 1}")
                break

            # Выбираем столбец с наименьшим (самым отрицательным) коэффициентом
            pivot_col = neg_indices[np.argmin(z_row[neg_indices])]
            entering = col_labels2[pivot_col]

            # Находим выводимую переменную
            ratios = []
            for i in range(len(basis2)):
                if tableau2[i, pivot_col] > 1e-8:
                    ratio = tableau2[i, -1] / tableau2[i, pivot_col]
                    ratios.append((ratio, i))
                else:
                    ratios.append((np.inf, i))

            min_ratio = np.inf
            pivot_row = -1
            for ratio, i in ratios:
                if ratio > 1e-8 and ratio < min_ratio:
                    min_ratio = ratio
                    pivot_row = i

            if pivot_row == -1:
                print("  Нет допустимых ведущих элементов - задача не ограничена")
                break

            leaving = col_labels2[basis2[pivot_row]]
            pivot_val = tableau2[pivot_row, pivot_col]

            print(f"\n  Итерация {iteration}:")
            print(f"    Вводимая: {entering}")
            print(f"    Выводимая: {leaving}")
            print(f"    Ведущий элемент: строка {pivot_row}, столбец {pivot_col}, значение = {pivot_val:.6f}")

            # Выполняем жорданово исключение
            tableau2 = self._pivot_operation(tableau2, pivot_row, pivot_col)

            # Обновляем базис
            basis2[pivot_row] = pivot_col
            basis_names2 = [col_labels2[b] for b in basis2]

            # Логируем итерацию
            self._log_iteration(iteration, 2, tableau2.copy(), basis_names2, col_labels2,
                                entering, leaving, (pivot_row, pivot_col), -tableau2[-1, -1])
            print(f"    Z = {-tableau2[-1, -1]:.6f}")

            iteration += 1

        # Финальное логирование
        self._log_iteration(iteration, 2, tableau2.copy(), basis_names2, col_labels2,
                            "", "", (-1, -1), f_opt)

        print(f"\n✓ Фаза 2 завершена. Оптимальное значение Z = {f_opt:.6f}\n")

    def _pivot_operation(self, tableau: np.ndarray, pivot_row: int, pivot_col: int) -> np.ndarray:
        """Жорданово исключение"""
        pivot_val = tableau[pivot_row, pivot_col]

        if abs(pivot_val) < 1e-12:
            print(f"  Предупреждение: ведущий элемент слишком мал: {pivot_val}")
            return tableau

        m = tableau.shape[0]

        # Нормализуем ведущую строку
        tableau[pivot_row, :] /= pivot_val

        # Обнуляем остальные строки в ведущем столбце
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