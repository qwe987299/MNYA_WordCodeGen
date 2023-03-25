pyinstaller --onefile --icon=icon.ico --noconsole MNYA_WordCodeGen.py
del MNYA_WordCodeGen.spec
del MNYA_WordCodeGen.exe
copy dist\MNYA_WordCodeGen.exe .\
rd /s /q dist
rd /s /q build
exit