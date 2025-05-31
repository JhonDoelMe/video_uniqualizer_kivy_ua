# utils.py
import os
import sys
from pathlib import Path

def get_user_data_dir_ua(app_name):
    """ Отримує шлях до папки даних користувача для програми. """
    if sys.platform == "win32":
        path = Path(os.environ["APPDATA"]) / app_name
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / app_name
    else:
        path = Path.home() / ".local" / "share" / app_name
    path.mkdir(parents=True, exist_ok=True)
    return str(path)

def get_ffmpeg_path_for_moviepy_ua():
    """
    Намагається знайти FFmpeg для MoviePy.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_dir = Path(sys._MEIPASS)
        potential_paths = [
            bundle_dir / 'ffmpeg.exe',
            bundle_dir / 'ffmpeg_binaries' / 'ffmpeg.exe',
        ]
        for path in potential_paths:
            if path.exists():
                return str(path.resolve())
    return 'ffmpeg'