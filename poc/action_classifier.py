"""
Clasificador de acciones sospechosas basado en análisis de pose y tracking.
Detecta: merodeo, movimientos rápidos de mano, ocultamiento de productos,
y comportamientos erráticos en zona de estanterías.
"""
import math
import numpy as np
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional

from .detector import Detection, PoseDetection
from .config import (
    LOITERING_TIME_SECONDS,
    RAPID_GRAB_FRAMES,
    CONCEALMENT_ANGLE_THRESHOLD,
    DEFAULT_SHELF_ZONE,
    EXPECTED_FPS,
    FRAME_SKIP,
)


@dataclass
class SuspiciousEvent:
    """Evento sospechoso detectado."""
    event_type: str           # "merodeo", "movimiento_rapido", "ocultamiento", "sin_pago"
    severity: str             # "alta", "media", "baja"
    description: str          # descripción paso a paso
    start_frame: int
    end_frame: int
    start_time_sec: float
    end_time_sec: float
    person_id: int            # ID de tracking simple
    confidence: float         # confianza del evento
    keyframes: list = field(default_factory=list)  # frames clave para captura


class PersonTracker:
    """Tracker simple basado en IoU para asociar personas entre frames."""

    def __init__(self):
        self.next_id = 0
        self.active_tracks: dict[int, dict] = {}  # id -> {bbox, last_seen, first_seen}

    def update(self, detections: list[Detection], frame_idx: int, timestamp_sec: float) -> dict[int, Detection]:
        """Asocia detecciones de personas con tracks existentes."""
        person_dets = [d for d in detections if d.class_id == 0]

        if not person_dets and not self.active_tracks:
            return {}

        # Calcular IoU entre tracks activos y nuevas detecciones
        matched = {}
        unmatched_dets = list(range(len(person_dets)))

        if self.active_tracks and person_dets:
            track_ids = list(self.active_tracks.keys())
            iou_matrix = np.zeros((len(track_ids), len(person_dets)))

            for i, tid in enumerate(track_ids):
                for j, det in enumerate(person_dets):
                    iou_matrix[i, j] = self._iou(self.active_tracks[tid]["bbox"], det.bbox)

            # Greedy matching
            while iou_matrix.size > 0:
                max_idx = np.unravel_index(iou_matrix.argmax(), iou_matrix.shape)
                if iou_matrix[max_idx] < 0.2:
                    break
                tid = track_ids[max_idx[0]]
                det_idx = max_idx[1]
                matched[tid] = person_dets[det_idx]
                self.active_tracks[tid]["bbox"] = person_dets[det_idx].bbox
                self.active_tracks[tid]["last_seen"] = frame_idx
                if det_idx in unmatched_dets:
                    unmatched_dets.remove(det_idx)
                iou_matrix[max_idx[0], :] = -1
                iou_matrix[:, max_idx[1]] = -1

        # Crear nuevos tracks para detecciones no asociadas
        for det_idx in unmatched_dets:
            det = person_dets[det_idx]
            self.active_tracks[self.next_id] = {
                "bbox": det.bbox,
                "last_seen": frame_idx,
                "first_seen": frame_idx,
                "first_time": timestamp_sec,
            }
            matched[self.next_id] = det
            self.next_id += 1

        # Eliminar tracks perdidos (no vistos en 30 frames)
        lost_ids = [
            tid for tid, info in self.active_tracks.items()
            if frame_idx - info["last_seen"] > 30
        ]
        for tid in lost_ids:
            del self.active_tracks[tid]

        return matched

    @staticmethod
    def _iou(box1: tuple, box2: tuple) -> float:
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - inter
        return inter / union if union > 0 else 0


