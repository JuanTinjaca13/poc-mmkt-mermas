@echo off
echo ============================================
echo  POC Mermas MMKT - Setup
echo ============================================
echo.

echo [1/3] Creando entorno virtual...
python -m venv .venv
call .venv\Scripts\activate.bat

echo [2/3] Instalando dependencias...
pip install -r requirements.txt

echo [3/3] Descargando modelos YOLOv8...
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt'); YOLO('yolov8n-pose.pt'); print('Modelos descargados OK')"

echo.
echo ============================================
echo  Setup completado!
echo.
echo  Para ejecutar el analisis:
echo    python run_poc.py
echo.
echo  Para el dashboard:
echo    streamlit run poc/app.py
echo ============================================
