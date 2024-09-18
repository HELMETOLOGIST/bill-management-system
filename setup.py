import sys
from cx_Freeze import setup, Executable
from setuptools import find_packages

# Determine the base for Windows
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

executables = [
    Executable('manage.py', base=base, icon='icon.ico')
]

# Define the packages from your requirements.txt
options = {
    'build_exe': {
        'packages': [
            'django',
            'altgraph', 'arabic_reshaper', 'asgiref', 'asn1crypto',
            'backports.zoneinfo', 'certifi', 'cffi', 'chardet', 'charset_normalizer',
            'click', 'colorama', 'cryptography', 'cssselect2', 'cx_Freeze', 'cx_Logging',
            'gunicorn', 'html5lib', 'idna', 'importlib_metadata', 'lief', 'lxml',
            'oscrypto', 'packaging', 'pefile', 'pillow', 'pycparser', 'pyHanko',
            'pyhanko_certvalidator', 'pyinstaller', 'pyinstaller_hooks_contrib',
            'pypdf', 'pypng', 'PyQt5', 'PyQt5.Qt5', 'PyQt5_sip', 'PyQtWebEngine',
            'PyQtWebEngine.Qt5', 'python_bidi', 'pywin32_ctypes', 'PyYAML', 'qrcode',
            'reportlab', 'requests', 'sip', 'six', 'sqlparse', 'svglib', 'tinycss2',
            'tomli', 'typing_extensions', 'tzdata', 'tzlocal', 'uritools', 'urllib3',
            'webencodings', 'xhtml2pdf', 'xlwt'
        ],
        'include_files': [
            ('templates', 'templates'),
            ('staticfiles', 'staticfiles'),
            ('db.sqlite3', 'db.sqlite3'),
            ('back.png', 'back.png'),
            ('email.png', 'email.png'),
            ('forward.png', 'forward.png'),
            ('icon.ico', 'icon.ico'),
            ('main.js', 'main.js'),
            ('spinner.gif', 'spinner.gif')
        ],
        'excludes': ['node_modules']  # Exclude unwanted directories
    }
}

setup(
    name="best_buy",
    version="0.1",
    description="Django Desktop App",
    executables=executables,
    options=options,
    packages=find_packages(include=['bestbuy', 'bill_management'])  # Explicitly include your app and project
)
