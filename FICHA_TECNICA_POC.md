# 📋 FICHA TÉCNICA — POC Análisis Visual de Mermas
## MicroMarkets Novaventa | Servicios Nutresa

---

## Información General

| Campo | Valor |
|-------|-------|
| **Nombre del proyecto** | POC Análisis Visual de Mermas MMKT |
| **Cliente** | Servicios Nutresa S.A.S. / Novaventa S.A.S. |
| **Referencia RFP** | Solución para Análisis de Mermas Micromarkets Novaventa |
| **Fecha de desarrollo** | Mayo 2026 |
| **Estado** | ✅ Funcional — Resultados obtenidos |

---

## Datos de Entrada (proporcionados por el cliente)

### Videos de Prueba

| Carpeta | Archivo | Fecha grabación | Cámara |
|---------|---------|-----------------|--------|
| Video 1 | `20260120_133819_tp00053.mp4` | 20/01/2026 13:38 | TP-00053 |
| Video 2 | `20251126_091509_tp00042.mp4` | 26/11/2025 09:15 | TP-00042 |
| Video 2 | `20251128_172747_tp00412.mp4` | 28/11/2025 17:27 | TP-00412 |
| Video 2 | `20251203_040704_tp00111.mp4` | 03/12/2025 04:07 | TP-00111 |
| Video 2 | `20251203_103652_tp00422.mp4` | 03/12/2025 10:36 | TP-00422 |
| Video 2 | `20251206_130819_tp00389.mp4` | 06/12/2025 13:08 | TP-00389 |

### Informes de Referencia (formato actual manual)

- INFORME MMKT AGROFRUT
- INFORME MMKT CONCENTRIX PISO 15
- INFORME MMKT CONCENTRIX PISO 16
- INFORME MMKT CONCENTRIX PISO 16 - 2
- INFORME MMKT INTOUCH INSTANCIA 246
- INFORME MMKT INTOUCH INSTANCIA 58
- MMKT HACEB SERVICIOS GENERALES

---

## Especificaciones Técnicas de la Cámara (según RFP)

| Parámetro | Valor |
|-----------|-------|
| **Modelo** | TP-Link Tapo C200 |
| **Resolución** | Full HD 1080p (1920x1080) / 720p detectado en video |
| **FPS** | 15 fps |
| **Codec** | H.264 |
| **Sensor** | 1/2.8" — 2304 x 1296 a 15 fps |
| **Almacenamiento** | MicroSD 128 GB, borrado automático al llenado |
| **Características** | Detección de movimiento, audio bidireccional, visión nocturna |
| **Ángulo de visión** | Amplio (100°+) |

---

## Arquitectura del POC

### Componentes de Software

| Módulo | Archivo | Función |
|--------|---------|---------|
| Configuración | `poc/config.py` | Parámetros calibrados para Tapo C200 |
| Detector | `poc/detector.py` | YOLOv8 detección + YOLOv8-pose |
| Clasificador | `poc/action_classifier.py` | Análisis de comportamiento + tracking |
| Informes | `poc/report_generator.py` | HTML + clips + capturas + JSON |
| Pipeline | `poc/video_analyzer.py` | Orquestador principal |
| Dashboard | `poc/app.py` | Visualización Streamlit |

### Modelos de IA Utilizados

| Modelo | Versión | Tamaño | Uso |
|--------|---------|--------|-----|
| YOLOv8n | v8.4.0 | 6.2 MB | Detección de personas y objetos |
| YOLOv8n-pose | v8.4.0 | 6.5 MB | Estimación de pose (17 keypoints) |

### Dependencias Principales

| Librería | Versión | Propósito |
|----------|---------|-----------|
| ultralytics | 8.4.46 | Framework YOLOv8 |
| opencv-python | 4.13.0 | Procesamiento de video |
| torch | 2.11.0 | Backend de deep learning |
| numpy | 2.4.4 | Computación numérica |
| streamlit | 1.57.0 | Dashboard web |

---

## Resultados del Análisis

### Video Analizado: `20260120_133819_tp00053.mp4`

| Parámetro | Valor |
|-----------|-------|
| **Resolución detectada** | 1280x720 |
| **FPS** | 15.0 |
| **Duración total** | 39 minutos 19 segundos |
| **Frames totales** | 35,400 |
| **Frames procesados** | 9,000 (1 de cada 3) |
| **Tiempo de procesamiento** | ~10 minutos (CPU) |
| **Velocidad** | 10.5 frames/segundo |

### Eventos Detectados

**Total: 6 eventos | Severidad Alta: 6 | Media: 0 | Baja: 0**

#### Evento 1
- **Tipo:** Movimiento rápido de mano
- **Tiempo:** 00:12:50 - 00:12:51
- **Persona:** #0 (mano izquierda)
- **Velocidad:** 233 px/frame
- **Confianza:** 85%
- **Captura:** `evt_movimiento_rapido_0_20260120_133819_tp00053_f11574.jpg`

