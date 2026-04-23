# controllers/file_manager.py
"""
Модуль для работы с файлами проектов
"""

import json
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QMessageBox
from datetime import datetime


class FileManager:
    """
    Класс для сохранения и загрузки проектов
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.current_file = None

    def save_project(self, data: Dict[str, Any], filename: str) -> bool:
        """
        Сохранение проекта в файл JSON

        Args:
            data: данные проекта (входные данные и результаты)
            filename: путь к файлу

        Returns:
            True если успешно
        """
        try:
            # Добавление метаданных
            data['metadata'] = {
                'saved_at': datetime.now().isoformat(),
                'version': '1.0.0',
                'app': 'Оптимизатор кормового рациона'
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            self.current_file = filename
            return True

        except Exception as e:
            QMessageBox.critical(
                self.parent, "Ошибка",
                f"Не удалось сохранить проект:\n{str(e)}"
            )
            return False

    def load_project(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Загрузка проекта из файла JSON

        Args:
            filename: путь к файлу

        Returns:
            словарь с данными или None при ошибке
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.current_file = filename

            # Проверка целостности данных
            if 'input' not in data:
                raise ValueError("Файл не содержит входных данных")

            return data

        except json.JSONDecodeError:
            QMessageBox.critical(
                self.parent, "Ошибка",
                "Файл поврежден или имеет неверный формат JSON"
            )
            return None
        except Exception as e:
            QMessageBox.critical(
                self.parent, "Ошибка",
                f"Не удалось загрузить проект:\n{str(e)}"
            )
            return None

    def export_to_json(self, data: Dict[str, Any], filename: str) -> bool:
        """
        Экспорт данных в JSON без метаданных

        Args:
            data: данные для экспорта
            filename: путь к файлу

        Returns:
            True если успешно
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            QMessageBox.critical(
                self.parent, "Ошибка",
                f"Не удалось экспортировать данные:\n{str(e)}"
            )
            return False