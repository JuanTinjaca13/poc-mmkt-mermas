"""
Generador de informes de mermas estilo MMKT.
Produce informes HTML con capturas de imagen, descripción paso a paso
y consolidación de clips de video por evento.
"""
import json
import cv2
from pathlib import Path
from datetime import datetime
from typing import Optional

from .action_classifier import SuspiciousEvent
from .config import (
    REPORTS_DIR,
    CAPTURES_DIR,
    CLIPS_DIR,
    DATA_DIR,
    REPORT_TITLE_PREFIX,
    SEVERITY_LEVELS,
    CLIP_PADDING_SECONDS,
    CLIP_MAX_DURATION_SECONDS,
    EXPECTED_FPS,
)


class ReportGenerator:
    """Genera informes de mermas en formato HTML con capturas y clips."""

    def __init__(self, video_path: str, mmkt_name: str = ""):
        self.video_path = Path(video_path)
        self.video_name = self.video_path.stem
        self.mmkt_name = mmkt_name or self._extract_mmkt_name()
        self.captures_saved: list[dict] = []

    def _extract_mmkt_name(self) -> str:
        """Extrae nombre del MMKT del nombre del archivo de video."""
        # Formato: YYYYMMDD_HHMMSS_tpXXXXX.mp4
        parts = self.video_name.split("_")
        if len(parts) >= 3:
            return f"TP-{parts[2].replace('tp', '').upper()}"
        return self.video_name

    def save_event_capture(
        self,
        frame: "np.ndarray",
        event: SuspiciousEvent,
        frame_idx: int,
    ) -> str:
        """Guarda captura de frame para un evento y retorna la ruta."""
        filename = f"evt_{event.event_type}_{event.person_id}_{self.video_name}_f{frame_idx}.jpg"
        filepath = CAPTURES_DIR / filename
        cv2.imwrite(str(filepath), frame)
        self.captures_saved.append({
            "event_type": event.event_type,
            "person_id": event.person_id,
            "frame_idx": frame_idx,
            "filepath": str(filepath),
            "filename": filename,
        })
        return str(filepath)

    def extract_event_clip(
        self,
        event: SuspiciousEvent,
    ) -> Optional[str]:
        """Extrae un clip de video del evento con padding."""
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            return None

        fps = cap.get(cv2.CAP_PROP_FPS) or EXPECTED_FPS
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        start_sec = max(0, event.start_time_sec - CLIP_PADDING_SECONDS)
        end_sec = min(
            total_frames / fps,
            event.end_time_sec + CLIP_PADDING_SECONDS,
        )
        # Limitar duración
        if end_sec - start_sec > CLIP_MAX_DURATION_SECONDS:
            end_sec = start_sec + CLIP_MAX_DURATION_SECONDS

        start_frame = int(start_sec * fps)
        end_frame = int(end_sec * fps)

        filename = f"clip_{event.event_type}_{event.person_id}_{self.video_name}.mp4"
        filepath = CLIPS_DIR / filename

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(filepath), fourcc, fps, (width, height))

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        for _ in range(end_frame - start_frame):
            ret, frame = cap.read()
            if not ret:
                break
            writer.write(frame)

        writer.release()
        cap.release()
        return str(filepath)

    def generate_html_report(
        self,
        events: list[SuspiciousEvent],
        video_metadata: dict,
    ) -> str:
        """Genera informe HTML completo estilo MMKT."""
        now = datetime.now()
        report_filename = f"{REPORT_TITLE_PREFIX}_{self.mmkt_name}_{now.strftime('%Y%m%d_%H%M%S')}.html"
        report_path = REPORTS_DIR / report_filename

        # Agrupar eventos por severidad
        events_alta = [e for e in events if e.severity == "alta"]
        events_media = [e for e in events if e.severity == "media"]
        events_baja = [e for e in events if e.severity == "baja"]

        # Generar HTML
        html = self._build_html(
            events=events,
            events_alta=events_alta,
            events_media=events_media,
            events_baja=events_baja,
            video_metadata=video_metadata,
            report_date=now,
        )

        report_path.write_text(html, encoding="utf-8")

        # Guardar datos JSON
        self._save_events_json(events, video_metadata)

        print(f"[Informe] Generado: {report_path}")
        return str(report_path)

    def _save_events_json(self, events: list[SuspiciousEvent], video_metadata: dict):
        """Guarda eventos en formato JSON para analítica posterior."""
        data = {
            "video": self.video_name,
            "mmkt": self.mmkt_name,
            "metadata": video_metadata,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_events": len(events),
                "alta": len([e for e in events if e.severity == "alta"]),
                "media": len([e for e in events if e.severity == "media"]),
                "baja": len([e for e in events if e.severity == "baja"]),
            },
            "events": [
                {
                    "type": e.event_type,
                    "severity": e.severity,
                    "description": e.description,
                    "start_time": e.start_time_sec,
                    "end_time": e.end_time_sec,
                    "person_id": e.person_id,
                    "confidence": e.confidence,
                }
                for e in events
            ],
        }
        json_path = DATA_DIR / f"eventos_{self.video_name}.json"
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _build_html(self, events, events_alta, events_media, events_baja, video_metadata, report_date) -> str:
        """Construye el HTML del informe."""

        def _time_fmt(seconds: float) -> str:
            m, s = divmod(int(seconds), 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        def _event_rows(event_list: list[SuspiciousEvent]) -> str:
            rows = ""
            for i, e in enumerate(event_list, 1):
                # Buscar captura asociada
                capture = next(
                    (c for c in self.captures_saved
                     if c["event_type"] == e.event_type and c["person_id"] == e.person_id),
                    None,
                )
                img_tag = ""
                if capture:
                    img_tag = f'<img src="../captures/{capture["filename"]}" style="max-width:320px;border-radius:4px;">'

                severity_color = {"alta": "#e74c3c", "media": "#f39c12", "baja": "#3498db"}[e.severity]

                rows += f"""
                <tr>
                    <td>{i}</td>
                    <td><span style="background:{severity_color};color:#fff;padding:2px 8px;border-radius:3px;">
                        {e.severity.upper()}</span></td>
                    <td>{e.event_type.replace('_', ' ').title()}</td>
                    <td>{_time_fmt(e.start_time_sec)} - {_time_fmt(e.end_time_sec)}</td>
                    <td>Persona #{e.person_id}</td>
                    <td>{e.confidence:.0%}</td>
                    <td>{e.description}</td>
                    <td>{img_tag}</td>
                </tr>"""
            return rows

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{REPORT_TITLE_PREFIX} - {self.mmkt_name}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; color: #333; }}
        .header {{ background: linear-gradient(135deg, #1a5e1f, #2ecc71); color: white; padding: 30px;
                   border-radius: 8px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header p {{ margin: 5px 0 0; opacity: 0.9; }}
        .summary {{ display: flex; gap: 15px; margin-bottom: 20px; }}
        .summary-card {{ flex: 1; background: white; padding: 20px; border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
        .summary-card .number {{ font-size: 36px; font-weight: bold; }}
        .summary-card.alta .number {{ color: #e74c3c; }}
        .summary-card.media .number {{ color: #f39c12; }}
        .summary-card.baja .number {{ color: #3498db; }}
        .section {{ background: white; padding: 20px; border-radius: 8px;
                   box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .section h2 {{ color: #1a5e1f; border-bottom: 2px solid #2ecc71; padding-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        th {{ background: #1a5e1f; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; vertical-align: top; }}
        tr:hover {{ background: #f9f9f9; }}
        .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
        .meta-item {{ padding: 8px; background: #f9f9f9; border-radius: 4px; }}
        .meta-item strong {{ color: #1a5e1f; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛒 {REPORT_TITLE_PREFIX} - {self.mmkt_name}</h1>
        <p>Informe de Análisis de Mermas | Video: {self.video_name}</p>
        <p>Generado: {report_date.strftime('%d/%m/%Y %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <div class="summary-card">
            <div class="number">{len(events)}</div>
            <div>Total Eventos</div>
        </div>
        <div class="summary-card alta">
            <div class="number">{len(events_alta)}</div>
            <div>Severidad Alta</div>
        </div>
        <div class="summary-card media">
            <div class="number">{len(events_media)}</div>
            <div>Severidad Media</div>
        </div>
        <div class="summary-card baja">
            <div class="number">{len(events_baja)}</div>
            <div>Severidad Baja</div>
        </div>
    </div>

    <div class="section">
        <h2>📋 Metadata del Video</h2>
        <div class="meta-grid">
            <div class="meta-item"><strong>Archivo:</strong> {self.video_name}.mp4</div>
            <div class="meta-item"><strong>MicroMarket:</strong> {self.mmkt_name}</div>
            <div class="meta-item"><strong>Duración:</strong> {_time_fmt(video_metadata.get('duration_sec', 0))}</div>
            <div class="meta-item"><strong>Resolución:</strong> {video_metadata.get('width', '?')}x{video_metadata.get('height', '?')}</div>
            <div class="meta-item"><strong>FPS:</strong> {video_metadata.get('fps', '?')}</div>
            <div class="meta-item"><strong>Frames procesados:</strong> {video_metadata.get('frames_processed', '?')}</div>
        </div>
    </div>

    <div class="section">
        <h2>🚨 Eventos Detectados - Detalle Paso a Paso</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th><th>Severidad</th><th>Tipo</th><th>Tiempo</th>
                    <th>Persona</th><th>Confianza</th><th>Descripción</th><th>Captura</th>
                </tr>
            </thead>
            <tbody>
                {_event_rows(events)}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>📊 Resumen por Tipo de Evento</h2>
        <table>
            <thead><tr><th>Tipo</th><th>Cantidad</th><th>Descripción</th></tr></thead>
            <tbody>
                <tr><td>Merodeo</td><td>{len([e for e in events if e.event_type == 'merodeo'])}</td>
                    <td>Permanencia prolongada en zona de estanterías sin transacción</td></tr>
                <tr><td>Movimiento Rápido</td><td>{len([e for e in events if e.event_type == 'movimiento_rapido'])}</td>
                    <td>Agarre rápido de producto desde estantería</td></tr>
                <tr><td>Ocultamiento</td><td>{len([e for e in events if e.event_type == 'ocultamiento'])}</td>
                    <td>Postura de ocultamiento de producto en cuerpo</td></tr>
            </tbody>
        </table>
    </div>

    <div class="footer">
        <p>POC Análisis de Mermas MicroMarkets - Servicios Nutresa / Novaventa</p>
        <p>Generado automáticamente por sistema de visión computacional</p>
    </div>
</body>
</html>"""
