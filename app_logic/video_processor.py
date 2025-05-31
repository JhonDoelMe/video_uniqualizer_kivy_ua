# app_logic/video_processor.py
from moviepy.editor import VideoFileClip
from moviepy.video.fx import all as vfx 
from moviepy.audio.fx import all as afx 
import numpy as np 
import os
import time 

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
        
        original_clip_for_info = clip # Зберігаємо посилання на оригінальний кліп для інформації

        current_progress = 0.05 # Початковий прогрес
        
        # Розрахуємо кількість активних основних кроків для розподілу прогресу
        num_major_steps = 0
        if options.get("resize_active"): num_major_steps +=1
        if options.get("bw_filter_active"): num_major_steps +=1
        if options.get("uniek_filter_active"): num_major_steps +=1
        if options.get("rotation_angle", 0) != 0 : num_major_steps +=1 # ! Враховуємо поворот
        if options.get("flip_h_active"): num_major_steps +=1          # ! Враховуємо дзеркало H
        if options.get("flip_v_active"): num_major_steps +=1          # ! Враховуємо дзеркало V
        
        available_progress_for_ops = 0.85 # Залишаємо 0.05 на завантаження і 0.1 на збереження
        progress_step = available_progress_for_ops / num_major_steps if num_major_steps > 0 else 0

        active_effects_tags = [] # Для назви файлу

        # --- Зміна роздільної здатності ---
        if options.get("resize_active"):
            status_callback("Застосування зміни роздільної здатності...")
            # ... (код для resize залишається майже без змін, додаємо перевірку скасування) ...
            try:
                width_str = options.get("width", "")
                height_str = options.get("height", "")
                if not width_str or not height_str: status_callback("Помилка: Ширина або висота для зміни розміру не вказані.")
                else:
                    width = int(width_str); height = int(height_str)
                    if width > 0 and height > 0:
                        if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано під час зміни розміру.")
                        processed_clip = processed_clip.resize(newsize=(width, height))
                        status_callback(f"Роздільну здатність змінено на {width}x{height}")
                    else: status_callback("Помилка: Ширина та висота > 0.")
            except ValueError: status_callback("Помилка: Некоректні значення для ширини/висоти.")
            except ProcessingCancelledError: raise
            except Exception as e: status_callback(f"Помилка при зміні розміру: {str(e)}")
            current_progress += progress_step; progress_callback(current_progress)

        # --- ! Нові трансформації: Поворот та Дзеркало ---
        rotation_angle = options.get("rotation_angle", 0)
        if rotation_angle != 0:
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано перед поворотом.")
            status_callback(f"Застосування повороту на {rotation_angle}°...")
            try:
                processed_clip = processed_clip.rotate(rotation_angle, expand=True) # expand=True щоб уникнути обрізки, але розмір може змінитися
                status_callback(f"Поворот на {rotation_angle}° застосовано.")
                active_effects_tags.append(f"rot{rotation_angle}")
            except ProcessingCancelledError: raise
            except Exception as e: status_callback(f"Помилка при повороті: {str(e)}")
            current_progress += progress_step; progress_callback(current_progress)

        if options.get("flip_h_active"):
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано перед горизонтальним дзеркалом.")
            status_callback("Застосування горизонтального дзеркального відображення...")
            try:
                processed_clip = processed_clip.fx(vfx.mirror_x)
                status_callback("Горизонтальне дзеркало застосовано.")
                active_effects_tags.append("fliph")
            except ProcessingCancelledError: raise
            except Exception as e: status_callback(f"Помилка горизонтального дзеркала: {str(e)}")
            current_progress += progress_step; progress_callback(current_progress)

        if options.get("flip_v_active"):
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано перед вертикальним дзеркалом.")
            status_callback("Застосування вертикального дзеркального відображення...")
            try:
                processed_clip = processed_clip.fx(vfx.mirror_y)
                status_callback("Вертикальне дзеркало застосовано.")
                active_effects_tags.append("flipv")
            except ProcessingCancelledError: raise
            except Exception as e: status_callback(f"Помилка вертикального дзеркала: {str(e)}")
            current_progress += progress_step; progress_callback(current_progress)
        # --- Кінець нових трансформацій ---

        # --- Чорно-білий фільтр ---
        if options.get("bw_filter_active"):
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано перед Ч/Б фільтром.")
            status_callback("Застосування чорно-білого фільтру...")
            try:
                processed_clip = processed_clip.fx(vfx.blackwhite)
                status_callback("Чорно-білий фільтр застосовано.")
                active_effects_tags.append("bw") # Додаємо тег до назви файлу
            except ProcessingCancelledError: raise
            except Exception as e: status_callback(f"Помилка при застосуванні Ч/Б фільтру: {str(e)}")
            current_progress += progress_step; progress_callback(current_progress)

        # --- Комплекс фільтрів "Унік" ---
        if options.get("uniek_filter_active"):
            status_callback("Застосування комплексу 'Унік' фільтрів...")
            uniek_filters_count = 6 
            uniek_progress_sub_step = progress_step / uniek_filters_count if uniek_filters_count > 0 and progress_step > 0 else 0.01 # Маленький крок, якщо progress_step=0

            # 1. Обрізка
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано в 'Унік': Обрізка")
            try:
                status_callback("Унік (1/6): Незначна обрізка...")
                h_orig, w_orig = processed_clip.h, processed_clip.w; crop_px = 2
                if w_orig > crop_px*2 and h_orig > crop_px*2: 
                    processed_clip = processed_clip.crop(x1=crop_px,y1=crop_px,width=w_orig-crop_px*2,height=h_orig-crop_px*2)
                else: status_callback("Унік (1/6): Обрізку пропущено (замалий розмір).")
            except Exception as e: status_callback(f"Унік (1/6) Помилка обрізки: {e}")
            current_progress += uniek_progress_sub_step; progress_callback(min(current_progress, 0.9))


            # 2. Гамма-корекція
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано в 'Унік': Гамма")
            try:
                status_callback("Унік (2/6): Гамма-корекція...")
                processed_clip = processed_clip.fx(vfx.gamma_corr, 1.03)
            except Exception as e: status_callback(f"Унік (2/6) Помилка гамма-корекції: {e}")
            current_progress += uniek_progress_sub_step; progress_callback(min(current_progress, 0.9))

            # 3. Контрастність
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано в 'Унік': Контраст")
            try:
                status_callback("Унік (3/6): Регулювання контрастності...")
                processed_clip = processed_clip.fx(vfx.lum_contrast, lum=0, contrast=3)
            except Exception as e: status_callback(f"Унік (3/6) Помилка контрасту: {e}")
            current_progress += uniek_progress_sub_step; progress_callback(min(current_progress, 0.9))

            # 4. Шум
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано в 'Унік': Шум")
            try:
                status_callback("Унік (4/6): Додавання легкого шуму...")
                def add_subtle_noise(frame):
                    gauss = np.random.normal(0, 1.5, frame.shape) 
                    noisy_frame = np.clip(frame.astype(np.int16) + gauss, 0, 255).astype(np.uint8)
                    return noisy_frame
                processed_clip = processed_clip.fl_image(add_subtle_noise)
            except Exception as e: status_callback(f"Унік (4/6) Помилка додавання шуму: {e}")
            current_progress += uniek_progress_sub_step; progress_callback(min(current_progress, 0.9))
            
            # 5. Гучність аудіо
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано в 'Унік': Гучність аудіо")
            if processed_clip.audio:
                try:
                    status_callback("Унік (5/6): Зміна гучності аудіо...")
                    processed_clip.audio = processed_clip.audio.fx(afx.volumex, 1.02)
                except Exception as e: status_callback(f"Унік (5/6) Помилка зміни гучності: {e}")
            else: status_callback("Унік (5/6): Аудіо відсутнє, пропуск зміни гучності.")
            current_progress += uniek_progress_sub_step; progress_callback(min(current_progress, 0.9))

            # 6. Швидкість відео
            if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано в 'Унік': Швидкість")
            try:
                status_callback("Унік (6/6): Зміна швидкості відео...")
                processed_clip = processed_clip.speedx(0.995) 
            except Exception as e: status_callback(f"Унік (6/6) Помилка зміни швидкості: {e}")
            current_progress = min(current_progress + uniek_progress_sub_step, 0.9) # Завершуємо прогрес для "Унік"
            progress_callback(current_progress) 
            
            active_effects_tags.append("uniek") # Додаємо тег "uniek" до назви
            status_callback("Комплекс 'Унік' фільтрів застосовано.")
        
        # --- Формування назви файлу ---
        base_name_original, ext = os.path.splitext(os.path.basename(input_path))
        output_parts = [base_name_original]
        
        if active_effects_tags: # Якщо є хоч якісь теги ефектів
            output_parts.append("-".join(active_effects_tags))
        
        size_tag = "originalSize" # За замовчуванням, якщо розмір не змінився або не відомий
        if hasattr(processed_clip, 'size') and processed_clip.size:
            final_width, final_height = processed_clip.size
            size_tag = f"{final_width}x{final_height}"
            # Якщо зміна розміру була активна, але фінальний розмір не відповідає бажаному,
            # це може бути через expand=True при повороті. Додамо позначку.
            if options.get("resize_active"):
                 if str(final_width) != options.get("width","") or str(final_height) != options.get("height",""):
                     if not any(tag.startswith("rot") for tag in active_effects_tags): # Не додаємо, якщо це через поворот
                        pass # Можна додати позначку, що розмір змінився не точно
            elif original_clip_for_info.size[0] == final_width and original_clip_for_info.size[1] == final_height :
                 pass # Розмір не змінився відносно оригіналу, тег size_tag вже коректний
        
        output_parts.append(size_tag)
            
        output_file_name_base = "_".join(output_parts)
        # Прибираємо подвійні підкреслення, якщо вони утворилися
        output_file_name_base = output_file_name_base.replace("__", "_")
        if output_file_name_base.endswith("_"): output_file_name_base = output_file_name_base[:-1]
        if output_file_name_base.startswith("_"): output_file_name_base = output_file_name_base[1:]


        output_file_name = f"{output_file_name_base}{ext}"
        output_path = os.path.join(output_folder, output_file_name)

        status_callback(f"Збереження відео в: {output_path}")
        progress_callback(0.9) 

        if check_if_cancelled_callback(): raise ProcessingCancelledError("Скасовано перед збереженням файлу.")

        processed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=4, logger=None)

        if check_if_cancelled_callback(): 
            raise ProcessingCancelledError("Скасовано після запису файлу.")

        progress_callback(1.0) 
        status_callback(f"Відео успішно збережено: {output_path}")
        return output_path 

    except ProcessingCancelledError as e: 
        status_callback(str(e) if str(e) else "Обробку скасовано.")
        return None
    except Exception as e:
        status_callback(f"Загальна помилка обробки відео в `process_video_task`: {type(e).__name__} - {str(e)}")
        import traceback
        traceback.print_exc()
        return None 
    finally:
        if 'original_clip_for_info' in locals() and original_clip_for_info: # original_clip_for_info це той самий clip
             try: original_clip_for_info.close() 
             except Exception: pass
        # processed_clip може бути тим самим об'єктом, що й clip, або новим.
        # Якщо це той самий, він вже закритий. Якщо новий, його треба закрити.
        # MoviePy часто повертає нові об'єкти кліпів після застосування fx.
        if 'processed_clip' in locals() and processed_clip and \
           ('original_clip_for_info' not in locals() or processed_clip != original_clip_for_info) and \
           hasattr(processed_clip, 'close'):
            try: processed_clip.close()
            except Exception: pass