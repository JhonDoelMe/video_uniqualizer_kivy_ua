# Файл конфігурації PyInstaller для Desktop збірок.
# Назвіть цей файл відповідно до назви вашого додатку, наприклад, video_editor_kivy_ua.spec
#
# # -*- mode: python ; coding: utf-8 -*-

from kivy_deps import hookspath, runtime_hooks 

block_cipher = None

a = Analysis(['main.py'], 
             pathex=['.'], 
             binaries=[
                 # ('ffmpeg_binaries/ffmpeg.exe', 'ffmpeg_binaries'), 
                 # ('ffmpeg_binaries/ffprobe.exe', 'ffmpeg_binaries')
             ],
             datas=[
                 ('assets', 'assets'), 
                 ('ui', 'ui') 
             ],
             hiddenimports=[],
             hookspath=hookspath(), 
             runtime_hooks=runtime_hooks(), 
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='VideoEditorKivyUA', 
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True, 
          console=False, 
          # icon='assets/app_icon.ico' # Для Windows потрібна .ico іконка
          )

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='VideoEditorKivyUA_App')
