"""
Configuración centralizada del POC.
Parámetros ajustados para cámaras TP-Link Tapo C200 (1080p @ 15fps, H.264).
"""
from pathlib import Path

# ── Rutas ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = OUTPUT_DIR / "reports"
CLIPS_DIR = OUTPUT_DIR / "clips"
CAPTURES_DIR = OUTPUT_DIR / "captures"
DATA_DIR = OUTPUT_DIR / "data"

# Crear directorios de salida
for d in [REPORTS_DIR, CLIPS_DIR, CAPTURES_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Modelo YOLOv8 ─────────────────────────────────────────────────────
YOLO_MODEL = "yolov8n.pt"          # nano para POC rápido (se puede escalar a yolov8m/l)
YOLO_POSE_MODEL = "yolov8n-pose.pt"  # pose estimation para análisis de comportamiento
CONFIDENCE_THRESHOLD = 0.45         # umbral de confianza detección
IOU_THRESHOLD = 0.5                 # umbral NMS

# Clases COCO relevantes para MicroMarket
CLASSES_OF_INTEREST = {
    0: "persona",
    39: "botella",
    41: "taza",
    42: "tenedor",
    43: "cuchillo",
    44: "cuchara",
    46: "banana",
    47: "manzana",
    49: "naranja",
    67: "celular",
    73: "libro",
    24: "mochila",
    25: "paraguas",
    26: "bolso",
    28: "maleta",
}

# ── Análisis de Video ─────────────────────────────────────────────────
# Tapo C200: 1080p @ 15fps, H.264
EXPECTED_FPS = 15
FRAME_SKIP = 3                      # procesar 1 de cada N frames (5 fps efectivos)
MAX_VIDEO_DURATION_MINUTES = 15      # duración máxima a procesar por video (ajustar para producción)

# ── Detección de Eventos Sospechosos ──────────────────────────────────
# Zona de interés: área de estanterías/góndolas (se ajusta por MMKT)
# Formato: (x_min_pct, y_min_pct, x_max_pct, y_max_pct) como % del frame
DEFAULT_SHELF_ZONE = (0.1, 0.2, 0.9, 0.8)

# Umbrales de comportamiento sospechoso
LOITERING_TIME_SECONDS = 15         # merodeo: persona en zona > N segundos sin transacción
RAPID_GRAB_FRAMES = 8              # movimiento rápido de mano hacia estantería
CONCEALMENT_ANGLE_THRESHOLD = 45   # ángulo de brazo que sugiere ocultamiento
PERSON_REAPPEAR_THRESHOLD = 0.7    # similitud para re-identificación básica

# ── Generación de Clips ───────────────────────────────────────────────
CLIP_PADDING_SECONDS = 5           # segundos antes/después del evento para el clip
CLIP_MAX_DURATION_SECONDS = 30     # duración máxima de un clip de evento

# ── Informe ───────────────────────────────────────────────────────────
REPORT_TITLE_PREFIX = "INFORME MMKT"
SEVERITY_LEVELS = {
    "alta": "Evento con alta probabilidad de merma/hurto",
    "media": "Comportamiento sospechoso que requiere revisión",
    "baja": "Anomalía detectada, posible falso positivo",
}
