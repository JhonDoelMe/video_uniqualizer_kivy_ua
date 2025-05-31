# Допоміжні функції
import os
import sys
from pathlib import Path

def get_user_data_dir_ua(app_name):
    """ Отримує шлях до папки даних користувача для програми. """
    if sys.platform == "win32":
        path = Path(os.environ["APPDATA"]) / app_name
    elif sys.platform == "darwin": # macOS
        path = Path.home() / "Library" / "Application Support" / app_name
    else: # Linux та інші
        path = Path.home() / ".local" / "share" / app_name
    path.mkdir(parents=True, exist_ok=True)
    return str(path)

def get_ffmpeg_path_for_moviepy_ua():
    """
    Намагається знайти FFmpeg для MoviePy, особливо якщо він упакований з програмою (для desktop).
    Повертає шлях до ffmpeg.exe або просто 'ffmpeg', якщо передбачається, що він у PATH.
    Це більше актуально для PyInstaller збірок. Buildozer для Android обробляє це інакше.
    """
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
