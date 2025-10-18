"""
Базовый класс для всех загрузчиков видео

Определяет общий интерфейс для загрузчиков различных платформ.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple


class BaseUploader(ABC):
    """
    Абстрактный базовый класс для загрузчиков видео на различные платформы.
    
    Все конкретные реализации загрузчиков должны наследоваться от этого класса
    и реализовывать все абстрактные методы.
    """
    
    @abstractmethod
    def upload(self, video_path: str, description: str, tags: str, credentials: Dict[str, Any]) -> Any:
        """
        Основной метод для загрузки видео на платформу.
        
        Args:
            video_path (str): Путь к видеофайлу для загрузки
            description (str): Описание видео
            tags (str): Теги для видео (строка, разделенная пробелами или запятыми)
            credentials (Dict[str, Any]): Учетные данные для доступа к платформе
            
        Returns:
            Any: Результат загрузки, специфичный для каждой платформы
            
        Raises:
            RuntimeError: Если необходимые библиотеки не установлены
            FileNotFoundError: Если видеофайл не найден
            Exception: Другие ошибки, специфичные для платформы
        """
        pass
    
    @abstractmethod
    def validate_credentials(self, credentials: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Проверка валидности учетных данных.
        
        Args:
            credentials (Dict[str, Any]): Учетные данные для проверки
            
        Returns:
            Tuple[bool, str]: (is_valid, message) 
                - is_valid: True если учетные данные валидны
                - message: Сообщение об ошибке или "OK" при успехе
        """
        pass
    
    def prepare_description(self, description: str, tags: str, max_length: int = None) -> str:
        """
        Подготовка описания с тегами.
        
        Args:
            description (str): Основное описание
            tags (str): Теги (строка, разделенная пробелами или запятыми)
            max_length (int, optional): Максимальная длина результата
            
        Returns:
            str: Подготовленное описание с тегами
        """
        # Очистка и форматирование тегов
        if tags:
            # Разделяем теги по пробелам или запятым
            tag_list = []
            for tag in tags.replace(',', ' ').split():
                clean_tag = tag.strip()
                if clean_tag and not clean_tag.startswith('#'):
                    clean_tag = '#' + clean_tag
                if clean_tag:
                    tag_list.append(clean_tag)
            
            tags_str = ' '.join(tag_list)
            full_description = f"{description}\n\n{tags_str}" if description else tags_str
        else:
            full_description = description
        
        # Обрезка до максимальной длины если указана
        if max_length and len(full_description) > max_length:
            full_description = full_description[:max_length-3] + "..."
        
        return full_description.strip()
    
    def check_video_file(self, video_path: str) -> None:
        """
        Проверка существования видеофайла.
        
        Args:
            video_path (str): Путь к видеофайлу
            
        Raises:
            FileNotFoundError: Если файл не существует
        """
        if not video_path:
            raise FileNotFoundError("Путь к видеофайлу не указан")
        
        if not isinstance(video_path, str):
            raise TypeError("Путь к видеофайлу должен быть строкой")
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Видеофайл не найден: {video_path}")
    
    def get_required_libraries(self) -> Dict[str, str]:
        """
        Возвращает список необходимых библиотек для работы загрузчика.
        
        Returns:
            Dict[str, str]: Словарь {имя_библиотеки: pip_команда_для_установки}
        """
        return {}
    
    def check_libraries(self) -> bool:
        """
        Проверка наличия необходимых библиотек.
        
        Returns:
            bool: True если все библиотеки доступны
        """
        required_libs = self.get_required_libraries()
        for lib_name, pip_command in required_libs.items():
            try:
                __import__(lib_name)
            except ImportError:
                return False
        return True


# Импорт для использования в check_video_file
import os