#### Evento 2
- **Tipo:** Movimiento rápido de mano
- **Tiempo:** 00:12:52 - 00:12:55
- **Persona:** #0 (mano derecha)
- **Velocidad:** 273 px/frame
- **Confianza:** 85%
- **Observación:** Misma persona que Evento 1, posible agarre con ambas manos

#### Evento 3
- **Tipo:** Movimiento rápido de mano
- **Tiempo:** 00:29:09 - 00:29:11
- **Persona:** #4 (mano derecha)
- **Velocidad:** 250 px/frame
- **Confianza:** 85%
- **Captura:** `evt_movimiento_rapido_4_20260120_133819_tp00053_f26268.jpg`

#### Evento 4
- **Tipo:** Movimiento rápido de mano
- **Tiempo:** 00:29:17 - 00:29:20
- **Persona:** #6 (mano derecha)
- **Velocidad:** 190 px/frame
- **Confianza:** 78%
- **Captura:** `evt_movimiento_rapido_6_20260120_133819_tp00053_f26409.jpg`

#### Evento 5
- **Tipo:** Movimiento rápido de mano
- **Tiempo:** 00:29:18 - 00:29:24
- **Persona:** #6 (mano derecha)
- **Velocidad:** 247 px/frame
- **Confianza:** 85%
- **Observación:** Reincidencia de Persona #6

#### Evento 6
- **Tipo:** Movimiento rápido de mano
- **Tiempo:** 00:29:26 - 00:29:31
- **Persona:** #7 (mano derecha)
- **Velocidad:** 115 px/frame
- **Confianza:** 67%
- **Captura:** `evt_movimiento_rapido_7_20260120_133819_tp00053_f26577.jpg`

### Patrones Identificados

1. **Cluster temporal:** 4 de 6 eventos ocurren entre 29:09 y 29:31 (ventana de 22 segundos)
2. **Reincidencia:** Persona #6 aparece en 2 eventos consecutivos
3. **Hora foco:** Dos picos de actividad — minuto 12 y minuto 29
4. **Lateralidad:** 5 de 6 eventos involucran la mano derecha

---

## Salidas Generadas

### Informe HTML
- **Archivo:** `INFORME MMKT_TP-00053_20260504_131541.html`
- **Contenido:** Resumen ejecutivo, tabla de eventos, capturas, metadata
- **Formato:** Responsive, colores corporativos Nutresa (verde)

### Capturas de Evidencia (6 imágenes)
- Frames anotados con bounding boxes y esqueletos de pose
- Resolución original del video (1280x720)
- Formato JPG

### Clips de Video (4 clips)
- Segmentos de video con padding de 5 segundos
- Formato MP4 (H.264)
- Duración máxima: 30 segundos por clip

### Datos Estructurados (JSON)
- Metadata del video
- Lista de eventos con timestamps, confianza, tipo
- Resumen por severidad
- Listo para integración con dashboards/APIs

---

## Parámetros de Configuración

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `CONFIDENCE_THRESHOLD` | 0.45 | Umbral mínimo de confianza para detección |
| `FRAME_SKIP` | 3 | Procesar 1 de cada 3 frames (5 fps efectivos) |
| `LOITERING_TIME_SECONDS` | 15 | Tiempo para considerar merodeo |
| `RAPID_GRAB_FRAMES` | 8 | Ventana de frames para movimiento rápido |
| `CONCEALMENT_ANGLE_THRESHOLD` | 45° | Ángulo de brazo para ocultamiento |
| `CLIP_PADDING_SECONDS` | 5 | Segundos de contexto en clips |
| `CLIP_MAX_DURATION_SECONDS` | 30 | Duración máxima de clip |

---

## Instrucciones de Ejecución

### Requisitos
- Python 3.11+
- 4 GB RAM mínimo
- Windows 10/11 (probado) o Linux

### Instalación
```bash
cd poc-mmkt-mermas
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Ejecución
```bash
# Analizar video individual
.venv\Scripts\python -m poc.video_analyzer --video "../Video 1/20260120_133819_tp00053.mp4"

# Analizar carpeta completa
.venv\Scripts\python -m poc.video_analyzer --folder "../Video 2/"

# Dashboard de visualización
.venv\Scripts\streamlit run poc/app.py
```

---

## Limitaciones del POC (transparencia)

| Limitación | Mitigación en Producción |
|-----------|--------------------------|
| Solo análisis offline | Fase 2 incluye streaming RTSP |
| Sin integración VEGA | API definida, pendiente credenciales |
| Modelo nano (ligero) | Escalar a YOLOv8m/l con GPU |
| Sin calibración por sede | Configuración de zonas por MMKT |
| Posibles falsos positivos | Fine-tuning con datos etiquetados |
| Sin reconocimiento facial | Motor de embeddings en Fase 3 |

---

*Ficha técnica del POC desarrollado para el RFP "Solución para Análisis de Mermas Micromarkets Novaventa"*
*Fecha: Mayo 2026*
