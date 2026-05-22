# POC - Análisis Visual de Mermas MicroMarkets Novaventa

## Fase 1: Análisis Visual con IA

### Descripción
Prueba de concepto para la detección automatizada de eventos sospechosos (mermas/hurtos) 
en videos de cámaras TP-Link Tapo C200 instaladas en MicroMarkets, usando visión computacional 
y modelos de Deep Learning.

### Arquitectura POC

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Videos MP4     │────▶│  Pipeline de     │────▶│  Generador de       │
│  (Offline/      │     │  Análisis Visual │     │  Informes           │
│   MicroSD)      │     │  (YOLOv8 + Pose) │     │  (HTML/PDF + Clips) │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
                               │
                        ┌──────┴──────┐
                        │  Detección  │
                        │  - Personas │
                        │  - Objetos  │
                        │  - Poses    │
                        │  - Acciones │
                        └─────────────┘
```

### Componentes

1. **video_analyzer.py** - Pipeline principal de análisis de video
2. **detector.py** - Detección de personas y objetos con YOLOv8
3. **action_classifier.py** - Clasificación de acciones sospechosas (pose estimation)
4. **report_generator.py** - Generación de informes tipo MMKT con capturas y clips
5. **app.py** - Dashboard web (Streamlit) para visualización
6. **config.py** - Configuración centralizada

### Requisitos
```bash
pip install -r requirements.txt
```

### Uso Rápido
```bash
# Analizar un video individual
python -m poc.video_analyzer --video "../Video 1/20260120_133819_tp00053.mp4"

# Analizar carpeta completa de videos
python -m poc.video_analyzer --folder "../Video 2/"

# Lanzar dashboard
streamlit run poc/app.py
```

### Estructura de Salida
```
output/
├── reports/
│   ├── INFORME_MMKT_20260120_133819_tp00053.html
│   └── ...
├── clips/
│   ├── evento_001_20260120_133819.mp4
│   └── ...
├── captures/
│   ├── frame_001_20260120_133819.jpg
│   └── ...
└── data/
    └── eventos.json
```
