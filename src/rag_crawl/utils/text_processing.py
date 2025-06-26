"""
Модуль для извлечения текста из файлов различных форматов.
"""

import io
import re
from typing import Union
from pathlib import Path
from fastapi import UploadFile
import docx
import markdown
from bs4 import BeautifulSoup


async def extract_text_from_file(file: UploadFile) -> str:
    """
    Извлекает текст из загруженного файла в зависимости от его типа.
    
    Args:
        file: Загруженный файл через FastAPI
        
    Returns:
        str: Извлеченный текст
        
    Raises:
        ValueError: Если формат файла не поддерживается
    """
    content = await file.read()
    filename = file.filename or ""
    content_type = file.content_type or ""
    
    # Сброс указателя файла для повторного чтения если нужно
    await file.seek(0)
    
    file_extension = Path(filename).suffix.lower()
    
    # PDF файлы - отключаем обработку
    if file_extension == ".pdf" or "pdf" in content_type:
        raise ValueError("Обработка PDF файлов временно отключена")
    
    # Word документы
    elif file_extension in [".docx", ".doc"] or "document" in content_type:
        return extract_text_from_docx(content)
    
    # Markdown файлы
    elif file_extension in [".md", ".markdown"]:
        return extract_text_from_markdown(content)
    
    # HTML файлы
    elif file_extension in [".html", ".htm"] or "html" in content_type:
        return extract_text_from_html(content)
    
    # Текстовые файлы (по умолчанию)
    elif file_extension in [".txt", ".text"] or "text" in content_type or not file_extension:
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            # Попытка с другой кодировкой
            try:
                return content.decode("cp1251")
            except UnicodeDecodeError:
                return content.decode("latin-1")
    
    else:
        raise ValueError(f"Неподдерживаемый тип файла: {file_extension} ({content_type})")


def extract_text_from_docx(content: bytes) -> str:
    """Извлекает текст из Word документа (.docx)."""
    try:
        doc = docx.Document(io.BytesIO(content))
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    except Exception as e:
        raise ValueError(f"Ошибка обработки DOCX: {e}")


def extract_text_from_markdown(content: bytes) -> str:
    """Извлекает текст из Markdown файла."""
    try:
        md_text = content.decode("utf-8")
        
        # Конвертируем Markdown в HTML, затем извлекаем текст
        html = markdown.markdown(md_text)
        soup = BeautifulSoup(html, "html.parser")
        
        return soup.get_text(separator="\n").strip()
    except Exception as e:
        raise ValueError(f"Ошибка обработки Markdown: {e}")


def extract_text_from_html(content: bytes) -> str:
    """Извлекает текст из HTML файла."""
    try:
        html_text = content.decode("utf-8")
        soup = BeautifulSoup(html_text, "html.parser")
        
        # Удаляем скрипты и стили
        for script in soup(["script", "style"]):
            script.decompose()
        
        return soup.get_text(separator="\n").strip()
    except Exception as e:
        raise ValueError(f"Ошибка обработки HTML: {e}")


def clean_text(text: str) -> str:
    """
    Очищает и нормализует извлеченный текст.
    
    Args:
        text: Исходный текст
        
    Returns:
        str: Очищенный текст
    """
    # Удаление лишних пробелов и переносов строк
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    # Объединение строк с учетом пунктуации
    cleaned_lines = []
    for line in lines:
        if cleaned_lines and not line[0].isupper() and not cleaned_lines[-1].endswith((".", "!", "?")):
            # Продолжение предыдущей строки
            cleaned_lines[-1] += " " + line
        else:
            cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines)


def sanitize_filename(filename: str) -> str:
    """
    Очищает имя файла от недопустимых символов.
    
    Args:
        filename: Исходное имя файла
        
    Returns:
        str: Очищенное имя файла
    """
    # Удаляем путь, оставляем только имя файла
    filename = Path(filename).name
    # Заменяем недопустимые символы
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Ограничиваем длину
    if len(filename) > 255:
        name, ext = Path(filename).stem, Path(filename).suffix
        filename = name[:255-len(ext)] + ext
    return filename 