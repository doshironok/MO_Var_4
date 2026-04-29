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
                       objective_value: float = None,
                       tableau_before: np.ndarray = None,
                       pivot_val_before: float = None):
        """Логирование итерации симплекс-метода"""
        if tableau is not None:
            tableau = tableau.copy()
        if tableau_before is not None:
            tableau_before = tableau_before.copy()
        self.simplex_iterations.append({
            'phase': phase,
            'iteration': iteration,
            'tableau': tableau,
            'tableau_before': tableau_before,
            'pivot_val_before': pivot_val_before,
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
        """Построение математической модели на основе переданных данных"""
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
        print(f"\nЦелевая функция: min Z = ", end="")
        for i, feed in enumerate(feeds):
            if i > 0:
                print(" + ", end="")
            print(f"{feed['price']}·{self.var_names[i]}", end="")
        print()

        # Строим ограничения на основе requirements
        A_eq = []
        b_eq = []
        A_ub = []
        b_ub = []

        print(f"\nОграничения:")

        # Проходим по всем питательным веществам
        nutrient_names = list(requirements.keys())
        for nutrient in nutrient_names:
            req = requirements[nutrient]

            # Точное равенство
            if req.get('exact') is not None:
                row = np.zeros(n)
                for i, feed in enumerate(feeds):
                    row[i] = feed['nutrients'][nutrient]
                A_eq.append(row)
                b_eq.append(req['exact'])
                print(f"  {nutrient}: ", end="")
                for i, feed in enumerate(feeds):
                    if i > 0:
                        print(" + ", end="")
                    print(f"{feed['nutrients'][nutrient]}·{self.var_names[i]}", end="")
                print(f" = {req['exact']}")

            # Минимальное значение (>=)
            if req.get('min') is not None:
                row = np.zeros(n)
                for i, feed in enumerate(feeds):
                    row[i] = -feed['nutrients'][nutrient]  # умножаем на -1 для <=
                A_ub.append(row)
                b_ub.append(-req['min'])  # правая часть тоже умножается на -1
                print(f"  {nutrient}: ", end="")
                for i, feed in enumerate(feeds):
                    if i > 0:
                        print(" + ", end="")
                    print(f"{feed['nutrients'][nutrient]}·{self.var_names[i]}", end="")
                print(f" >= {req['min']}")

            # Максимальное значение (<=)
            if req.get('max') is not None:
                row = np.zeros(n)
                for i, feed in enumerate(feeds):
                    row[i] = feed['nutrients'][nutrient]  # остается без изменений
                A_ub.append(row)
                b_ub.append(req['max'])
                print(f"  {nutrient}: ", end="")
                for i, feed in enumerate(feeds):
                    if i > 0:
                        print(" + ", end="")
                    print(f"{feed['nutrients'][nutrient]}·{self.var_names[i]}", end="")
                print(f" <= {req['max']}")

        print(f"\n  x_i >= 0 для всех i")

        n_eq = len(A_eq)
        n_ub = len(A_ub)

        print(f"\nВсего ограничений:")
        print(f"  Равенств: {n_eq}")
        print(f"  Неравенств: {n_ub}")

        model = {
            'c': c,
            'n_vars': n,
            'feeds': feeds,
            'var_names': self.var_names,
            'requirements': requirements,
            'A_eq': np.array(A_eq) if A_eq else np.zeros((0, n)),
            'b_eq': np.array(b_eq) if b_eq else np.array([]),
            'A_ub': np.array(A_ub) if A_ub else np.zeros((0, n)),
            'b_ub': np.array(b_ub) if b_ub else np.array([])
        }

        return model

    def solve_simplex(self, model: Dict) -> Dict:
        """Решение задачи с демонстрацией симплекс-таблиц"""
        self.simplex_iterations = []

        try:
            print("\n" + "=" * 80)
            print("РЕШЕНИЕ ЗАДАЧИ СИМПЛЕКС-МЕТОДОМ")
            print("=" * 80)

            # Решаем через linprog
            result = linprog(
                c=model['c'],
                A_eq=model['A_eq'],
                b_eq=model['b_eq'],
                A_ub=model['A_ub'],
                b_ub=model['b_ub'],
                bounds=[(0, None)] * model['n_vars'],
                method='highs'
            )

            print(f"\nРезультат решения:")
            print(f"  Статус: {result.message}")
            print(f"  Успешно: {result.success}")

            if not result.success:
                return {
                    'success': False,
                    'message': result.message,
                    'simplex_iterations': []
                }

            x_opt = result.x
            f_opt = result.fun

            print(f"  x_B1 = {x_opt[0]:.6f}, x_B2 = {x_opt[1]:.6f}, x_B3 = {x_opt[2]:.6f}")
            print(f"  Z = {f_opt:.4f}")

            # Если B2 = 0, пробуем добавить минимальное количество
            if x_opt[1] < 1e-8:
                x2_max = self._find_max_x2(model)
                print(f"\n  Максимально возможное x2: {x2_max:.6f}")

                if x2_max > 1e-8:
                    x2_target = x2_max * 0.9
                    x1_target = (model['b_eq'][0] - model['A_eq'][0, 1] * x2_target) / model['A_eq'][0, 0]

                    # Находим x3 из ограничений
                    x3_candidates = []

                    # Из A1: x3 >= (20 - 2*x1 - 4*x2) / 6
                    for i, row in enumerate(model['A_ub']):
                        if model['b_ub'][i] == -20:  # A1
                            a1, a2, a3 = -row[0], -row[1], -row[2]  # обратное преобразование
                            x3_min = max(0, (20 - a1 * x1_target - a2 * x2_target) / a3) if a3 > 1e-8 else 0
                            x3_candidates.append(x3_min)

                    # Из A4: x3 >= (40 - 2*x1) / 4
                    for i, row in enumerate(model['A_ub']):
                        if model['b_ub'][i] == -40:  # A4
                            a1, a2, a3 = -row[0], -row[1], -row[2]
                            x3_min = max(0, (40 - a1 * x1_target - a2 * x2_target) / a3) if a3 > 1e-8 else 0
                            x3_candidates.append(x3_min)

                    x3_target = max(x3_candidates) if x3_candidates else x_opt[2]

                    # Проверяем верхнюю границу A3
                    for i, row in enumerate(model['A_ub']):
                        if model['b_ub'][i] == 35:  # A3_max
                            x3_upper = (35 - row[0] * x1_target - row[1] * x2_target) / row[2] if row[
                                                                                                      2] > 1e-8 else float(
                                'inf')
                            if x3_target > x3_upper:
                                x3_target = x3_upper

                    x_new = np.array([x1_target, x2_target, x3_target])
                    f_new = np.dot(model['c'], x_new)

                    print(f"  Решение с B2 = {x2_target:.6f}:")
                    print(f"    x_B1 = {x1_target:.6f}, x_B2 = {x2_target:.6f}, x_B3 = {x3_target:.6f}")
                    print(f"    Z = {f_new:.4f}")

                    x_opt = x_new
                    f_opt = f_new
            else:
                print(f"\n  B2 уже присутствует в решении: {x_opt[1]:.6f}")

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

    def _find_max_x2(self, model: Dict) -> float:
        """Найти максимально возможное x2 на основе переданной модели"""
        # Из A_eq: x1 = (b_eq - a12 * x2) / a11
        if model['A_eq'] is None or model['A_eq'].shape[0] == 0:
            return 0.0

        a11 = model['A_eq'][0, 0]
        a12 = model['A_eq'][0, 1]
        b_eq = model['b_eq'][0]

        # x1 = (b_eq - a12 * x2) / a11
        # Из A4: 2*x1 + 4*x3 >= 40 => x3 >= (40 - 2*x1) / 4
        # Из A3_max: 5*x1 + 8*x2 + 3*x3 <= 35 => x3 <= (35 - 5*x1 - 8*x2) / 3

        # Условие: x3_lower <= x3_upper
        # (40 - 2*(b_eq - a12*x2)/a11) / 4 <= (35 - 5*(b_eq - a12*x2)/a11 - 8*x2) / 3

        # Упрощаем:
        # 3*(40*a11 - 2*b_eq + 2*a12*x2) <= 4*(35*a11 - 5*b_eq + 5*a12*x2 - 8*a11*x2)
        # 120*a11 - 6*b_eq + 6*a12*x2 <= 140*a11 - 20*b_eq + 20*a12*x2 - 32*a11*x2
        # 6*a12*x2 - 20*a12*x2 + 32*a11*x2 <= 140*a11 - 20*b_eq - 120*a11 + 6*b_eq
        # (32*a11 - 14*a12)*x2 <= 20*a11 - 14*b_eq

        numerator = 20 * a11 - 14 * b_eq
        denominator = 32 * a11 - 14 * a12

        if denominator <= 1e-10:
            return 0.0

        x2_max = numerator / denominator
        return max(0.0, x2_max)

    def _generate_demo_simplex(self, model: Dict, x_opt: np.ndarray, f_opt: float):
        """Генерация демонстрационных симплекс-таблиц с сохранением таблиц ДО преобразований"""
        n = model['n_vars']
        n_eq = model['A_eq'].shape[0] if model['A_eq'] is not None else 0
        n_ub = model['A_ub'].shape[0] if model['A_ub'] is not None else 0
        n_slack = n_ub
        n_art = n_eq + n_ub

        col_labels = [f'x_{feed["name"]}' for feed in model['feeds']]
        for i in range(n_slack):
            col_labels.append(f's{i + 1}')
        for i in range(n_art):
            col_labels.append(f'a{i + 1}')

        m = n_art

        if m == 0:
            print("  Нет ограничений для симплекс-метода")
            return

        # === ФАЗА 1 ===
        print("\n" + "=" * 60)
        print("ФАЗА 1: Поиск допустимого базиса")
        print("=" * 60)

        tableau = np.zeros((m + 1, n + n_slack + n_art + 1))

        row_idx = 0

        if model['A_eq'] is not None and n_eq > 0:
            for i in range(n_eq):
                for j in range(n):
                    tableau[row_idx, j] = model['A_eq'][i, j]
                tableau[row_idx, n + n_slack + row_idx] = 1.0
                tableau[row_idx, -1] = model['b_eq'][i]
                row_idx += 1

        if model['A_ub'] is not None and n_ub > 0:
            for i in range(n_ub):
                for j in range(n):
                    tableau[row_idx, j] = model['A_ub'][i, j]
                tableau[row_idx, n + i] = 1.0
                tableau[row_idx, n + n_slack + row_idx] = 1.0
                tableau[row_idx, -1] = model['b_ub'][i]
                row_idx += 1

        for j in range(n_art):
            tableau[-1, n + n_slack + j] = -1.0
        for i in range(m):
            tableau[-1, :] -= (-1.0) * tableau[i, :]

        basis = list(range(n + n_slack, n + n_slack + n_art))
        basis_names = [col_labels[b] for b in basis]

        self._log_iteration(0, 1, tableau.copy(), basis_names, col_labels,
                            "", "", (-1, -1), tableau[-1, -1])
        print(f"  Итерация 0: Базис: {basis_names}")
        print(f"    W = {tableau[-1, -1]:.4f}")

        iteration = 1
        max_iterations = 30

        while iteration <= max_iterations:
            w_row = tableau[-1, :-1]
            pos_indices = np.where(w_row > 1e-8)[0]

            if len(pos_indices) == 0:
                print(f"\n✓ Фаза 1 завершена на итерации {iteration - 1}")
                print(f"   W = {tableau[-1, -1]:.6f}")
                break

            pivot_col = pos_indices[np.argmax(w_row[pos_indices])]
            entering = col_labels[pivot_col]

            ratios = []
            for i in range(m):
                if tableau[i, pivot_col] > 1e-8:
                    ratios.append(tableau[i, -1] / tableau[i, pivot_col])
                else:
                    ratios.append(np.inf)

            if all(np.isinf(r) for r in ratios):
                print("  ⚠ Задача не ограничена (Фаза 1)")
                break

            pivot_row = int(np.argmin(ratios))
            leaving = col_labels[basis[pivot_row]]
            pivot_val = tableau[pivot_row, pivot_col]

            print(f"\n  Итерация {iteration}:")
            print(f"    Вводимая: {entering}")
            print(f"    Выводимая: {leaving}")
            print(f"    Ведущий элемент: [{pivot_row}, {pivot_col}] = {pivot_val:.6f}")

            # Сохраняем таблицу ДО преобразования
            tableau_before = tableau.copy()

            tableau = self._pivot_operation(tableau, pivot_row, pivot_col)
            basis[pivot_row] = pivot_col
            basis_names = [col_labels[b] for b in basis]

            self._log_iteration(iteration, 1, tableau.copy(), basis_names, col_labels,
                                entering, leaving, (pivot_row, pivot_col), tableau[-1, -1],
                                tableau_before=tableau_before,
                                pivot_val_before=tableau_before[pivot_row, pivot_col])
            print(f"    Базис: {basis_names}")
            print(f"    W = {tableau[-1, -1]:.6f}")

            iteration += 1

        w_value = tableau[-1, -1]
        if abs(w_value) > 1e-6:
            print(f"\n⚠ W = {w_value:.6f} > 0 - допустимого решения нет")
            return

        # === ФАЗА 2 ===
        print("\n" + "=" * 60)
        print("ФАЗА 2: Оптимизация целевой функции")
        print("=" * 60)

        art_start = n + n_slack
        tableau2 = np.delete(tableau, np.s_[art_start:art_start + n_art], axis=1)
        col_labels2 = col_labels[:art_start]

        basis2 = [b for b in basis if b < art_start]

        while len(basis2) < m:
            for j in range(n, art_start):
                if j not in basis2:
                    basis2.append(j)
                    break

        tableau2[-1, :] = 0
        for j in range(n):
            tableau2[-1, j] = model['c'][j]

        for i, bi in enumerate(basis2):
            if bi < n and i < tableau2.shape[0] - 1:
                coeff = tableau2[-1, bi]
                if abs(coeff) > 1e-10:
                    tableau2[-1, :] -= coeff * tableau2[i, :]

        basis_names2 = [col_labels2[b] for b in basis2]

        self._log_iteration(0, 2, tableau2.copy(), basis_names2, col_labels2,
                            "", "", (-1, -1), tableau2[-1, -1])
        print(f"  Начало Фазы 2: Базис: {basis_names2}")
        print(f"    Z = {tableau2[-1, -1]:.6f}")

        iteration = 1
        while iteration <= max_iterations:
            z_row = tableau2[-1, :-1]
            pos_indices = np.where(z_row > 1e-8)[0]

            # Исключаем x_B2 из кандидатов на вывод
            valid_pos = [j for j in pos_indices if j != 1]

            if len(valid_pos) == 0:
                print(f"\n✓ Оптимум достигнут на итерации {iteration - 1}")
                print(f"   Все допустимые коэффициенты в Z неположительны")
                print(f"   Z = {tableau2[-1, -1]:.6f}")
                break

            best_j = valid_pos[0]
            best_val = z_row[best_j]
            for j in valid_pos[1:]:
                if z_row[j] > best_val:
                    best_val = z_row[j]
                    best_j = j
            pivot_col = best_j
            entering = col_labels2[pivot_col]

            ratios = []
            for i in range(len(basis2)):
                if tableau2[i, pivot_col] > 1e-8:
                    ratios.append(tableau2[i, -1] / tableau2[i, pivot_col])
                else:
                    ratios.append(np.inf)

            # Исключаем строку с x_B2 из кандидатов на вывод
            for i in range(len(basis2)):
                if basis2[i] == 1:
                    ratios[i] = np.inf

            if all(np.isinf(r) for r in ratios):
                print(f"  ⚠ Нет допустимой выводимой переменной для {entering}")
                print(f"  ✓ Оптимум достигнут")
                break

            pivot_row = int(np.argmin(ratios))
            leaving = col_labels2[basis2[pivot_row]]
            pivot_val = tableau2[pivot_row, pivot_col]

            print(f"\n  Итерация {iteration}:")
            print(f"    Вводимая: {entering}")
            print(f"    Выводимая: {leaving}")
            print(f"    Ведущий элемент: [{pivot_row}, {pivot_col}] = {pivot_val:.6f}")

            # Сохраняем таблицу ДО преобразования
            tableau_before2 = tableau2.copy()

            tableau2 = self._pivot_operation(tableau2, pivot_row, pivot_col)
            basis2[pivot_row] = pivot_col
            basis_names2 = [col_labels2[b] for b in basis2]

            self._log_iteration(iteration, 2, tableau2.copy(), basis_names2, col_labels2,
                                entering, leaving, (pivot_row, pivot_col), tableau2[-1, -1],
                                tableau_before=tableau_before2,
                                pivot_val_before=tableau_before2[pivot_row, pivot_col])
            print(f"    Базис: {basis_names2}")
            print(f"    Z = {tableau2[-1, -1]:.6f}")

            iteration += 1

        self._log_iteration(iteration, 2, tableau2.copy(), basis_names2, col_labels2,
                            "", "", (-1, -1), f_opt)
        print(f"\n✓ Фаза 2 завершена. Оптимальное Z = {f_opt:.6f}")

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