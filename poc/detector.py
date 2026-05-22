"""
Módulo de detección de personas y objetos usando YOLOv8.
Optimizado para escenarios de MicroMarket (cámaras Tapo C200, 1080p).
"""
import cv2
import numpy as np
from ultralytics import YOLO
from dataclasses import dataclass, field
from typing import Optional

from .config import (
    YOLO_MODEL,
    YOLO_POSE_MODEL,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    CLASSES_OF_INTEREST,
)


@dataclass
class Detection:
    """Representa una detección individual en un frame."""
    class_id: int
    class_name: str
    confidence: float
    bbox: tuple  # (x1, y1, x2, y2)
    frame_idx: int
    timestamp_sec: float


@dataclass
class PoseDetection:
    """Detección de persona con keypoints de pose."""
    bbox: tuple
    confidence: float
    keypoints: np.ndarray  # shape (17, 3) -> x, y, conf por keypoint
    frame_idx: int
    timestamp_sec: float

    # Índices de keypoints COCO relevantes
    # 5: hombro_izq, 6: hombro_der, 7: codo_izq, 8: codo_der
    # 9: muñeca_izq, 10: muñeca_der

    @property
    def left_wrist(self) -> Optional[tuple]:
        kp = self.keypoints[9]
        return (kp[0], kp[1]) if kp[2] > 0.3 else None

    @property
    def right_wrist(self) -> Optional[tuple]:
        kp = self.keypoints[10]
        return (kp[0], kp[1]) if kp[2] > 0.3 else None

    @property
    def left_elbow(self) -> Optional[tuple]:
        kp = self.keypoints[7]
        return (kp[0], kp[1]) if kp[2] > 0.3 else None

    @property
    def right_elbow(self) -> Optional[tuple]:
        kp = self.keypoints[8]
        return (kp[0], kp[1]) if kp[2] > 0.3 else None

    @property
    def left_shoulder(self) -> Optional[tuple]:
        kp = self.keypoints[5]
        return (kp[0], kp[1]) if kp[2] > 0.3 else None

    @property
    def right_shoulder(self) -> Optional[tuple]:
        kp = self.keypoints[6]
        return (kp[0], kp[1]) if kp[2] > 0.3 else None


class ObjectDetector:
    """Detector de objetos basado en YOLOv8 para escenarios MicroMarket."""

    def __init__(self, model_path: str = YOLO_MODEL):
        print(f"[Detector] Cargando modelo: {model_path}")
        self.model = YOLO(model_path)
        self.classes_of_interest = CLASSES_OF_INTEREST

    def detect(self, frame: np.ndarray, frame_idx: int, timestamp_sec: float) -> list[Detection]:
        """Ejecuta detección sobre un frame y retorna detecciones filtradas."""
        results = self.model(
            frame,
            conf=CONFIDENCE_THRESHOLD,
            iou=IOU_THRESHOLD,
            verbose=False,
        )

        detections = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id not in self.classes_of_interest:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                detections.append(Detection(
                    class_id=cls_id,
                    class_name=self.classes_of_interest[cls_id],
                    confidence=float(box.conf[0]),
                    bbox=(int(x1), int(y1), int(x2), int(y2)),
                    frame_idx=frame_idx,
                    timestamp_sec=timestamp_sec,
                ))

        return detections


class PoseEstimator:
    """Estimador de pose humana para análisis de comportamiento."""

    def __init__(self, model_path: str = YOLO_POSE_MODEL):
        print(f"[PoseEstimator] Cargando modelo: {model_path}")
        self.model = YOLO(model_path)

    def estimate(self, frame: np.ndarray, frame_idx: int, timestamp_sec: float) -> list[PoseDetection]:
        """Estima poses de todas las personas en el frame."""
        results = self.model(
            frame,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False,
        )

        poses = []
        for result in results:
            if result.keypoints is None or result.boxes is None:
                continue

            keypoints_data = result.keypoints.data.cpu().numpy()
            boxes_data = result.boxes

            for i in range(len(boxes_data)):
                x1, y1, x2, y2 = boxes_data.xyxy[i].cpu().numpy()
                conf = float(boxes_data.conf[i])

                if i < len(keypoints_data):
                    kps = keypoints_data[i]  # (17, 3)
                else:
                    continue

                poses.append(PoseDetection(
                    bbox=(int(x1), int(y1), int(x2), int(y2)),
                    confidence=conf,
                    keypoints=kps,
                    frame_idx=frame_idx,
                    timestamp_sec=timestamp_sec,
                ))

        return poses


def draw_detections(frame: np.ndarray, detections: list[Detection], poses: list[PoseDetection] = None) -> np.ndarray:
    """Dibuja detecciones y poses sobre el frame para visualización."""
    annotated = frame.copy()

    # Dibujar detecciones de objetos
    for det in detections:
        x1, y1, x2, y2 = det.bbox
        color = (0, 255, 0) if det.class_name == "persona" else (255, 165, 0)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        label = f"{det.class_name} {det.confidence:.2f}"
        cv2.putText(annotated, label, (x1, y1 - 10),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Dibujar esqueletos de pose
    if poses:
        skeleton_pairs = [
            (5, 7), (7, 9),    # brazo izquierdo
            (6, 8), (8, 10),   # brazo derecho
            (5, 6),            # hombros
            (5, 11), (6, 12),  # torso
            (11, 12),          # caderas
            (11, 13), (13, 15),  # pierna izquierda
            (12, 14), (14, 16),  # pierna derecha
        ]

        for pose in poses:
            kps = pose.keypoints
            for p1, p2 in skeleton_pairs:
                if kps[p1][2] > 0.3 and kps[p2][2] > 0.3:
                    pt1 = (int(kps[p1][0]), int(kps[p1][1]))
                    pt2 = (int(kps[p2][0]), int(kps[p2][1]))
                    cv2.line(annotated, pt1, pt2, (0, 255, 255), 2)

            # Puntos clave
            for kp in kps:
                if kp[2] > 0.3:
                    cv2.circle(annotated, (int(kp[0]), int(kp[1])), 4, (0, 0, 255), -1)

    return annotated
