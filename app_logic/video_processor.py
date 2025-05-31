# app_logic/video_processor.py
from moviepy.editor import VideoFileClip
# from moviepy.video.fx import all as vfx # Розкоментуйте, якщо потрібні ефекти

import os
import time # Для імітації прогресу та перевірки скасування

# Тепер ця функція приймає check_if_cancelled_callback
def process_video_task(input_path, output_folder, options, 
                       status_callback, progress_callback, check_if_cancelled_callback):
    try:
        # Перевірка вхідних шляхів (залишається)
        if not input_path or not os.path.exists(input_path):
            status_callback("Помилка: Вхідний файл не знайдено.")
            return None # Повертаємо None при помилці
        if not output_folder or not os.path.isdir(output_folder):
            status_callback("Помилка: Папку для збереження не знайдено або вказано невірний шлях.")
            return None

        status_callback(f"Завантаження відео: {os.path.basename(input_path)}")
        progress_callback(0.05) 

        # Перевірка на скасування перед завантаженням кліпу
        if check_if_cancelled_callback():
            status_callback("Обробку скасовано користувачем.")
            return None

        clip = VideoFileClip(input_path)
        processed_clip = clip 

        # --- Зміна роздільної здатності (логіка залишається, але з перевірками на скасування) ---
        if options.get("resize_active"):
            status_callback("Застосування зміни роздільної здатності...")
            try:
                width_str = options.get("width", "")
                height_str = options.get("height", "")

                if not width_str or not height_str:
                    status_callback("Помилка: Ширина або висота для зміни розміру не вказані.")
                else:
                    width = int(width_str)
                    height = int(height_str)
                    if width > 0 and height > 0:
                        # Перед довгою операцією перевіряємо скасування
                        if check_if_cancelled_callback():
                            status_callback("Обробку скасовано перед зміною розміру.")
                            clip.close()
                            return None
                        processed_clip = processed_clip.resize(newsize=(width, height))
                        status_callback(f"Роздільну здатність змінено на {width}x{height}")
                    else:
                        status_callback("Помилка: Ширина та висота для зміни розміру мають бути більшими за 0.")
            except ValueError:
                status_callback("Помилка: Некоректні значення для ширини/висоти (мають бути цілими числами).")
            except Exception as e:
                status_callback(f"Помилка при зміні розміру: {str(e)}")
        
        progress_callback(0.5) 
        if check_if_cancelled_callback():
            status_callback("Обробку скасовано після зміни розміру.")
            if 'clip' in locals(): clip.close()
            if 'processed_clip' in locals() and processed_clip != clip and hasattr(processed_clip, 'close'): processed_clip.close()
            return None
            
        # --- Тут будуть інші операції редагування ---
        # Наприклад, імітуємо ще якусь роботу
        # for i in range(50, 81):
        #     if check_if_cancelled_callback():
        #         status_callback("Обробку скасовано під час додаткових операцій.")
        #         if 'clip' in locals(): clip.close()
        #         if 'processed_clip' in locals() and processed_clip != clip and hasattr(processed_clip, 'close'): processed_clip.close()
        #         return None
        #     time.sleep(0.02) # Імітація
        #     progress_callback(i / 100.0)
        #     status_callback(f"Виконується крок {i}/100...")


        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        suffix = "_edited_pyside" # Новий суфікс
        if options.get("resize_active"):
             # Можна додати більш точну перевірку, чи операція дійсно була успішною
            current_size = processed_clip.size
            if str(current_size[0]) == options.get("width", "") and str(current_size[1]) == options.get("height", ""):
                 suffix += "_resized"
            
        output_file_name = f"{name}{suffix}{ext}"
        output_path = os.path.join(output_folder, output_file_name)

        status_callback(f"Збереження відео в: {output_path}")
        
        # Перевірка на скасування перед записом файлу (тривала операція)
        if check_if_cancelled_callback():
            status_callback("Обробку скасовано перед збереженням файлу.")
            if 'clip' in locals(): clip.close()
            if 'processed_clip' in locals() and processed_clip != clip and hasattr(processed_clip, 'close'): processed_clip.close()
            return None

        # Для write_videofile можна також передати колбек для прогресу, якщо він підтримується,
        # або обернути його для періодичної перевірки скасування.
        # Поки що MoviePy не має зручного progress_callback для write_videofile, який би легко інтегрувався.
        # Прогрес тут буде стрибком.
        processed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=4, logger=None)

        # Якщо ми дійшли сюди і не було скасування:
        if check_if_cancelled_callback(): # Остання перевірка, хоча малоймовірно після write_videofile
            status_callback("Обробку скасовано одразу після збереження.")
            # Файл вже збережено, але позначаємо як скасоване
            if 'clip' in locals(): clip.close()
            if 'processed_clip' in locals() and processed_clip != clip and hasattr(processed_clip, 'close'): processed_clip.close()
            return None # Або output_path, якщо хочемо зберегти результат скасованої операції

        progress_callback(1.0) 
        status_callback(f"Відео успішно збережено: {output_path}")
        return output_path # Повертаємо шлях до файлу при успіху

    except Exception as e:
        status_callback(f"Загальна помилка обробки відео в `process_video_task`: {str(e)}")
        import traceback
        traceback.print_exc()
        return None # Повертаємо None при помилці
    finally:
        if 'clip' in locals():
            clip.close()
        if 'processed_clip' in locals() and processed_clip != clip and hasattr(processed_clip, 'close'):
            try:
                processed_clip.close()
            except Exception as e_close:
                print(f"Не вдалося закрити processed_clip у finally: {e_close}")