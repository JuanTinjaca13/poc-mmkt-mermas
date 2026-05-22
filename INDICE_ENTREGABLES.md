# 📦 ÍNDICE DE ENTREGABLES — POC Mermas MMKT
## Propuesta Comercial | Valor Agregado

---

## Documentación

| # | Documento | Descripción |
|---|-----------|-------------|
| 1 | `PROPUESTA_VALOR_AGREGADO_POC.md` | Documento principal de valor agregado para la propuesta comercial |
| 2 | `FICHA_TECNICA_POC.md` | Ficha técnica detallada con resultados, arquitectura y configuración |
| 3 | `README.md` | Documentación técnica del proyecto (para equipo de desarrollo) |

---

## Código Fuente

| # | Archivo | Descripción |
|---|---------|-------------|
| 1 | `poc/config.py` | Configuración calibrada para cámaras Tapo C200 |
| 2 | `poc/detector.py` | Módulo de detección YOLOv8 + estimación de pose |
| 3 | `poc/action_classifier.py` | Clasificador de acciones sospechosas con tracking |
| 4 | `poc/report_generator.py` | Generador de informes HTML + clips + capturas |
| 5 | `poc/video_analyzer.py` | Pipeline principal de análisis |
| 6 | `poc/app.py` | Dashboard Streamlit para visualización |
| 7 | `run_poc.py` | Script de ejecución rápida |
| 8 | `requirements.txt` | Dependencias del proyecto |
| 9 | `setup.bat` | Script de instalación automática |

---

## Resultados del Análisis

| # | Archivo | Descripción |
|---|---------|-------------|
| 1 | `output/reports/INFORME MMKT_TP-00053_*.html` | **Informe visual completo** — Abrir en navegador |
| 2 | `output/captures/*.jpg` | **6 capturas** con detecciones anotadas |
| 3 | `output/clips/*.mp4` | **4 clips de video** de eventos detectados |
| 4 | `output/data/*.json` | **Datos estructurados** de eventos |

---

## Cómo Presentar al Cliente

### Opción A: Presentación ejecutiva
1. Abrir `PROPUESTA_VALOR_AGREGADO_POC.md` — resumen de alto nivel
2. Mostrar `output/reports/INFORME MMKT_TP-00053_*.html` en navegador — impacto visual
3. Reproducir clips de `output/clips/` — evidencia tangible

### Opción B: Demostración técnica
1. Ejecutar el análisis en vivo sobre un video
2. Mostrar el dashboard Streamlit
3. Revisar la ficha técnica para preguntas de detalle

### Opción C: Entrega documental
1. Incluir `PROPUESTA_VALOR_AGREGADO_POC.md` como anexo de la propuesta
2. Adjuntar el informe HTML como evidencia
3. Referenciar la ficha técnica para el equipo evaluador

---

## Estructura Completa del Proyecto

```
poc-mmkt-mermas/
│
├── 📄 INDICE_ENTREGABLES.md          ← Este archivo
├── 📄 PROPUESTA_VALOR_AGREGADO_POC.md ← Documento comercial principal
├── 📄 FICHA_TECNICA_POC.md           ← Detalle técnico completo
├── 📄 README.md                       ← Documentación de desarrollo
├── 📄 requirements.txt               ← Dependencias Python
├── 📄 setup.bat                       ← Instalación automática
├── 📄 run_poc.py                      ← Script de ejecución
│
├── 📁 poc/                            ← Código fuente
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py                      ← Configuración Tapo C200
│   ├── detector.py                    ← YOLOv8 + Pose
│   ├── action_classifier.py           ← Clasificador de acciones
│   ├── report_generator.py            ← Generador de informes
│   ├── video_analyzer.py              ← Pipeline principal
│   └── app.py                         ← Dashboard Streamlit
│
└── 📁 output/                         ← Resultados generados
    ├── 📁 reports/                    ← Informes HTML
    ├── 📁 captures/                   ← Capturas JPG con anotaciones
    ├── 📁 clips/                      ← Clips MP4 de eventos
    └── 📁 data/                       ← JSON estructurado
```

---

*Índice preparado para la propuesta comercial del RFP Novaventa — Mayo 2026*
