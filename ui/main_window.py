# ui/main_window.py
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QCheckBox, QProgressBar, QComboBox,
    QFileDialog, QMessageBox, QSizePolicy, QSpacerItem, QGroupBox
)
from PySide6.QtCore import Qt, Slot, Signal, QThread
from PySide6.QtGui import QIcon

from moviepy.editor import VideoFileClip
from app_logic.video_processor import process_video_task 

class VideoProcessingThread(QThread):
    status_updated = Signal(str)
    progress_updated = Signal(int) 
    processing_finished = Signal(bool, str) 

    def __init__(self, input_path, output_folder, options):
        super().__init__()
        self.input_path = input_path
        self.output_folder = output_folder
        self.options = options
        self.is_cancelled_flag = False

    def run(self):
        try:
            def _emit_status(message):
                if not self.is_cancelled_flag: self.status_updated.emit(message)
            def _emit_progress(value_0_to_1):
                if not self.is_cancelled_flag: self.progress_updated.emit(int(value_0_to_1 * 100))
            def _check_if_cancelled():
                return self.is_cancelled_flag

            output_filepath = process_video_task(
                self.input_path, self.output_folder, self.options,
                _emit_status, _emit_progress, _check_if_cancelled
            )

            if self.is_cancelled_flag: self.processing_finished.emit(False, "Обробку скасовано користувачем.")
            elif output_filepath: self.processing_finished.emit(True, output_filepath)
            else: self.processing_finished.emit(False, "Не вдалося обробити відео (невідома помилка в завданні).")
        except Exception as e:
            error_message = f"Помилка під час обробки у video_processor: {str(e)}"
            self.status_updated.emit(error_message)
            self.processing_finished.emit(False, error_message)
            import traceback
            traceback.print_exc()

    def cancel(self):
        self.status_updated.emit("Спроба скасувати обробку...")
        self.is_cancelled_flag = True

