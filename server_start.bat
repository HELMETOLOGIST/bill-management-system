@echo off
REM Navigate to the Django project directory
cd /d D:\MSI\Brototype\BROTOTYPE\3-Bill-Management-System\bill-management-system

REM Activate the Python virtual environment
call env\Scripts\activate.bat

REM Run the Django development server
python manage.py runserver

REM Ensure the command window stays open in case of errors
pause