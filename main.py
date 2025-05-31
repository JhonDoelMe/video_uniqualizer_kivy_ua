# main.py (для PySide6)
import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt 
from ui.main_window import MainWindow 

# --- Додавання шляхів ---
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# --- Кінець додавання шляхів ---

def run_app():
    print(f"Запуск відеоредактора на PySide6...")
    
    app = QApplication(sys.argv) 
    
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    # --- Завантаження стилів з файлу style.qss ---
    try:
        style_file_path = project_root / "style.qss" 
        with open(style_file_path, "r", encoding="utf-8") as f: 
            app.setStyleSheet(f.read())
            print("Файл стилів style.qss успішно завантажено.")
    except FileNotFoundError:
        print("ПОПЕРЕДЖЕННЯ: Файл стилів style.qss не знайдено. Будуть використані стандартні стилі.")
    except Exception as e:
        print(f"ПОМИЛКА при завантаженні стилів: {e}")
    # --- Кінець завантаження стилів ---

    window = MainWindow() 
    # window.show() # Старий спосіб показу вікна
    window.showMaximized() # ! НОВИЙ СПОСІБ: Вікно відкриється на весь екран
    
    sys.exit(app.exec()) 

if __name__ == "__main__":
    run_app()