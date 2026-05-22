"""
Pipeline principal de análisis de video para detección de mermas en MicroMarkets.
Orquesta: lectura de video → detección → análisis de comportamiento → informe.

Uso:
    python -m poc.video_analyzer --video "../Video 1/20260120_133819_tp00053.mp4"
    python -m poc.video_analyzer --folder "../Video 2/"
"""
import argparse
import cv2
import sys
import time
from pathlib import Path
from tqdm import tqdm

from .config import (
    FRAME_SKIP,
    MAX_VIDEO_DURATION_MINUTES,
    EXPECTED_FPS,
    CAPTURES_DIR,
)
from .detector import ObjectDetector, PoseEstimator, draw_detections
from .action_classifier import ActionClassifier, SuspiciousEvent
from .report_generator import ReportGenerator


class VideoAnalyzer:
    """Pipeline completo de análisis de video para mermas MMKT."""

    def __init__(self):
        self.detector = ObjectDetector()
        self.pose_estimator = PoseEstimator()

    def analyze_video(self, video_path: str, save_annotated: bool = False) -> dict:
        """
        Analiza un video completo y genera informe.

        Args:
            video_path: Ruta al archivo de video MP4
            save_annotated: Si True, guarda video anotado con detecciones

        Returns:
            dict con resumen del análisis
        """
        video_path = Path(video_path)
        if not video_path.exists():
            print(f"[Error] Video no encontrado: {video_path}")
            return {"error": "Video no encontrado"}

        print(f"\n{'='*60}")
        print(f"  Analizando: {video_path.name}")
        print(f"{'='*60}")

        # Abrir video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"[Error] No se pudo abrir el video: {video_path}")
            return {"error": "No se pudo abrir video"}

        # Metadata del video
        fps = cap.get(cv2.CAP_PROP_FPS) or EXPECTED_FPS
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_sec = total_frames / fps if fps > 0 else 0

        # Limitar duración
        max_frames = int(MAX_VIDEO_DURATION_MINUTES * 60 * fps)
        frames_to_process = min(total_frames, max_frames)

        video_metadata = {
            "filename": video_path.name,
            "fps": fps,
            "total_frames": total_frames,
            "width": width,
            "height": height,
            "duration_sec": duration_sec,
            "frames_processed": 0,
        }

        print(f"  Resolución: {width}x{height} | FPS: {fps:.1f} | Duración: {duration_sec:.0f}s")
        print(f"  Frames totales: {total_frames} | A procesar: {frames_to_process // FRAME_SKIP}")

        # Inicializar componentes
        classifier = ActionClassifier(frame_width=width, frame_height=height)
        report_gen = ReportGenerator(str(video_path))

        # Writer para video anotado (opcional)
        annotated_writer = None
        if save_annotated:
            out_path = CAPTURES_DIR / f"annotated_{video_path.stem}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            annotated_writer = cv2.VideoWriter(
                str(out_path), fourcc, fps / FRAME_SKIP, (width, height)
            )

        # ── Loop principal de análisis ────────────────────────────────
        all_events: list[SuspiciousEvent] = []
        frames_analyzed = 0
        start_time = time.time()

        pbar = tqdm(total=frames_to_process // FRAME_SKIP, desc="Analizando", unit="frames")

        frame_idx = 0
        while frame_idx < frames_to_process:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1

            # Skip frames para eficiencia
            if frame_idx % FRAME_SKIP != 0:
                continue

            timestamp_sec = frame_idx / fps
            frames_analyzed += 1

            # 1. Detección de objetos
            detections = self.detector.detect(frame, frame_idx, timestamp_sec)

            # 2. Estimación de pose (solo si hay personas)
            poses = []
            person_count = sum(1 for d in detections if d.class_id == 0)
            if person_count > 0:
                poses = self.pose_estimator.estimate(frame, frame_idx, timestamp_sec)

            # 3. Clasificación de acciones
            new_events = classifier.analyze_frame(detections, poses, frame_idx, timestamp_sec)

            # 4. Guardar capturas de eventos nuevos
            for event in new_events:
                annotated_frame = draw_detections(frame, detections, poses)
                report_gen.save_event_capture(annotated_frame, event, frame_idx)
                all_events.append(event)
                severity_icon = {"alta": "🔴", "media": "🟡", "baja": "🔵"}[event.severity]
                tqdm.write(
                    f"  {severity_icon} [{event.severity.upper()}] {event.event_type} "
                    f"@ {timestamp_sec:.1f}s - Persona #{event.person_id}"
                )

            # 5. Video anotado
            if annotated_writer:
                annotated_frame = draw_detections(frame, detections, poses)
                annotated_writer.write(annotated_frame)

            pbar.update(1)

        pbar.close()
        cap.release()
        if annotated_writer:
            annotated_writer.release()

        elapsed = time.time() - start_time
        video_metadata["frames_processed"] = frames_analyzed

        # ── Generar clips de eventos ──────────────────────────────────
        print(f"\n  Extrayendo clips de {len(all_events)} eventos...")
        for event in all_events:
            report_gen.extract_event_clip(event)

        # ── Generar informe HTML ──────────────────────────────────────
        report_path = report_gen.generate_html_report(all_events, video_metadata)

        # ── Resumen ───────────────────────────────────────────────────
        summary = {
            "video": video_path.name,
            "duration_sec": duration_sec,
            "frames_analyzed": frames_analyzed,
            "processing_time_sec": elapsed,
            "total_events": len(all_events),
            "events_alta": len([e for e in all_events if e.severity == "alta"]),
            "events_media": len([e for e in all_events if e.severity == "media"]),
            "events_baja": len([e for e in all_events if e.severity == "baja"]),
            "report_path": report_path,
        }

        print(f"\n  ✅ Análisis completado en {elapsed:.1f}s")
        print(f"  📊 Eventos: {summary['total_events']} "
              f"(🔴 {summary['events_alta']} | 🟡 {summary['events_media']} | 🔵 {summary['events_baja']})")
        print(f"  📄 Informe: {report_path}")

        return summary

    def analyze_folder(self, folder_path: str) -> list[dict]:
        """Analiza todos los videos MP4 en una carpeta."""
        folder = Path(folder_path)
        videos = sorted(folder.glob("*.mp4"))

        if not videos:
            print(f"[Error] No se encontraron videos MP4 en: {folder}")
            return []

        print(f"\n🎬 Encontrados {len(videos)} videos en {folder}")
        results = []
        for video in videos:
            result = self.analyze_video(str(video))
            results.append(result)

        # Resumen global
        total_events = sum(r.get("total_events", 0) for r in results)
        print(f"\n{'='*60}")
        print(f"  RESUMEN GLOBAL: {len(videos)} videos | {total_events} eventos totales")
        print(f"{'='*60}")

        return results


def main():
    parser = argparse.ArgumentParser(
        description="POC Análisis Visual de Mermas - MicroMarkets Novaventa"
    )
    parser.add_argument("--video", type=str, help="Ruta a un video MP4 individual")
    parser.add_argument("--folder", type=str, help="Ruta a carpeta con videos MP4")
    parser.add_argument("--annotated", action="store_true", help="Guardar video anotado")

    args = parser.parse_args()

    if not args.video and not args.folder:
        parser.print_help()
        sys.exit(1)

    analyzer = VideoAnalyzer()

    if args.video:
        analyzer.analyze_video(args.video, save_annotated=args.annotated)
    elif args.folder:
        analyzer.analyze_folder(args.folder)


if __name__ == "__main__":
    main()
