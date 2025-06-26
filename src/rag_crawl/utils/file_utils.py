"""
Утилиты для работы с файлами.
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_file(file_path: str) -> Optional[str]:
    """
    Извлекает текст из файла.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        Текстовое содержимое файла или None в случае ошибки
    """
    try:
        file_ext = Path(file_path).suffix.lower()
        
        # Обработка .txt файлов
        if file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        
        # В будущем здесь можно добавить поддержку других форматов:
        # PDF, DOCX, HTML и т.д.
        
        logger.warning(f"Неподдерживаемый формат файла: {file_ext}")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при извлечении текста из файла {file_path}: {e}")
        return None


def sanitize_filename(filename: str) -> str:
    """
    Очищает имя файла от недопустимых символов.
    
    Args:
        filename: Исходное имя файла
        
    Returns:
        Очищенное имя файла
    """
    # Удаляем недопустимые символы для имени файла
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Ограничиваем длину имени файла
    if len(filename) > 255:
        base, ext = os.path.splitext(filename)
        filename = base[:255-len(ext)] + ext
        
    return filename


def get_file_size(file_path: str) -> int:
    """
    Возвращает размер файла в байтах.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        Размер файла в байтах
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Ошибка при получении размера файла {file_path}: {e}")
        return 0 