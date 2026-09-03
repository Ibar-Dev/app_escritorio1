# PyInstaller hook for pywin32: ensures win32 DLLs and COM modules are included.
hiddenimports = [
    "win32api",
    "win32com",
    "win32com.client",
    "win32con",
    "win32print",
    "pywintypes",
    "pythoncom",
]
