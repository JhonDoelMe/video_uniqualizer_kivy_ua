# Відео Редактор на Kivy (Українська версія)

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
