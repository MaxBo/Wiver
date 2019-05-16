xcopy /e /Y "%RECIPE_DIR%\.." "%SRC_DIR%"
"%PYTHON%" -m pip install --no-deps .
if errorlevel 1 exit 1