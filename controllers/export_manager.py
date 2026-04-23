# controllers/export_manager.py
"""
Модуль для экспорта отчетов в различные форматы
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any
from PyQt6.QtWidgets import QMessageBox
import os

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class ExportManager:
    """
    Класс для экспорта отчетов
    """

    def __init__(self, parent=None):
        self.parent = parent
        self._register_fonts()

    def _register_fonts(self):
        """Регистрация шрифтов с поддержкой кириллицы"""
        if not REPORTLAB_AVAILABLE:
            return

        try:
            import platform
            system = platform.system()

            if system == "Windows":
                font_paths = [
                    "C:\\Windows\\Fonts\\arial.ttf",
                    "C:\\Windows\\Fonts\\DejaVuSans.ttf"
                ]
            elif system == "Linux":
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
                ]
            else:
                font_paths = [
                    "/Library/Fonts/Arial.ttf",
                    "/System/Library/Fonts/Helvetica.ttf"
                ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('CyrillicFont', font_path))
                    bold_path = font_path.replace('.ttf', 'bd.ttf').replace('.ttf', 'Bd.ttf')
                    if os.path.exists(bold_path):
                        pdfmetrics.registerFont(TTFont('CyrillicFont-Bold', bold_path))
                    else:
                        pdfmetrics.registerFont(TTFont('CyrillicFont-Bold', font_path))
                    break
            else:
                pdfmetrics.registerFont(TTFont('CyrillicFont', 'Helvetica'))
                pdfmetrics.registerFont(TTFont('CyrillicFont-Bold', 'Helvetica-Bold'))

        except Exception as e:
            print(f"Ошибка регистрации шрифтов: {e}")

    def export_to_excel(self, solution: Dict, nutrients_df: pd.DataFrame,
                        allocation_df: pd.DataFrame, filename: str) -> bool:
        """
        Экспорт результатов в Excel

        Args:
            solution: результаты оптимизации
            nutrients_df: таблица питательных веществ
            allocation_df: таблица распределения кормов
            filename: имя файла

        Returns:
            True если успешно
        """
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Лист со сводкой
                x = solution.get('x', [])
                feeds = solution.get('feeds', [])

                summary_data = {
                    'Показатель': [
                        'Минимальные затраты (тыс. руб)',
                        'Количество корма B1 (т)',
                        'Количество корма B2 (т)',
                        'Количество корма B3 (т)',
                        'Общее количество кормов (т)',
                        'Статус решения'
                    ],
                    'Значение': [
                        round(solution['fun'], 2) if solution['fun'] else 0,
                        round(x[0], 4) if len(x) > 0 else 0,
                        round(x[1], 4) if len(x) > 1 else 0,
                        round(x[2], 4) if len(x) > 2 else 0,
                        round(sum(x), 4),
                        'Успешно' if solution.get('success') else 'Ошибка'
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Сводка', index=False)

                # Лист с распределением кормов
                if allocation_df is not None and not allocation_df.empty:
                    allocation_df.to_excel(writer, sheet_name='Распределение кормов', index=False)

                # Лист с анализом питательных веществ
                if nutrients_df is not None and not nutrients_df.empty:
                    nutrients_df.to_excel(writer, sheet_name='Питательные вещества', index=False)

            return True

        except Exception as e:
            QMessageBox.critical(
                self.parent, "Ошибка",
                f"Не удалось экспортировать в Excel:\n{str(e)}"
            )
            return False

    def export_to_pdf(self, solution: Dict, nutrients_df: pd.DataFrame,
                      allocation_df: pd.DataFrame, filename: str) -> bool:
        """
        Экспорт результатов в PDF

        Args:
            solution: результаты оптимизации
            nutrients_df: таблица питательных веществ
            allocation_df: таблица распределения кормов
            filename: имя файла

        Returns:
            True если успешно
        """
        if not REPORTLAB_AVAILABLE:
            QMessageBox.warning(
                self.parent, "Предупреждение",
                "Библиотека reportlab не установлена.\n"
                "Установите: pip install reportlab"
            )
            return False

        try:
            doc = SimpleDocTemplate(
                filename, pagesize=A4,
                rightMargin=2 * cm, leftMargin=2 * cm,
                topMargin=2 * cm, bottomMargin=2 * cm
            )

            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'RussianTitle',
                parent=styles['Heading1'],
                fontName='CyrillicFont-Bold',
                fontSize=16,
                spaceAfter=30,
                alignment=1
            )

            heading_style = ParagraphStyle(
                'RussianHeading',
                parent=styles['Heading2'],
                fontName='CyrillicFont-Bold',
                fontSize=14,
                spaceBefore=15,
                spaceAfter=10
            )

            normal_style = ParagraphStyle(
                'RussianNormal',
                parent=styles['Normal'],
                fontName='CyrillicFont',
                fontSize=10,
                spaceBefore=6,
                spaceAfter=6
            )

            elements = []

            # Заголовок
            elements.append(Paragraph(
                "Отчет об оптимизации кормового рациона",
                title_style
            ))
            elements.append(Paragraph(
                f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                normal_style
            ))
            elements.append(Spacer(1, 0.5 * cm))

            # Основные показатели
            elements.append(Paragraph("Основные показатели", heading_style))

            x = solution.get('x', [])
            feeds = solution.get('feeds', [])
            cost = solution.get('fun', 0)

            summary_data = [
                ['Показатель', 'Значение'],
                ['Минимальные затраты', f"{cost:.2f} тыс. руб"],
                ['Количество корма B1', f"{x[0]:.4f} т" if len(x) > 0 else "0"],
                ['Количество корма B2', f"{x[1]:.4f} т" if len(x) > 1 else "0"],
                ['Количество корма B3', f"{x[2]:.4f} т" if len(x) > 2 else "0"],
                ['Общее количество', f"{sum(x):.4f} т"]
            ]

            table = Table(summary_data, colWidths=[8 * cm, 6 * cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'CyrillicFont-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'CyrillicFont'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.5 * cm))

            # Распределение кормов
            if allocation_df is not None and not allocation_df.empty:
                elements.append(Paragraph("Распределение кормов", heading_style))

                headers = list(allocation_df.columns)
                alloc_data = [headers]
                for _, row in allocation_df.iterrows():
                    alloc_data.append([str(row[col]) for col in headers])

                alloc_table = Table(alloc_data, colWidths=[4 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm], repeatRows=1)
                alloc_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'CyrillicFont-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'CyrillicFont'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(alloc_table)
                elements.append(Spacer(1, 0.3 * cm))

            # Ответы на вопросы
            elements.append(Paragraph("Ответы на вопросы задания", heading_style))
            elements.append(Paragraph(
                f"1. Количество корма B2: {x[1]:.4f} тонн (при x[1] > 0.0001)",
                normal_style
            ))
            elements.append(Paragraph(
                f"2. Общее количество кормов: {sum(x):.4f} тонн",
                normal_style
            ))
            elements.append(Paragraph(
                f"3. Минимальные затраты: {cost:.2f} тыс. руб",
                normal_style
            ))

            doc.build(elements)
            return True

        except Exception as e:
            QMessageBox.critical(
                self.parent, "Ошибка",
                f"Не удалось экспортировать в PDF:\n{str(e)}"
            )
            return False