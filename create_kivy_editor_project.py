import os
import shutil
import subprocess
from pathlib import Path

# --- Конфігурація структури проєкту ---
project_name = "video_editor_kivy_ua" # Назва проєкту

# Директорії, які потрібно створити
directories_to_create = [
    "",  # Корінь самого проєкту
    "app_logic", # Для основної логіки обробки відео
    "ui", # Для файлів Kivy UI (Python та .kv)
    "ui/widgets", # Для можливих кастомних віджетів Kivy
    "ffmpeg_binaries", # Для бінарників FFmpeg (актуально для Windows desktop збірки)
    "assets", # Іконки, шрифти та інші ресурси для Kivy
    "output", # Папка за замовчуванням для результатів
]

# Файли, які потрібно створити, з їхнім початковим вмістом українською
files_to_create_with_content = {
    "main.py": f"""# Головний скрипт, точка входу Kivy додатку
import os
# Встановлення змінних середовища для Kivy до імпорту інших модулів Kivy (якщо потрібно)
# Наприклад, для логування або графічного драйвера
# os.environ['KIVY_LOG_LEVEL'] = 'debug'

from kivy.app import App
from ui.main_app import VideoEditorApp # Припускаємо, що клас App буде там

def run_app():
    print(f"Запуск {project_name} Kivy App...")
    # Тут можна додати логіку для пошуку FFmpeg, якщо це потрібно робити централізовано
    # import app_logic.utils as utils
    # utils.prepare_ffmpeg_path() # Приклад
    app = VideoEditorApp()
    app.run()

if __name__ == "__main__":
    run_app()
""",
    "app_logic/__init__.py": """# Модуль app_logic
# Містить основну логіку програми, не пов'язану безпосередньо з GUI.
""",
    "app_logic/video_processor.py": """# Модуль з функціями обробки та редагування відео (MoviePy/OpenCV)
from moviepy.editor import VideoFileClip # , vfx (для ефектів)
import os
import threading
from kivy.clock import Clock # Для безпечного оновлення UI з іншого потоку

# Ця функція викликатиметься з UI, швидше за все, в окремому потоці
def process_video_task(input_path, output_folder, options, status_update_callback, progress_update_callback):
    try:
        if not input_path or not os.path.exists(input_path):
            Clock.schedule_once(lambda dt: status_update_callback("Помилка: Вхідний файл не знайдено."))
            return
        if not output_folder or not os.path.isdir(output_folder):
            Clock.schedule_once(lambda dt: status_update_callback("Помилка: Папку для збереження не знайдено."))
            return

        Clock.schedule_once(lambda dt: status_update_callback(f"Завантаження відео: {os.path.basename(input_path)}"))
        
        clip = VideoFileClip(input_path)
        processed_clip = clip # Початкова точка

        # --- Приклад застосування опцій ---
        # (Ця частина має бути значно розширена для редактора)
        if options.get("resize_active"): # Приклад опції "змінити розмір"
            try:
                width = int(options.get("width", "0"))
                height = int(options.get("height", "0"))
                if width > 0 and height > 0:
                    processed_clip = processed_clip.resize(newsize=(width, height))
                    Clock.schedule_once(lambda dt: status_update_callback(f"Роздільну здатність змінено на {width}x{height}"))
                else:
                    Clock.schedule_once(lambda dt: status_update_callback("Пропуск зміни розміру: некоректні розміри."))
            except ValueError:
                Clock.schedule_once(lambda dt: status_update_callback("Помилка: некоректні значення для зміни розміру."))
                return
        
        Clock.schedule_once(lambda dt: progress_update_callback(0.5)) # Приклад оновлення прогресу

        # ... Інші трансформації та операції редагування на основі 'options' ...
        # Наприклад: обрізка, додавання тексту, склейка, ефекти тощо.

        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        output_file_name = f"{name}_edited_kivy{ext}" # Додамо edited для розрізнення
        output_path = os.path.join(output_folder, output_file_name)

        Clock.schedule_once(lambda dt: status_update_callback(f"Збереження відео в: {output_path}"))
        
        processed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=4, logger=None)

        Clock.schedule_once(lambda dt: progress_update_callback(1.0))
        Clock.schedule_once(lambda dt: status_update_callback(f"Відео успішно збережено: {output_path}"))

    except Exception as e:
        Clock.schedule_once(lambda dt: status_update_callback(f"Помилка обробки відео: {str(e)}"))
        import traceback
        traceback.print_exc() # Для детальної помилки в консолі розробника
    finally:
        if 'clip' in locals() and clip:
            clip.close()
        if 'processed_clip' in locals() and processed_clip != clip:
            try:
                if hasattr(processed_clip, 'close') and callable(processed_clip.close):
                    processed_clip.close()
            except Exception:
                pass 
        Clock.schedule_once(lambda dt: status_update_callback("Обробку завершено (або сталася помилка)."))
""",
    "app_logic/utils.py": """# Допоміжні функції
import os
import sys
from pathlib import Path

def get_user_data_dir_ua(app_name):
    \""" Отримує шлях до папки даних користувача для програми. \"""
    if sys.platform == "win32":
        path = Path(os.environ["APPDATA"]) / app_name
    elif sys.platform == "darwin": # macOS
        path = Path.home() / "Library" / "Application Support" / app_name
    else: # Linux та інші
        path = Path.home() / ".local" / "share" / app_name
    path.mkdir(parents=True, exist_ok=True)
    return str(path)

def get_ffmpeg_path_for_moviepy_ua():
    \"""
    Намагається знайти FFmpeg для MoviePy, особливо якщо він упакований з програмою (для desktop).
    Повертає шлях до ffmpeg.exe або просто 'ffmpeg', якщо передбачається, що він у PATH.
    Це більше актуально для PyInstaller збірок. Buildozer для Android обробляє це інакше.
    \"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_dir = Path(sys._MEIPASS)
        potential_paths = [
            bundle_dir / 'ffmpeg.exe',
            bundle_dir / 'ffmpeg_binaries' / 'ffmpeg.exe',
        ]
        for path in potential_paths:
            if path.exists():
                print(f"FFmpeg знайдено в бандлі: {path}")
                return str(path.resolve())
    print("FFmpeg не знайдено в бандлі (або програма не заморожена), MoviePy шукатиме його в PATH.")
    return 'ffmpeg'

# def prepare_ffmpeg_path_ua():
#     ffmpeg_exe = get_ffmpeg_path_for_moviepy_ua()
#     if ffmpeg_exe != 'ffmpeg': 
#         os.environ["FFMPEG_BINARY"] = ffmpeg_exe
#         print(f"Встановлено FFMPEG_BINARY: {ffmpeg_exe}")
""",
    "ui/__init__.py": """# Модуль Kivy UI
""",
    "ui/main_app.py": """# Основний файл Kivy App та логіка GUI
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty, NumericProperty
from kivy.lang import Builder 
from kivy.utils import platform 
from kivy.clock import Clock

import threading
import os
from pathlib import Path # Додано для роботи зі шляхами
from app_logic import video_processor 

# Builder.load_file('ui/editor_layout.kv') # Якщо ім'я kv файлу відрізняється

class MainLayout(BoxLayout):
    status_label_text = StringProperty("Оберіть відео та опції для редагування...")
    progress_bar_value = NumericProperty(0)

    input_file_path = StringProperty("")
    output_folder_path = StringProperty("") 

    # Приклад опції для редагування
    opt_resize_active = BooleanProperty(False)
    opt_resize_width = StringProperty("1280")
    opt_resize_height = StringProperty("720")
    
    app = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if platform == 'android':
            try:
                from android.storage import Environment # type: ignore
                self.output_folder_path = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).getAbsolutePath()
                if not os.path.exists(self.output_folder_path): 
                    self.output_folder_path = App.get_running_app().user_data_dir
            except ImportError: 
                 self.output_folder_path = App.get_running_app().user_data_dir
        else: 
            self.output_folder_path = str(Path.home() / "Відео" / "ВідредагованіВідео") # Українською
        
        os.makedirs(self.output_folder_path, exist_ok=True)

    def select_video_file(self):
        self.app.open_filechooser(callback=self._on_file_selected)
        self.status_label_text = "Очікування вибору файлу..."

    def _on_file_selected(self, selection):
        if selection:
            self.input_file_path = selection[0] 
            self.status_label_text = f"Обрано файл: {os.path.basename(self.input_file_path)}"
        else:
            self.status_label_text = "Вибір файлу скасовано."

    def select_output_folder(self):
        self.app.open_folderchooser(callback=self._on_folder_selected)
        self.status_label_text = "Очікування вибору папки..."

    def _on_folder_selected(self, selection):
        if selection:
            self.output_folder_path = selection[0]
            self.status_label_text = f"Папка для збереження: {self.output_folder_path}"
        else:
            self.status_label_text = "Вибір папки скасовано."

    def run_processing(self):
        if not self.input_file_path:
            self._show_error_popup("Файл не обрано", "Будь ласка, оберіть вхідний відеофайл.")
            return
        if not self.output_folder_path:
            self._show_error_popup("Папку не обрано", "Будь ласка, оберіть папку для збереження.")
            return
        
        options = {
            "resize_active": self.opt_resize_active,
            "width": self.opt_resize_width,
            "height": self.opt_resize_height,
            # ... інші опції редагування з GUI ...
        }
        self.status_label_text = "Початок обробки..."
        self.progress_bar_value = 0 

        thread = threading.Thread(target=video_processor.process_video_task,
                                  args=(self.input_file_path,
                                        self.output_folder_path,
                                        options,
                                        self.update_status_from_thread, 
                                        self.update_progress_from_thread 
                                        ))
        thread.daemon = True 
        thread.start()

    def update_status_from_thread(self, message):
        self.status_label_text = message

    def update_progress_from_thread(self, progress_value): 
        self.progress_bar_value = progress_value
        
    def _show_error_popup(self, title, message):
        popup_content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_content.add_widget(Label(text=message, size_hint_y=None, height=80))
        btn_ok = Button(text="OK", size_hint_y=None, height=40)
        popup_content.add_widget(btn_ok)
        
        popup = Popup(title=title, content=popup_content, size_hint=(0.8, 0.4), auto_dismiss=False)
        btn_ok.bind(on_press=popup.dismiss)
        popup.open()

class VideoEditorApp(App): # Змінено ім'я класу App
    def build(self):
        if platform == 'android':
            self.request_android_permissions()
        
        self.main_layout = MainLayout(app=self)
        return self.main_layout

    def request_android_permissions(self):
        try:
            from android.permissions import request_permissions, Permission # type: ignore
            permissions_to_request = [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
            
            if permissions_to_request:
                request_permissions(permissions_to_request)
        except ImportError:
            print("Не вдалося імпортувати модуль android.permissions. Ймовірно, запуск не на Android.")
        except Exception as e:
            print(f"Помилка при запиті дозволів Android: {e}")

    def open_filechooser(self, callback):
        try:
            from plyer import filechooser # type: ignore
            filechooser.open_file(on_selection=callback, filters=['*.mp4', '*.avi', '*.mkv', '*.mov'])
        except ImportError:
            self._show_plyer_missing_popup("Plyer не встановлено або не налаштовано.")
        except Exception as e:
            self._show_plyer_missing_popup(f"Помилка Plyer: {e}")
            
    def open_folderchooser(self, callback):
        try:
            from plyer import filechooser # type: ignore
            filechooser.choose_dir(on_selection=callback)
        except ImportError:
            self._show_plyer_missing_popup("Plyer не встановлено або не налаштовано.")
        except Exception as e:
            self._show_plyer_missing_popup(f"Помилка Plyer: {e}")

    def _show_plyer_missing_popup(self, message):
        print(message) 
        popup_content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_content.add_widget(Label(text=f"{message}\\n\\nБудь ласка, введіть шлях вручну.", size_hint_y=None, height=100))
        btn_ok = Button(text="OK", size_hint_y=None, height=40)
        popup_content.add_widget(btn_ok)
        
        popup = Popup(title="Помилка вибору файлу/папки", content=popup_content, size_hint=(0.9, 0.5), auto_dismiss=False)
        btn_ok.bind(on_press=popup.dismiss)
        popup.open()
""",
    # Ім'я .kv файлу має відповідати імені класу App (VideoEditorApp -> videoeditor.kv)
    "ui/videoeditor.kv": """# Kivy KV Language файл для VideoEditorApp
<MainLayout>: 
    orientation: 'vertical'
    padding: dp(10)
    spacing: dp(10)

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        Label:
            text: "Відеофайл:"
            size_hint_x: 0.3
        TextInput:
            id: input_file_text
            text: root.input_file_path
            readonly: True 
            size_hint_x: 0.55
        Button:
            text: "Огляд..."
            size_hint_x: 0.15
            on_press: root.select_video_file()

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        Label:
            text: "Папка збер.:"
            size_hint_x: 0.3
        TextInput:
            id: output_folder_text
            text: root.output_folder_path
            size_hint_x: 0.55
        Button:
            text: "Огляд..."
            size_hint_x: 0.15
            on_press: root.select_output_folder()

    ScrollView: # Область для опцій редагування
        size_hint_y: 0.6
        GridLayout:
            cols: 2
            padding: dp(5)
            spacing: dp(5)
            size_hint_y: None
            height: self.minimum_height 

            Label:
                text: "Змінити розмір:"
                halign: 'left'
                valign: 'middle'
                text_size: self.width, None 
                size_hint_y: None
                height: dp(30)
            CheckBox:
                active: root.opt_resize_active
                on_active: root.opt_resize_active = self.active
                size_hint_x: None
                width: dp(48)
                size_hint_y: None
                height: dp(30)
            
            Label:
                text: "Ширина (px):"
                disabled: not root.opt_resize_active
                size_hint_y: None
                height: dp(30)
            TextInput:
                text: root.opt_resize_width
                on_text: root.opt_resize_width = self.text
                input_filter: 'int'
                disabled: not root.opt_resize_active
                size_hint_y: None
                height: dp(30)

            Label:
                text: "Висота (px):"
                disabled: not root.opt_resize_active
                size_hint_y: None
                height: dp(30)
            TextInput:
                text: root.opt_resize_height
                on_text: root.opt_resize_height = self.text
                input_filter: 'int'
                disabled: not root.opt_resize_active
                size_hint_y: None
                height: dp(30)
            
            # --- Додайте сюди інші опції редагування ---
            Label:
                text: "(Інші опції редагування тут)"
                size_hint_y: None
                height: dp(30)
            BoxLayout: 
                size_hint_y: None
                height: dp(30)

    Button:
        text: "Почати обробку"
        size_hint_y: None
        height: dp(50)
        on_press: root.run_processing()
        background_color: (0.2, 0.6, 0.2, 1)

    ProgressBar:
        id: progress_bar
        value: root.progress_bar_value 
        max: 1.0
        size_hint_y: None
        height: dp(20)

    Label:
        id: status_label
        text: root.status_label_text
        size_hint_y: None
        height: dp(40)
        text_size: self.width - dp(20), None 
        halign: 'center'
        valign: 'middle'
""",
    "ui/widgets/__init__.py": "# Кастомні віджети Kivy",
    "ffmpeg_binaries/README.txt": """Будь ласка, розмістіть тут виконувані файли FFmpeg для Windows Desktop збірок:
- ffmpeg.exe
- ffprobe.exe
- (та будь-які супутні .dll, якщо вони необхідні для вашої збірки FFmpeg)

Завантажити FFmpeg можна з офіційного сайту: https://ffmpeg.org/download.html
(Для Windows зазвичай обирають збірки від gyan.dev або BtbN).

Для Android збірок через Buildozer, FFmpeg має бути включений як рецепт (recipe).
""",
    "assets/app_icon.png": "", # Порожній файл, замініть реальною PNG іконкою
    "assets/README.txt": """Розмістіть тут ресурси для GUI, наприклад:
- app_icon.png (іконка програми, зазвичай 512x512 для Kivy/Buildozer)
- кастомні шрифти (.ttf)
- інші зображення або файли, що використовуються в інтерфейсі.
""",
    "output/README.txt": """Ця папка призначена для збереження оброблених відеофайлів.
Ви можете обрати іншу папку для збереження в самій програмі.
""",
    "buildozer.spec": """# Конфігураційний файл для Buildozer
[app]
title = Відео Редактор Kivy
package.name = videoeditorua
package.domain = org.example # Замініть на свій домен
source.dir = . 
source.include_exts = py,png,jpg,kv,atlas,ttf,json 

version = 0.1

requirements = python3,kivy,moviepy,opencv-python,numpy,plyer 
# Pillow часто потрібен як залежність для Kivy/OpenCV/MoviePy

orientation = portrait 

icon.filename = %(source.dir)s/assets/app_icon.png 
# presplash.filename = %(source.dir)s/assets/presplash.png

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET

# android.api = 33 
# android.minapi = 21 

android.archs = arm64-v8a, armeabi-v7a 

[buildozer]
log_level = 2 
warn_on_root = 1 
""",
    "PyInstaller.spec": """# Файл конфігурації PyInstaller для Desktop збірок.
# Назвіть цей файл відповідно до назви вашого додатку, наприклад, video_editor_kivy_ua.spec
#
# # -*- mode: python ; coding: utf-8 -*-

from kivy_deps import hookspath, runtime_hooks 

block_cipher = None

a = Analysis(['main.py'], 
             pathex=['.'], 
             binaries=[
                 # ('ffmpeg_binaries/ffmpeg.exe', 'ffmpeg_binaries'), 
                 # ('ffmpeg_binaries/ffprobe.exe', 'ffmpeg_binaries')
             ],
             datas=[
                 ('assets', 'assets'), 
                 ('ui', 'ui') 
             ],
             hiddenimports=[],
             hookspath=hookspath(), 
             runtime_hooks=runtime_hooks(), 
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='VideoEditorKivyUA', 
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True, 
          console=False, 
          # icon='assets/app_icon.ico' # Для Windows потрібна .ico іконка
          )

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='VideoEditorKivyUA_App') 
""",
    "requirements.txt": """kivy[base,full] 
# kivy_deps.gstreamer # або sdl2, angle - залежності для Kivy
opencv-python
moviepy
numpy 
Pillow 
plyer 
""",
    "README.md": f"""# Відео Редактор на Kivy (Українська версія)

Програма для редагування відео, створена з використанням Kivy для GUI, OpenCV та MoviePy для обробки відео.

## Основні технології
- GUI: Kivy
- Обробка відео: OpenCV, MoviePy
- Включення FFmpeg для desktop (Windows)

## Встановлення залежностей (для Desktop розробки)
Перед встановленням Kivy, можуть знадобитися системні залежності.
Див. документацію Kivy: https://kivy.org/doc/stable/gettingstarted/installation.html

```bash
pip install -r requirements.txt
```
Можливо, знадобиться встановити залежності Kivy для вашої системи (наприклад, `kivy_deps.sdl2`, `kivy_deps.glew` або `kivy_deps.angle`):
```bash
# Для Windows (рекомендовано):
# pip install kivy_deps.angle
# Для Linux/macOS:
# pip install kivy_deps.sdl2 kivy_deps.glew
```

## Запуск Desktop версії (з вихідного коду)
```bash
python main.py
```

## Збірка для Windows (PyInstaller)
1.  Встановіть PyInstaller: `pip install pyinstaller`
2.  Встановіть `kivy_deps.angle` (рекомендовано для Windows): `pip install kivy_deps.angle`
3.  Розмістіть `ffmpeg.exe` та `ffprobe.exe` у папці `ffmpeg_binaries`.
4.  Розмістіть іконку `app_icon.png` (для Kivy) та `app_icon.ico` (для .exe) у `assets`.
5.  Перейменуйте `PyInstaller.spec` на `video_editor_kivy_ua.spec` (або іншу відповідну назву) та відредагуйте його за потреби.
6.  Запустіть збірку: `pyinstaller video_editor_kivy_ua.spec`

## Збірка для Android (Buildozer)
1.  Встановіть Buildozer: `pip install buildozer`
2.  Налаштуйте середовище для збірки під Android (SDK, NDK тощо).
    Див. документацію Buildozer: https://buildozer.readthedocs.io/en/latest/installation.html
3.  Відредагуйте `buildozer.spec`.
    **Важливо:** Включення `opencv-python` та `moviepy` (з `ffmpeg`) в Android збірку – **складне завдання**. Можуть знадобитися кастомні рецепти для `python-for-android`.
4.  Запустіть збірку (з папки проєкту):
    `buildozer android debug`
    `buildozer android release`

## Примітки
- "Description" (Опис) репозиторію зазвичай встановлюється на платформах типу GitHub/GitLab.
- Розмістіть виконувані файли `ffmpeg.exe` та `ffprobe.exe` у папці `ffmpeg_binaries` (для Windows).
- Розмістіть іконку `app_icon.png` (наприклад, 512x512) у папці `assets`.
""",
    ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.pyd

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
# *.spec # .spec файл зазвичай зберігається

# Kivy
.kivy/
# *.kv~ # Резервні копії KV файлів
# *.py~ # Резервні копії Python файлів
*.kivy_ kivy_*.log

# Buildozer
.buildozer/ 
bin/ 
# buildozer.spec~ 

# IDE / Editor specific files
.vscode/
.idea/
*.swp
*~
.DS_Store 

# Virtual environments
venv/
.venv/
env/
.env/
ENV/
*.env 

# Windows specific
Thumbs.db
ehthumbs.db
Desktop.ini

# Папку output/ поки не ігноруємо, оскільки там є README.txt.
# Якщо ви не хочете комітити вміст output/, додайте 'output/*' сюди.
# ffmpeg_binaries/ також не ігнорується для прикладу з README.txt
"""
}
# --- Кінець конфігурації ---

def create_project_structure_with_git_ua():
    """
    Створює структуру папок та файлів для Kivy проєкту українською мовою та ініціалізує Git.
    """
    project_root = Path(project_name)
    print(f"Створення Kivy проєкту '{project_root}' (українська локалізація)...")

    if project_root.exists():
        print(f"ПОПЕРЕДЖЕННЯ: Директорія '{project_root}' вже існує. Файли можуть бути перезаписані.")
    
    # Створення директорій
    for dir_name in directories_to_create:
        dir_path = project_root / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  Створено/існує директорія: {dir_path}")
        except OSError as e:
            print(f"ПОМИЛКА при створенні директорії {dir_path}: {e}")
            return

    # Створення файлів
    for rel_file_path, content in files_to_create_with_content.items():
        file_path = project_root / rel_file_path
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")
            print(f"  Створено файл: {file_path}")
            if ".png" in rel_file_path and not content:
                 print(f"    -> Це заглушка для {rel_file_path}. Замініть її реальним файлом.")
        except OSError as e:
            print(f"ПОМИЛКА при створенні файлу {file_path}: {e}")

    print(f"\nСтруктура проєкту '{project_root}' успішно створена в поточній директорії ({Path.cwd()}).")

    # Ініціалізація Git
    if shutil.which("git"): 
        print("\nІніціалізація Git-репозиторію...")
        try:
            # Перевіряємо, чи це вже Git-репозиторій
            is_git_repo = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=project_root, capture_output=True, text=True, check=False).stdout.strip() == "true"
            
            if not is_git_repo:
                subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True)
                print(f"  Git-репозиторій ініціалізовано в '{project_root}'")
                # Встановлюємо гілку за замовчуванням на 'main'
                subprocess.run(["git", "branch", "-M", "main"], cwd=project_root, check=True, capture_output=True)
                print(f"  Головну гілку встановлено на 'main'.")
            else:
                print(f"  Директорія '{project_root}' вже є Git-репозиторієм.")

            subprocess.run(["git", "add", "."], cwd=project_root, check=True, capture_output=True)
            print(f"  Всі файли додано до індексації Git.")
            
            # Перевіряємо, чи є що комітити
            status_result = subprocess.run(["git", "status", "--porcelain"], cwd=project_root, capture_output=True, text=True, check=True)
            if status_result.stdout: # Якщо є зміни для коміту
                commit_message = "Початкова структура проєкту (автоматично згенеровано)"
                subprocess.run(["git", "commit", "-m", commit_message], cwd=project_root, check=True, capture_output=True)
                print(f"  Створено початковий коміт: '{commit_message}'")
            else:
                print("  Немає змін для створення початкового коміту (можливо, файли не змінилися).")

        except subprocess.CalledProcessError as e:
            print(f"ПОМИЛКА під час виконання команди Git: {e}")
            if e.stdout: print(f"Stdout: {e.stdout.decode(errors='ignore') if isinstance(e.stdout, bytes) else e.stdout}")
            if e.stderr: print(f"Stderr: {e.stderr.decode(errors='ignore') if isinstance(e.stderr, bytes) else e.stderr}")
        except FileNotFoundError:
             print("ПОМИЛКА: Команду 'git' не знайдено, хоча shutil.which її бачив. Перевірте PATH.")
    else:
        print("\nGit не знайдено в системі. Будь ласка, встановіть Git та ініціалізуйте репозиторій вручну.")

    print("\nРЕКОМЕНДАЦІЇ:")
    print(f"- 'Description' (Опис) для репозиторію зазвичай встановлюється на платформах типу GitHub/GitLab при створенні віддаленого репозиторію.")
    print(f"- Перегляньте та налаштуйте `buildozer.spec` та `PyInstaller.spec` (перейменуйте його на `{project_name}.spec`).")
    print(f"- Розмістіть бінарні файли FFmpeg у папці '{project_root / 'ffmpeg_binaries'}' (для Windows).")
    print(f"- Замініть `app_icon.png` у папці '{project_root / 'assets'}' на вашу реальну іконку (та створіть `app_icon.ico` для Windows).")
    print(f"- Встановлення залежностей та збірка (особливо для Android) можуть потребувати додаткових кроків. Див. README.md та офіційну документацію.")

if __name__ == "__main__":
    create_project_structure_with_git_ua()
# Створення Kivy проєкту з українською локалізацією