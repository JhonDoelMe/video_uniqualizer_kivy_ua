# Головний скрипт, точка входу Kivy додатку
import sys
print("Python, який виконується:", sys.executable)
# Перевірка версії Python
print("Версія Python:", sys.version)
import os
# Встановлення змінних середовища для Kivy до імпорту інших модулів Kivy (якщо потрібно)
# Наприклад, для логування або графічного драйвера
# os.environ['KIVY_LOG_LEVEL'] = 'debug'

from kivy.app import App
from ui.main_app import VideoEditorApp # Припускаємо, що клас App буде там

def run_app():
    print(f"Запуск video_editor_kivy_ua Kivy App...")
    # Тут можна додати логіку для пошуку FFmpeg, якщо це потрібно робити централізовано
    # import app_logic.utils as utils
    # utils.prepare_ffmpeg_path() # Приклад
    app = VideoEditorApp()
    app.run()

if __name__ == "__main__":
    run_app()
