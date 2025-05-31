# app_logic/video_processor.py
from moviepy.editor import VideoFileClip
from moviepy.video.fx import all as vfx
from moviepy.audio.fx import all as afx # ! Додано для аудіо ефектів
import numpy as np # ! Додано для генерації шуму
import os
import time 

# Визначаємо кастомний виняток для чистого переривання з глибоких викликів
class ProcessingCancelledError(Exception):
    pass

def process_video_task(input_path, output_folder, options, 
                       status_callback, progress_callback, check_if_cancelled_callback):
    try:
        if not input_path or not os.path.exists(input_path):
            status_callback("Помилка: Вхідний файл не знайдено.")
            return None 
        if not output_folder or not os.path.isdir(output_folder):
            status_callback("Помилка: Папку для збереження не знайдено або вказано невірний шлях.")
            return None

        status_callback(f"Завантаження відео: {os.path.basename(input_path)}")
        progress_callback(0.05) 

        if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано користувачем перед завантаженням кліпу.")

        clip = VideoFileClip(input_path)
        processed_clip = clip 
        
        current_progress = 0.10 
        # Розрахуємо кількість активних основних кроків для розподілу прогресу
        num_major_steps = 0
        if options.get("resize_active"): num_major_steps +=1
        if options.get("bw_filter_active"): num_major_steps +=1
        if options.get("uniek_filter_active"): num_major_steps +=1 # Комплекс "Унік" вважаємо одним великим кроком
        
        # Загальний прогрес, доступний для основних операцій (залишаємо 0.1 для завантаження і 0.1 для збереження)
        available_progress_for_ops = 0.8 
        progress_step = available_progress_for_ops / num_major_steps if num_major_steps > 0 else 0

        # --- Зміна роздільної здатності ---
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
                        if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано під час зміни розміру.")
                        processed_clip = processed_clip.resize(newsize=(width, height))
                        status_callback(f"Роздільну здатність змінено на {width}x{height}")
                    else:
                        status_callback("Помилка: Ширина та висота для зміни розміру мають бути більшими за 0.")
            except ValueError: status_callback("Помилка: Некоректні значення для ширини/висоти.")
            except ProcessingCancelledError: raise # Просто передаємо далі
            except Exception as e: status_callback(f"Помилка при зміні розміру: {str(e)}")
            current_progress += progress_step
            progress_callback(current_progress)

        # --- Чорно-білий фільтр ---
        if options.get("bw_filter_active"):
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано перед Ч/Б фільтром.")
            status_callback("Застосування чорно-білого фільтру...")
            try:
                processed_clip = processed_clip.fx(vfx.blackwhite)
                status_callback("Чорно-білий фільтр застосовано.")
            except ProcessingCancelledError: raise
            except Exception as e: status_callback(f"Помилка при застосуванні Ч/Б фільтру: {str(e)}")
            current_progress += progress_step
            progress_callback(current_progress)

        # --- ! Комплекс фільтрів "Унік" ---
        if options.get("uniek_filter_active"):
            status_callback("Застосування комплексу 'Унік' фільтрів...")
            uniek_filters_count = 6 # Кількість фільтрів в комплексі "Унік"
            uniek_progress_sub_step = progress_step / uniek_filters_count if uniek_filters_count > 0 else 0

            # 1. Незначна обрізка країв
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано в 'Унік': Обрізка")
            try:
                status_callback("Унік (1/6): Незначна обрізка...")
                h_orig, w_orig = processed_clip.h, processed_clip.w
                crop_px = 2
                if w_orig > crop_px * 2 and h_orig > crop_px * 2: # Запобігання помилки з малими розмірами
                    processed_clip = processed_clip.crop(x1=crop_px, y1=crop_px, 
                                                         width=w_orig - crop_px * 2, 
                                                         height=h_orig - crop_px * 2)
                else: status_callback("Унік (1/6): Обрізку пропущено (замалий розмір).")
            except Exception as e: status_callback(f"Унік (1/6) Помилка обрізки: {e}")
            current_progress += uniek_progress_sub_step; progress_callback(current_progress)

            # 2. Легка гамма-корекція
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано в 'Унік': Гамма")
            try:
                status_callback("Унік (2/6): Гамма-корекція...")
                processed_clip = processed_clip.fx(vfx.gamma_corr, 1.03)
            except Exception as e: status_callback(f"Унік (2/6) Помилка гамма-корекції: {e}")
            current_progress += uniek_progress_sub_step; progress_callback(current_progress)

            # 3. Незначне регулювання контрастності
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано в 'Унік': Контраст")
            try:
                status_callback("Унік (3/6): Регулювання контрастності...")
                processed_clip = processed_clip.fx(vfx.lum_contrast, lum=0, contrast=3) # contrast - додається
            except Exception as e: status_callback(f"Унік (3/6) Помилка контрасту: {e}")
            current_progress += uniek_progress_sub_step; progress_callback(current_progress)

            # 4. Додавання дуже легкого шуму
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано в 'Унік': Шум")
            try:
                status_callback("Унік (4/6): Додавання легкого шуму...")
                def add_subtle_noise(frame):
                    # if check_if_cancelled_callback(): # Ця перевірка тут не спрацює ефективно для fl_image
                    #    raise ProcessingCancelledError("Скасовано під час додавання шуму до кадру")
                    gauss = np.random.normal(0, 1.5, frame.shape) # Std dev 1.5
                    noisy_frame = np.clip(frame.astype(np.int16) + gauss, 0, 255).astype(np.uint8)
                    return noisy_frame
                processed_clip = processed_clip.fl_image(add_subtle_noise)
            except ProcessingCancelledError: raise # Якщо б помилка виникла всередині fl_image
            except Exception as e: status_callback(f"Унік (4/6) Помилка додавання шуму: {e}")
            current_progress += uniek_progress_sub_step; progress_callback(current_progress)
            
            # 5. Незначна зміна гучності аудіо
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано в 'Унік': Гучність аудіо")
            if processed_clip.audio:
                try:
                    status_callback("Унік (5/6): Зміна гучності аудіо...")
                    processed_clip.audio = processed_clip.audio.fx(afx.volumex, 1.02) # +2%
                except Exception as e: status_callback(f"Унік (5/6) Помилка зміни гучності: {e}")
            else: status_callback("Унік (5/6): Аудіо відсутнє, пропуск зміни гучності.")
            current_progress += uniek_progress_sub_step; progress_callback(current_progress)

            # 6. Дуже незначна зміна швидкості відео
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано в 'Унік': Швидкість")
            try:
                status_callback("Унік (6/6): Зміна швидкості відео...")
                processed_clip = processed_clip.speedx(0.995) # на 0.5% повільніше
            except Exception as e: status_callback(f"Унік (6/6) Помилка зміни швидкості: {e}")
            current_progress += uniek_progress_sub_step; progress_callback(min(current_progress, 0.8 + available_progress_for_ops)) # Обмежуємо прогрес

            status_callback("Комплекс 'Унік' фільтрів застосовано.")
        
        # --- Формування назви файлу ---
        base_name_original, ext = os.path.splitext(os.path.basename(input_path))
        output_parts = [base_name_original]
        applied_effects_tags = []

        if options.get("bw_filter_active"): # Перевіряємо, чи опція була активна
            # Потрібно мати більш надійний спосіб дізнатися, чи фільтр *дійсно* застосовано
            # Зараз просто довіряємо опції
            applied_effects_tags.append("bw")
        
        if options.get("uniek_filter_active"):
             applied_effects_tags.append("uniek")

        # Розмір додаємо завжди, якщо він відомий
        size_tag = "unknownSize"
        if hasattr(processed_clip, 'size') and processed_clip.size:
            final_width, final_height = processed_clip.size
            size_tag = f"{final_width}x{final_height}"
        
        if applied_effects_tags:
            output_parts.append("-".join(applied_effects_tags))
        output_parts.append(size_tag)
            
        output_file_name_base = "_".join(output_parts)
        output_file_name = f"{output_file_name_base}{ext}"
        output_path = os.path.join(output_folder, output_file_name)

        status_callback(f"Збереження відео в: {output_path}")
        progress_callback(0.9) 

        if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано перед збереженням файлу.")

        processed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=4, logger=None)

        if check_if_cancelled_callback(): 
            status_callback("Обробку скасовано одразу після збереження.")
            # Можна видалити частково збережений файл, якщо потрібно
            # if os.path.exists(output_path): os.remove(output_path)
            raise ProcessingCancelledError("Скасовано після запису файлу.")

        progress_callback(1.0) 
        status_callback(f"Відео успішно збережено: {output_path}")
        return output_path 

    except ProcessingCancelledError as e: # Обробка нашого кастомного винятку
        status_callback(str(e) if str(e) else "Обробку скасовано.")
        return None
    except Exception as e:
        status_callback(f"Загальна помилка обробки відео в `process_video_task`: {type(e).__name__} - {str(e)}")
        import traceback
        traceback.print_exc()
        return None 
    finally:
        if 'clip' in locals():
            try: clip.close()
            except Exception: pass
        if 'processed_clip' in locals() and processed_clip != clip and hasattr(processed_clip, 'close'):
            try: processed_clip.close()
            except Exception: pass