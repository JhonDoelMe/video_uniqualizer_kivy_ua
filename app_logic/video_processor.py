# Модуль з функціями обробки та редагування відео (MoviePy/OpenCV)
from moviepy.editor import VideoFileClip # , vfx (для ефектів)
# Якщо потрібні конкретні ефекти з vfx, розкоментуйте та імпортуйте їх:
# from moviepy.video.fx import all as vfx

import os
import threading
from kivy.clock import Clock # Для безпечного оновлення UI з іншого потоку

# Ця функція викликатиметься з UI, швидше за все, в окремому потоці
def process_video_task(input_path, output_folder, options, status_update_callback, progress_update_callback):
    try:
        # Перевірка вхідних шляхів
        if not input_path or not os.path.exists(input_path):
            Clock.schedule_once(lambda dt: status_update_callback("Помилка: Вхідний файл не знайдено."))
            return
        if not output_folder or not os.path.isdir(output_folder): # Перевірка, чи output_folder є директорією
            Clock.schedule_once(lambda dt: status_update_callback("Помилка: Папку для збереження не знайдено або вказано невірний шлях."))
            return

        Clock.schedule_once(lambda dt: status_update_callback(f"Завантаження відео: {os.path.basename(input_path)}"))
        Clock.schedule_once(lambda dt: progress_update_callback(0.05)) # Невеликий прогрес на етапі завантаження

        clip = VideoFileClip(input_path)
        processed_clip = clip # Починаємо з оригінального кліпу

        # --- Зміна роздільної здатності ---
        if options.get("resize_active"):
            Clock.schedule_once(lambda dt: status_update_callback("Застосування зміни роздільної здатності..."))
            try:
                # Отримуємо значення ширини та висоти з опцій
                # Kivy StringProperty передає рядки, тому конвертуємо в int
                # Додаємо перевірку, що значення не порожні перед конвертацією
                width_str = options.get("width", "")
                height_str = options.get("height", "")

                if not width_str or not height_str:
                    Clock.schedule_once(lambda dt: status_update_callback("Помилка: Ширина або висота для зміни розміру не вказані."))
                    # Не перериваємо, можливо інші операції ще будуть
                else:
                    width = int(width_str)
                    height = int(height_str)

                    if width > 0 and height > 0:
                        # MoviePy очікує newsize=(ширина, висота) або newsize=масштаб
                        # Також можна передати newsize=lambda t: (ширина_для_часу_t, висота_для_часу_t) для динаміки
                        # або newsize={'width': W, 'height': H}
                        processed_clip = processed_clip.resize(newsize=(width, height))
                        Clock.schedule_once(lambda dt: status_update_callback(f"Роздільну здатність змінено на {width}x{height}"))
                    else:
                        Clock.schedule_once(lambda dt: status_update_callback("Помилка: Ширина та висота для зміни розміру мають бути більшими за 0."))
            except ValueError:
                Clock.schedule_once(lambda dt: status_update_callback("Помилка: Некоректні значення для ширини/висоти (мають бути цілими числами)."))
                # Якщо помилка в конвертації, не продовжуємо з цією операцією
            except Exception as e:
                Clock.schedule_once(lambda dt: status_update_callback(f"Помилка при зміні розміру: {str(e)}"))
        
        Clock.schedule_once(lambda dt: progress_update_callback(0.5)) # Припускаємо, що зміна розміру - це половина роботи

        # --- Тут будуть інші операції редагування, якщо вони активні ---
        # ... наприклад, обрізка, зміна швидкості тощо ...

        # Формування імені вихідного файлу
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        # Додамо "_resized" до імені, якщо розмір було змінено, для наочності
        suffix = "_edited"
        if options.get("resize_active"): # Перевіряємо, чи була опція активна, а не чи вона вдалася
            # Краще мати більш точний флаг, чи операція дійсно була застосована
             # Але для простоти поки так
            suffix += "_resized"

        output_file_name = f"{name}{suffix}{ext}"
        output_path = os.path.join(output_folder, output_file_name)

        Clock.schedule_once(lambda dt: status_update_callback(f"Збереження відео в: {output_path}"))
        
        # Запис обробленого кліпу у файл
        # logger=None, щоб прибрати стандартний вивід прогресу MoviePy в консоль,
        # оскільки ми використовуємо свій Kivy ProgressBar.
        # threads=4 може прискорити запис, підберіть оптимальне значення для вашої системи.
        processed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=4, logger=None)

        Clock.schedule_once(lambda dt: progress_update_callback(1.0)) # Завершення прогресу
        Clock.schedule_once(lambda dt: status_update_callback(f"Відео успішно збережено: {output_path}"))

    except Exception as e:
        # Загальна обробка помилок на випадок непередбачених ситуацій
        Clock.schedule_once(lambda dt: status_update_callback(f"Загальна помилка обробки відео: {str(e)}"))
        import traceback
        traceback.print_exc() # Для детальної помилки в консолі розробника
    finally:
        # Важливо закривати кліпи, щоб звільнити ресурси
        if 'clip' in locals() and clip: # перевірка, чи змінна clip була створена
            clip.close()
        if 'processed_clip' in locals() and processed_clip and processed_clip != clip : # якщо processed_clip - це новий об'єкт
            try:
                # Деякі ефекти MoviePy можуть повертати об'єкти, що не мають методу close,
                # тому перевіряємо його наявність.
                if hasattr(processed_clip, 'close') and callable(processed_clip.close):
                    processed_clip.close()
            except Exception as e_close:
                # Можна залогувати, якщо закриття не вдалося, але не переривати роботу
                print(f"Не вдалося закрити processed_clip: {e_close}")
        
        # Повідомлення про завершення (або помилку, якщо вона була останньою)
        # Можливо, статус вже встановлено конкретною помилкою, тому не перезаписуємо його
        # Clock.schedule_once(lambda dt: status_update_callback("Обробку завершено (або сталася помилка)."))
        # Краще, якщо останнє повідомлення буде про успіх або конкретну помилку.
        pass # Статус вже має бути встановлений вище