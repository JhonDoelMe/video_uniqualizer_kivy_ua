# Основний файл Kivy App та логіка GUI
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView # ! Додано для вибору папок
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty, NumericProperty
from kivy.lang import Builder
from kivy.utils import platform
from kivy.clock import Clock
from kivy.metrics import dp # ! Додано для розмірів

import threading
import os
from pathlib import Path
from app_logic import video_processor

# Builder.load_file('ui/editor_layout.kv') # Якщо ім'я kv файлу відрізняється

class MainLayout(BoxLayout):
    status_label_text = StringProperty("Оберіть відео та опції для редагування...")
    progress_bar_value = NumericProperty(0)

    input_file_path = StringProperty("")
    output_folder_path = StringProperty("")

    opt_resize_active = BooleanProperty(False)
    opt_resize_width = StringProperty("1280")
    opt_resize_height = StringProperty("720")
    
    app = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        default_output_dir_name = "Edited_Videos" # Змінено на латиницю для шляху за замовчуванням
        if platform == 'android':
            try:
                from android.storage import Environment # type: ignore
                self.output_folder_path = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).getAbsolutePath()
                self.output_folder_path = os.path.join(self.output_folder_path, default_output_dir_name)
                if not os.path.exists(self.output_folder_path):
                    self.output_folder_path = os.path.join(App.get_running_app().user_data_dir, default_output_dir_name)
            except ImportError:
                 self.output_folder_path = os.path.join(App.get_running_app().user_data_dir, default_output_dir_name)
        else: # Desktop
            self.output_folder_path = str(Path.home() / "Videos" / default_output_dir_name) # Використовуємо "Videos"
        
        print(f"DEBUG: Початковий output_folder_path в __init__: {self.output_folder_path}")
        os.makedirs(self.output_folder_path, exist_ok=True)

    def select_video_file(self):
        # Залишаємо plyer для вибору файлу, оскільки він працював
        self.app.open_plyer_file_chooser(callback=self._on_file_selected)
        self.status_label_text = "Очікування вибору файлу..."

    def _on_file_selected(self, selection):
        print(f"DEBUG: _on_file_selected, selection: {selection}")
        if selection:
            if isinstance(selection, list) and len(selection) > 0:
                self.input_file_path = selection[0]
                self.status_label_text = f"Обрано файл: {os.path.basename(self.input_file_path)}"
                print(f"DEBUG: self.input_file_path оновлено на: {self.input_file_path}")
            else:
                self.status_label_text = "Вибір файлу скасовано (невірний формат)."
                print(f"DEBUG: _on_file_selected, невірний формат вибору: {selection}")
        else:
            self.status_label_text = "Вибір файлу скасовано."
            print("DEBUG: _on_file_selected, вибір скасовано користувачем.")

    def select_output_folder(self):
        # Тепер викликаємо новий Kivy-based folder chooser
        self.app.open_kivy_folder_chooser(callback=self._on_folder_selected,
                                          current_path=self.output_folder_path)
        self.status_label_text = "Очікування вибору папки..."
        print("DEBUG: select_output_folder викликано (Kivy Chooser), очікуємо callback...")

    def _on_folder_selected(self, selection): # selection тепер завжди очікується як список
        print(f"DEBUG (Kivy Chooser): _on_folder_selected, selection: {selection}, тип: {type(selection)}")
        if selection and isinstance(selection, list) and len(selection) > 0:
            selected_path = selection[0]
            if selected_path and os.path.isdir(selected_path):
                self.output_folder_path = selected_path
                self.status_label_text = f"Папка для збереження: {self.output_folder_path}"
                print(f"DEBUG (Kivy Chooser): self.output_folder_path ОНОВЛЕНО на: {self.output_folder_path}")
            else:
                self.status_label_text = "Вибір папки скасовано (невірний шлях)."
                print(f"DEBUG (Kivy Chooser): _on_folder_selected, невірний шлях: {selected_path}")
        else:
            self.status_label_text = "Вибір папки скасовано."
            print("DEBUG (Kivy Chooser): _on_folder_selected, вибір скасовано або порожній.")

    def run_processing(self):
        if not self.input_file_path:
            self._show_error_popup("Файл не обрано", "Будь ласка, оберіть вхідний відеофайл.")
            return
        if not self.output_folder_path:
            self._show_error_popup("Папку не обрано", "Будь ласка, оберіть папку для збереження.")
            return
        if not os.path.isdir(self.output_folder_path):
            self._show_error_popup("Папка не існує", f"Обрана папка для збереження не існує: {self.output_folder_path}")
            return
        
        print(f"DEBUG: run_processing, ПЕРЕД запуском потоку, output_folder_path: {self.output_folder_path}")
        
        options = {
            "resize_active": self.opt_resize_active,
            "width": self.opt_resize_width,
            "height": self.opt_resize_height,
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
        popup_content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        popup_content.add_widget(Label(text=message, size_hint_y=None, height=dp(80)))
        btn_ok = Button(text="OK", size_hint_y=None, height=dp(40))
        popup_content.add_widget(btn_ok)
        
        popup = Popup(title=title, content=popup_content, size_hint=(0.8, 0.4), auto_dismiss=False)
        btn_ok.bind(on_press=popup.dismiss)
        popup.open()

class VideoEditorApp(App):
    _folder_chooser_popup = None
    _folder_chooser_callback = None
    _kivy_filechooser_widget = None # Зберігаємо віджет FileChooser

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

    # Зберігаємо старий метод для вибору файлів (якщо він працював)
    def open_plyer_file_chooser(self, callback):
        try:
            from plyer import filechooser # type: ignore
            filechooser.open_file(on_selection=callback, filters=['*.mp4', '*.avi', '*.mkv', '*.mov'])
        except ImportError:
            self._show_general_error_popup("Помилка Plyer", "Plyer не встановлено або не налаштовано.")
        except Exception as e:
            self._show_general_error_popup("Помилка Plyer", f"Помилка Plyer file chooser: {e}")
            
    # --- Новий Kivy Folder Chooser ---
    def open_kivy_folder_chooser(self, callback, current_path=None):
        self._folder_chooser_callback = callback

        if not self._folder_chooser_popup:
            content = BoxLayout(orientation='vertical', spacing=dp(5), padding=dp(5))
            
            # Використовуємо Path.home() як початковий шлях, якщо current_path недійсний
            initial_path_to_show = str(Path.home())
            if current_path and os.path.isdir(current_path):
                initial_path_to_show = current_path
            
            # Створюємо FileChooser один раз і зберігаємо його
            self._kivy_filechooser_widget = FileChooserListView(
                path=initial_path_to_show, 
                dirselect=True, # Дозволяє обирати директорії
                # filters=[lambda folder, filename: os.path.isdir(os.path.join(folder, filename))] # Показувати тільки папки
            )
            
            buttons_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
            btn_select = Button(text="Обрати цю папку")
            btn_select.bind(on_press=self._handle_kivy_folder_selection)
            btn_cancel = Button(text="Скасувати")
            btn_cancel.bind(on_press=self._dismiss_kivy_folder_chooser)
            
            buttons_layout.add_widget(btn_select)
            buttons_layout.add_widget(btn_cancel)
            
            content.add_widget(self._kivy_filechooser_widget)
            content.add_widget(buttons_layout)
            
            self._folder_chooser_popup = Popup(title="Оберіть папку для збереження",
                                               content=content,
                                               size_hint=(0.9, 0.9),
                                               auto_dismiss=False)
        else:
            # Якщо Popup вже існує, просто оновлюємо шлях у FileChooser
            if current_path and os.path.isdir(current_path):
                 self._kivy_filechooser_widget.path = current_path
            else:
                 self._kivy_filechooser_widget.path = str(Path.home())


        self._folder_chooser_popup.open()

    def _handle_kivy_folder_selection(self, instance):
        # Для dirselect=True, обраний шлях - це поточний шлях FileChooser'а
        selected_path = self._kivy_filechooser_widget.path
        
        if os.path.isdir(selected_path):
            if self._folder_chooser_callback:
                self._folder_chooser_callback([selected_path]) # Передаємо як список для сумісності
        else: 
            if self._folder_chooser_callback:
                self._folder_chooser_callback([]) # Помилка або не обрано
        self._dismiss_kivy_folder_chooser()

    def _dismiss_kivy_folder_chooser(self, instance=None):
        if self._folder_chooser_popup:
            self._folder_chooser_popup.dismiss()
            
    def _show_general_error_popup(self, title, message): # Узагальнений метод для помилок
        print(message)
        popup_content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        popup_content.add_widget(Label(text=message, size_hint_y=None, height=dp(100)))
        btn_ok = Button(text="OK", size_hint_y=None, height=dp(40))
        popup_content.add_widget(btn_ok)
        
        popup = Popup(title=title, content=popup_content, size_hint=(0.9, 0.5), auto_dismiss=False)
        btn_ok.bind(on_press=popup.dismiss)
        popup.open()