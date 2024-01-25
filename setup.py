from cx_Freeze import setup, Executable

setup(
    name="SASYR",
    version="1.0",
    description="Prototipo de SASYR",
    executables=[Executable("main.py")]
)
