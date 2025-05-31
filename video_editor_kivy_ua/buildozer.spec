# Конфігураційний файл для Buildozer
[app]
title = Відео Редактор Kivy
package.name = videoeditorua
package.domain = org.example # Замініть на свій домен
source.dir = . 
source.include_exts = py,png,jpg,kv,atlas,ttf,json 

version = 0.1

requirements = python3,kivy,moviepy,opencv-python,numpy,plyer 
# Pillow часто потрібен як залежність для Kivy/OpenCV/MoviePy

orientation = portrait 

icon.filename = %(source.dir)s/assets/app_icon.png 
# presplash.filename = %(source.dir)s/assets/presplash.png

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET

# android.api = 33 
# android.minapi = 21 

android.archs = arm64-v8a, armeabi-v7a 

[buildozer]
log_level = 2 
warn_on_root = 1