class ActionClassifier:
    """
    Clasifica acciones sospechosas analizando:
    1. Merodeo prolongado en zona de estanterías
    2. Movimientos rápidos de mano (posible agarre de producto)
    3. Ocultamiento de productos (ángulo de brazo hacia cuerpo/bolsillo)
    4. Persona que toma producto sin pasar por kiosco de pago
    """

    def __init__(self, frame_width: int = 1920, frame_height: int = 1080):
        self.tracker = PersonTracker()
        self.frame_width = frame_width
        self.frame_height = frame_height

        # Historial por persona
        self.person_history: dict[int, list] = defaultdict(list)
        self.wrist_history: dict[int, list] = defaultdict(list)
        self.events: list[SuspiciousEvent] = []

        # Zona de estanterías (en píxeles)
        sz = DEFAULT_SHELF_ZONE
        self.shelf_zone = (
            int(sz[0] * frame_width),
            int(sz[1] * frame_height),
            int(sz[2] * frame_width),
            int(sz[3] * frame_height),
        )

        # FPS efectivo considerando frame skip
        self.effective_fps = EXPECTED_FPS / FRAME_SKIP

    def analyze_frame(
        self,
        detections: list[Detection],
        poses: list[PoseDetection],
        frame_idx: int,
        timestamp_sec: float,
    ) -> list[SuspiciousEvent]:
        """Analiza un frame y retorna nuevos eventos sospechosos detectados."""
        new_events = []

        # Actualizar tracking
        tracked = self.tracker.update(detections, frame_idx, timestamp_sec)

        # Analizar cada persona trackeada
        for person_id, det in tracked.items():
            # Guardar historial de posición
            center = ((det.bbox[0] + det.bbox[2]) // 2, (det.bbox[1] + det.bbox[3]) // 2)
            self.person_history[person_id].append({
                "frame": frame_idx,
                "time": timestamp_sec,
                "center": center,
                "bbox": det.bbox,
            })

            # Buscar pose correspondiente a esta persona
            person_pose = self._match_pose_to_person(det, poses)

            if person_pose:
                # Guardar historial de muñecas
                self.wrist_history[person_id].append({
                    "frame": frame_idx,
                    "time": timestamp_sec,
                    "left_wrist": person_pose.left_wrist,
                    "right_wrist": person_pose.right_wrist,
                    "left_elbow": person_pose.left_elbow,
                    "right_elbow": person_pose.right_elbow,
                    "left_shoulder": person_pose.left_shoulder,
                    "right_shoulder": person_pose.right_shoulder,
                })

            # ── Check 1: Merodeo ──
            event = self._check_loitering(person_id, frame_idx, timestamp_sec)
            if event:
                new_events.append(event)

            # ── Check 2: Movimiento rápido de mano ──
            if person_pose:
                event = self._check_rapid_hand_movement(person_id, frame_idx, timestamp_sec)
                if event:
                    new_events.append(event)

            # ── Check 3: Ocultamiento ──
            if person_pose:
                event = self._check_concealment(person_id, person_pose, frame_idx, timestamp_sec)
                if event:
                    new_events.append(event)

        self.events.extend(new_events)
        return new_events

    def _is_in_shelf_zone(self, point: tuple) -> bool:
        """Verifica si un punto está dentro de la zona de estanterías."""
        return (self.shelf_zone[0] <= point[0] <= self.shelf_zone[2] and
                self.shelf_zone[1] <= point[1] <= self.shelf_zone[3])

    def _match_pose_to_person(self, det: Detection, poses: list[PoseDetection]) -> Optional[PoseDetection]:
        """Asocia una pose con una detección de persona por IoU de bbox."""
        best_iou = 0
        best_pose = None
        for pose in poses:
            iou = PersonTracker._iou(det.bbox, pose.bbox)
            if iou > best_iou:
                best_iou = iou
                best_pose = pose
        return best_pose if best_iou > 0.5 else None

    def _check_loitering(self, person_id: int, frame_idx: int, timestamp_sec: float) -> Optional[SuspiciousEvent]:
        """Detecta merodeo prolongado en zona de estanterías."""
        history = self.person_history[person_id]
        if len(history) < 2:
            return None

        # Tiempo en zona de estanterías
        time_in_zone = 0
        frames_in_zone = [h for h in history if self._is_in_shelf_zone(h["center"])]

        if len(frames_in_zone) < 2:
            return None

        duration = frames_in_zone[-1]["time"] - frames_in_zone[0]["time"]

        if duration >= LOITERING_TIME_SECONDS:
            # Verificar que no hayamos reportado esto ya para esta persona
            already_reported = any(
                e.person_id == person_id and e.event_type == "merodeo"
                and abs(e.end_time_sec - timestamp_sec) < LOITERING_TIME_SECONDS
                for e in self.events
            )
            if not already_reported:
                return SuspiciousEvent(
                    event_type="merodeo",
                    severity="media",
                    description=(
                        f"Persona #{person_id} permaneció {duration:.0f}s en zona de estanterías "
                        f"sin realizar transacción visible. "
                        f"Posición promedio: centro del área de góndolas."
                    ),
                    start_frame=frames_in_zone[0]["frame"],
                    end_frame=frame_idx,
                    start_time_sec=frames_in_zone[0]["time"],
                    end_time_sec=timestamp_sec,
                    person_id=person_id,
                    confidence=min(0.9, 0.5 + (duration / LOITERING_TIME_SECONDS) * 0.2),
                    keyframes=[frames_in_zone[0]["frame"], frame_idx],
                )
        return None

    def _check_rapid_hand_movement(self, person_id: int, frame_idx: int, timestamp_sec: float) -> Optional[SuspiciousEvent]:
        """Detecta movimientos rápidos de mano hacia estanterías."""
        wrist_hist = self.wrist_history[person_id]
        if len(wrist_hist) < RAPID_GRAB_FRAMES:
            return None

        recent = wrist_hist[-RAPID_GRAB_FRAMES:]

        for hand in ["right_wrist", "left_wrist"]:
            positions = [h[hand] for h in recent if h[hand] is not None]
            if len(positions) < RAPID_GRAB_FRAMES // 2:
                continue

            # Calcular velocidad de movimiento
            velocities = []
            for i in range(1, len(positions)):
                dx = positions[i][0] - positions[i - 1][0]
                dy = positions[i][1] - positions[i - 1][1]
                speed = math.sqrt(dx ** 2 + dy ** 2)
                velocities.append(speed)

            if not velocities:
                continue

            max_speed = max(velocities)
            avg_speed = sum(velocities) / len(velocities)

            # Movimiento rápido: velocidad pico > 3x promedio y > umbral absoluto
            if max_speed > 80 and max_speed > avg_speed * 2.5:
                already_reported = any(
                    e.person_id == person_id and e.event_type == "movimiento_rapido"
                    and abs(e.end_time_sec - timestamp_sec) < 3
                    for e in self.events
                )
                if not already_reported:
                    return SuspiciousEvent(
                        event_type="movimiento_rapido",
                        severity="alta",
                        description=(
                            f"Persona #{person_id} realizó un movimiento rápido de mano ({hand.replace('_', ' ')}) "
                            f"hacia la zona de estanterías. Velocidad pico: {max_speed:.0f}px/frame. "
                            f"Patrón consistente con agarre rápido de producto."
                        ),
                        start_frame=recent[0]["frame"],
                        end_frame=frame_idx,
                        start_time_sec=recent[0]["time"],
                        end_time_sec=timestamp_sec,
                        person_id=person_id,
                        confidence=min(0.85, 0.5 + (max_speed / 200) * 0.3),
                        keyframes=[frame_idx],
                    )
        return None

    def _check_concealment(
        self,
        person_id: int,
        pose: PoseDetection,
        frame_idx: int,
        timestamp_sec: float,
    ) -> Optional[SuspiciousEvent]:
        """Detecta posible ocultamiento de producto (brazo hacia cuerpo/bolsillo)."""
        for side, shoulder, elbow, wrist in [
            ("izquierdo", pose.left_shoulder, pose.left_elbow, pose.left_wrist),
            ("derecho", pose.right_shoulder, pose.right_elbow, pose.right_wrist),
        ]:
            if not all([shoulder, elbow, wrist]):
                continue

            # Calcular ángulo del brazo
            angle = self._angle_between(shoulder, elbow, wrist)

            # Ángulo cerrado + muñeca cerca del torso = posible ocultamiento
            if angle < CONCEALMENT_ANGLE_THRESHOLD:
                # Verificar que la muñeca está cerca del cuerpo (no extendida)
                bbox = pose.bbox
                body_center_x = (bbox[0] + bbox[2]) / 2
                body_width = bbox[2] - bbox[0]

                wrist_dist_from_center = abs(wrist[0] - body_center_x)

                if wrist_dist_from_center < body_width * 0.4:
                    already_reported = any(
                        e.person_id == person_id and e.event_type == "ocultamiento"
                        and abs(e.end_time_sec - timestamp_sec) < 5
                        for e in self.events
                    )
                    if not already_reported:
                        return SuspiciousEvent(
                            event_type="ocultamiento",
                            severity="alta",
                            description=(
                                f"Persona #{person_id} muestra postura de ocultamiento: "
                                f"brazo {side} con ángulo cerrado ({angle:.0f}°) y muñeca "
                                f"cerca del torso. Patrón consistente con guardar producto "
                                f"en bolsillo o bajo ropa."
                            ),
                            start_frame=frame_idx,
                            end_frame=frame_idx,
                            start_time_sec=timestamp_sec,
                            end_time_sec=timestamp_sec,
                            person_id=person_id,
                            confidence=0.65,
                            keyframes=[frame_idx],
                        )
        return None

    @staticmethod
    def _angle_between(p1: tuple, p2: tuple, p3: tuple) -> float:
        """Calcula el ángulo en p2 formado por p1-p2-p3."""
        v1 = (p1[0] - p2[0], p1[1] - p2[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        mag1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
        mag2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
        if mag1 * mag2 == 0:
            return 180.0
        cos_angle = max(-1, min(1, dot / (mag1 * mag2)))
        return math.degrees(math.acos(cos_angle))