class MainWindow(QMainWindow):
    PRESET_SETTINGS = {
        'tiktok_reels': {'width': "1080", 'height': "1920", 'resize_active': True, 'bw_filter_active': False, 'uniek_filter_active': False, 'name': "TikTok/Reels (1080x1920)"},
        'instagram_portrait': {'width': "1080", 'height': "1350", 'resize_active': True, 'bw_filter_active': False, 'uniek_filter_active': False, 'name': "Instagram Портрет (1080x1350)"},
        'instagram_square': {'width': "1080", 'height': "1080", 'resize_active': True, 'bw_filter_active': False, 'uniek_filter_active': False, 'name': "Instagram Квадрат (1080x1080)"},
        'youtube_1080p': {'width': "1920", 'height': "1080", 'resize_active': True, 'bw_filter_active': False, 'uniek_filter_active': False, 'name': "YouTube 1080p (1920x1080)"},
        'youtube_720p': {'width': "1280", 'height': "720", 'resize_active': True, 'bw_filter_active': False, 'uniek_filter_active': False, 'name': "YouTube 720p (1280x720)"},
    }
    DEFAULT_OPTIONS = {
        'resize_active': False, 'width': "1280", 'height': "720",
        'bw_filter_active': False,
        'uniek_filter_active': False,
        'rotation_angle': 0, 
        'flip_h_active': False, 
        'flip_v_active': False, 
    }
    ROTATION_MAP = { "Без повороту": 0, "90° за годинниковою": -90, "180°": 180, "90° проти годинникової": 90 }
    ROTATION_MAP_INV = {v: k for k, v in ROTATION_MAP.items()}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Відео Редактор на PySide6")
        self.setGeometry(100, 100, 900, 750) # Змінив ширину для горизонтального розміщення

        self.current_input_file = ""
        self.current_output_folder = str(Path.home() / "Videos" / "Edited_Videos_PySide")
        os.makedirs(self.current_output_folder, exist_ok=True)

        self._init_ui()
        self.reset_all_options(show_status=False) 
        self.processing_thread = None 

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) # Головний макет - вертикальний

        # --- 1. Секція вибору файлів ---
        file_selection_layout = QHBoxLayout()
        self.input_file_label = QLabel("Відеофайл: Не обрано")
        self.input_file_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btn_select_input = QPushButton("Обрати відео...")
        btn_select_input.clicked.connect(self.select_input_file)
        file_selection_layout.addWidget(self.input_file_label)
        file_selection_layout.addWidget(btn_select_input)
        main_layout.addLayout(file_selection_layout)

        output_folder_layout = QHBoxLayout()
        self.output_folder_label = QLabel(f"Папка збереження: {self.current_output_folder}")
        self.output_folder_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btn_select_output = QPushButton("Обрати папку...")
        btn_select_output.clicked.connect(self.select_output_folder)
        output_folder_layout.addWidget(self.output_folder_label)
        output_folder_layout.addWidget(btn_select_output)
        main_layout.addLayout(output_folder_layout)
        
        # --- 2. Секція медіа-інформації ---
        self.media_info_group = QWidget() 
        media_info_layout_main = QVBoxLayout(self.media_info_group) 
        media_info_layout_main.setContentsMargins(0,5,0,5)
        media_info_title = QLabel("--- Інформація про вихідний файл ---")
        media_info_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        media_info_layout_main.addWidget(media_info_title)
        media_info_grid = QVBoxLayout() 
        self.info_filename_label = QLabel("Файл: -")
        self.info_resolution_label = QLabel("Роздільна здатність: -")
        self.info_duration_label = QLabel("Тривалість: -")
        self.info_fps_label = QLabel("FPS: -")
        media_info_grid.addWidget(self.info_filename_label)
        media_info_grid.addWidget(self.info_resolution_label)
        media_info_grid.addWidget(self.info_duration_label)
        media_info_grid.addWidget(self.info_fps_label)
        media_info_layout_main.addLayout(media_info_grid)
        main_layout.addWidget(self.media_info_group)
        
        # --- Горизонтальний макет для пресетів та детальних опцій ---
        presets_and_options_HLayout = QHBoxLayout()

        # --- 3. Секція пресетів (ліва частина) ---
        presets_group = QGroupBox("Швидкі пресети") # Використовуємо QGroupBox
        presets_main_layout = QVBoxLayout(presets_group) # Макет для вмісту QGroupBox
        # presets_main_layout.addWidget(QLabel("Швидкі пресети для платформ:")) # Заголовок вже є у QGroupBox
        
        presets_grid_layout = QGridLayout() 
        btn_tiktok = QPushButton("TikTok/Reels\n(1080x1920)")
        btn_tiktok.clicked.connect(lambda: self.apply_preset('tiktok_reels'))
        presets_grid_layout.addWidget(btn_tiktok, 0, 0) 
        btn_insta_portrait = QPushButton("Instagram Портрет\n(1080x1350)")
        btn_insta_portrait.clicked.connect(lambda: self.apply_preset('instagram_portrait'))
        presets_grid_layout.addWidget(btn_insta_portrait, 0, 1) 
        btn_insta_square = QPushButton("Instagram Квадрат\n(1080x1080)")
        btn_insta_square.clicked.connect(lambda: self.apply_preset('instagram_square'))
        presets_grid_layout.addWidget(btn_insta_square, 0, 2) 
        btn_yt_1080 = QPushButton("YouTube 1080p\n(1920x1080)")
        btn_yt_1080.clicked.connect(lambda: self.apply_preset('youtube_1080p'))
        presets_grid_layout.addWidget(btn_yt_1080, 1, 0) 
        btn_yt_720 = QPushButton("YouTube 720p\n(1280x720)")
        btn_yt_720.clicked.connect(lambda: self.apply_preset('youtube_720p'))
        presets_grid_layout.addWidget(btn_yt_720, 1, 1) 
        btn_reset_options = QPushButton("Скинути опції")
        btn_reset_options.clicked.connect(self.reset_all_options)
        presets_grid_layout.addWidget(btn_reset_options, 1, 2) 
        presets_main_layout.addLayout(presets_grid_layout)
        presets_main_layout.addStretch(1) # Додаємо розтягувач, щоб кнопки не розтягувалися на всю висоту групи
        
        presets_and_options_HLayout.addWidget(presets_group) # Додаємо групу пресетів до горизонтального макету

        # --- 4. Секція детальних опцій (права частина) ---
        options_group = QGroupBox("Детальні налаштування / Фільтри") 
        options_layout = QVBoxLayout(options_group)

        # Опція: Змінити роздільну здатність
        self.cb_resize = QCheckBox("Змінити роздільну здатність")
        resize_fields_layout = QHBoxLayout()
        self.le_width = QLineEdit() 
        self.le_height = QLineEdit() 
        self.cb_resize.toggled.connect(self.le_width.setEnabled)
        self.cb_resize.toggled.connect(self.le_height.setEnabled)
        resize_fields_layout.addWidget(QLabel("Ширина:"))
        resize_fields_layout.addWidget(self.le_width)
        resize_fields_layout.addWidget(QLabel("Висота:"))
        resize_fields_layout.addWidget(self.le_height)
        options_layout.addWidget(self.cb_resize)
        options_layout.addLayout(resize_fields_layout)

        # Опція: Чорно-білий фільтр
        self.cb_bw_filter = QCheckBox("Чорно-білий фільтр")
        options_layout.addWidget(self.cb_bw_filter)

        # Опція: Унікалізація (комплекс фільтрів)
        self.cb_uniek_filter = QCheckBox("Унік (комплекс фільтрів)")
        options_layout.addWidget(self.cb_uniek_filter)

        # Секція: Трансформації кадру
        transform_group = QGroupBox("Трансформації кадру")
        transform_layout = QVBoxLayout(transform_group)
        rotation_layout = QHBoxLayout()
        rotation_layout.addWidget(QLabel("Поворот:"))
        self.rotation_combobox = QComboBox()
        self.rotation_combobox.addItems(list(self.ROTATION_MAP.keys()))
        rotation_layout.addWidget(self.rotation_combobox)
        transform_layout.addLayout(rotation_layout)
        self.cb_flip_h = QCheckBox("Дзеркально по горизонталі")
        transform_layout.addWidget(self.cb_flip_h)
        self.cb_flip_v = QCheckBox("Дзеркально по вертикалі")
        transform_layout.addWidget(self.cb_flip_v)
        options_layout.addWidget(transform_group) 
        options_layout.addStretch(1) # Додаємо розтягувач, щоб опції не розтягувалися на всю висоту групи
        
        presets_and_options_HLayout.addWidget(options_group) # Додаємо групу опцій до горизонтального макету
        
        # Можна встановити коефіцієнти розтягування для блоків
        presets_and_options_HLayout.setStretchFactor(presets_group, 1) # Пресети займають 1 частину
        presets_and_options_HLayout.setStretchFactor(options_group, 1) # Опції займають 1 частину (або 2 для більшого місця)

        main_layout.addLayout(presets_and_options_HLayout) # Додаємо горизонтальний макет до головного

        # --- Розтягувач та керуючі елементи внизу ---
        # main_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)) # Цей розтягувач тепер менш потрібен тут

        self.btn_process = QPushButton("Почати обробку")
        self.btn_process.setFixedHeight(40) 
        self.btn_process.clicked.connect(self.start_processing)
        main_layout.addWidget(self.btn_process)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Готово до роботи.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

    @Slot()
    def select_input_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Обрати відеофайл для редагування",
            self.current_input_file or str(Path.home()), 
            "Відеофайли (*.mp4 *.avi *.mkv *.mov);;Всі файли (*)"
        )
        if filepath:
            self.current_input_file = filepath
            self.input_file_label.setText(f"Відеофайл: {os.path.basename(filepath)}")
            self.info_filename_label.setText("Файл: -")
            self.info_resolution_label.setText("Роздільна здатність: -")
            self.info_duration_label.setText("Тривалість: -")
            self.info_fps_label.setText("FPS: -")
            self.status_label.setText(f"Обрано файл: {os.path.basename(filepath)}. Завантаження медіа-інфо...")
            self.load_media_info(filepath) 

    @Slot()
    def select_output_folder(self):
        foldername = QFileDialog.getExistingDirectory(
            self, "Обрати папку для збереження результату",
            self.current_output_folder or str(Path.home())
        )
        if foldername:
            self.current_output_folder = foldername
            self.output_folder_label.setText(f"Папка збереження: {foldername}")
            self.status_label.setText(f"Папку для збереження змінено на: {foldername}")

    def load_media_info(self, filepath):
        self.status_label.setText(f"Завантаження інформації про {os.path.basename(filepath)}...")
        QApplication.processEvents() 
        try:
            print(f"DEBUG: Завантаження медіа-інфо для: {filepath}")
            clip = VideoFileClip(filepath)
            self.info_filename_label.setText(f"Файл: {os.path.basename(filepath)}")
            if clip.size: 
                self.info_resolution_label.setText(f"Роздільна здатність: {clip.size[0]}x{clip.size[1]}")
            else:
                self.info_resolution_label.setText("Роздільна здатність: невідомо")
            self.info_duration_label.setText(f"Тривалість: {clip.duration:.2f} сек")
            self.info_fps_label.setText(f"FPS: {clip.fps:.2f}")
            clip.close() 
            self.status_label.setText(f"Медіа-інформацію для '{os.path.basename(filepath)}' завантажено.")
            print(f"DEBUG: Медіа-інфо завантажено: Розмір={self.info_resolution_label.text()}, Трив={self.info_duration_label.text()}, FPS={self.info_fps_label.text()}")
        except Exception as e:
            self.info_filename_label.setText(f"Файл: {os.path.basename(filepath)}")
            self.info_resolution_label.setText("Роздільна здатність: Помилка")
            self.info_duration_label.setText("Тривалість: Помилка")
            self.info_fps_label.setText("FPS: Помилка")
            error_msg = f"Помилка завантаження медіа-інфо: {type(e).__name__} - {e}"
            self.status_label.setText(error_msg)
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc() 

    @Slot(str) 
    def apply_preset(self, preset_name):
        preset_data = self.PRESET_SETTINGS.get(preset_name)
        if not preset_data:
            self.update_status_label(f"Помилка: Пресет '{preset_name}' не знайдено.")
            return

        self.cb_resize.setChecked(preset_data.get('resize_active', self.DEFAULT_OPTIONS['resize_active']))
        self.le_width.setText(preset_data.get('width', self.DEFAULT_OPTIONS['width']))
        self.le_height.setText(preset_data.get('height', self.DEFAULT_OPTIONS['height']))
        self.cb_bw_filter.setChecked(preset_data.get('bw_filter_active', self.DEFAULT_OPTIONS['bw_filter_active']))
        self.cb_uniek_filter.setChecked(preset_data.get('uniek_filter_active', self.DEFAULT_OPTIONS['uniek_filter_active']))
        self.rotation_combobox.setCurrentText(self.ROTATION_MAP_INV[preset_data.get('rotation_angle', self.DEFAULT_OPTIONS['rotation_angle'])])
        self.cb_flip_h.setChecked(preset_data.get('flip_h_active', self.DEFAULT_OPTIONS['flip_h_active']))
        self.cb_flip_v.setChecked(preset_data.get('flip_v_active', self.DEFAULT_OPTIONS['flip_v_active']))
        
        applied_preset_name = preset_data.get('name', preset_name.replace("_", " ").title())
        self.update_status_label(f"Застосовано пресет: {applied_preset_name}")

    @Slot()
    def reset_all_options(self, show_status=True): 
        self.cb_resize.setChecked(self.DEFAULT_OPTIONS['resize_active'])
        self.le_width.setText(self.DEFAULT_OPTIONS['width'])
        self.le_height.setText(self.DEFAULT_OPTIONS['height'])
        self.cb_bw_filter.setChecked(self.DEFAULT_OPTIONS['bw_filter_active'])
        self.cb_uniek_filter.setChecked(self.DEFAULT_OPTIONS['uniek_filter_active'])
        self.rotation_combobox.setCurrentText(self.ROTATION_MAP_INV[self.DEFAULT_OPTIONS['rotation_angle']])
        self.cb_flip_h.setChecked(self.DEFAULT_OPTIONS['flip_h_active'])
        self.cb_flip_v.setChecked(self.DEFAULT_OPTIONS['flip_v_active'])
        if show_status:
            self.update_status_label("Усі опції скинуто до значень за замовчуванням.")
    
    @Slot()
    def start_processing(self):
        if not self.current_input_file:
            QMessageBox.warning(self, "Помилка", "Будь ласка, оберіть вхідний відеофайл.")
            return
        if not self.current_output_folder:
            QMessageBox.warning(self, "Помилка", "Будь ласка, оберіть папку для збереження.")
            return

        options = {
            "resize_active": self.cb_resize.isChecked(),
            "width": self.le_width.text(),
            "height": self.le_height.text(),
            "bw_filter_active": self.cb_bw_filter.isChecked(),
            "uniek_filter_active": self.cb_uniek_filter.isChecked(),
            "rotation_angle": self.ROTATION_MAP[self.rotation_combobox.currentText()],
            "flip_h_active": self.cb_flip_h.isChecked(),
            "flip_v_active": self.cb_flip_v.isChecked(),
        }

        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.cancel() 
            if not self.processing_thread.wait(3000):
                 print("DEBUG: Попередній потік не завершився вчасно після скасування.")
        
        self.processing_thread = VideoProcessingThread(
            self.current_input_file, self.current_output_folder, options
        )
        self.processing_thread.status_updated.connect(self.update_status_label)
        self.processing_thread.progress_updated.connect(self.update_progress_bar)
        self.processing_thread.processing_finished.connect(self.on_processing_finished)
        
        self.btn_process.setEnabled(False) 
        self.progress_bar.setValue(0) 
        self.processing_thread.start() 

    @Slot(str)
    def update_status_label(self, message):
        self.status_label.setText(message)

    @Slot(int)
    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    @Slot(bool, str)
    def on_processing_finished(self, success, message_or_filepath):
        self.btn_process.setEnabled(True) 
        self.progress_bar.setValue(100 if success else self.progress_bar.value()) 
        if success:
            QMessageBox.information(self, "Завершено", f"Обробку завершено!\nФайл збережено: {message_or_filepath}")
        else:
            QMessageBox.critical(self, "Помилка", f"Під час обробки сталася помилка:\n{message_or_filepath}")

    def closeEvent(self, event):
        if self.processing_thread and self.processing_thread.isRunning():
            self.status_label.setText("Скасування обробки перед виходом...")
            self.processing_thread.cancel()
            if not self.processing_thread.wait(3000): 
                print("Потік обробки не завершився вчасно при закритті вікна.")
        event.accept()