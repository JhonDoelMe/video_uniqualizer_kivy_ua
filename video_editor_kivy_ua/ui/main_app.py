# Основний файл Kivy App та логіка GUI
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
        popup_content.add_widget(Label(text=f"{message}\n\nБудь ласка, введіть шлях вручну.", size_hint_y=None, height=100))
        btn_ok = Button(text="OK", size_hint_y=None, height=40)
        popup_content.add_widget(btn_ok)
        
        popup = Popup(title="Помилка вибору файлу/папки", content=popup_content, size_hint=(0.9, 0.5), auto_dismiss=False)
        btn_ok.bind(on_press=popup.dismiss)
        popup.open()
