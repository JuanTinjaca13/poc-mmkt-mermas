"""
Dashboard Streamlit para visualización de análisis de mermas MMKT.
Permite cargar videos, ejecutar análisis y revisar informes.

Ejecutar: streamlit run poc/app.py
"""
import streamlit as st
import json
import cv2
import tempfile
import numpy as np
from pathlib import Path
from datetime import datetime

from config import OUTPUT_DIR, DATA_DIR, REPORTS_DIR, CAPTURES_DIR, CLIPS_DIR


st.set_page_config(
    page_title="POC Mermas MMKT - Novaventa",
    page_icon="🛒",
    layout="wide",
)

# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style="background: linear-gradient(135deg, #1a5e1f, #2ecc71); padding: 20px;
            border-radius: 10px; margin-bottom: 20px;">
    <h1 style="color: white; margin: 0;">🛒 POC Análisis de Mermas - MicroMarkets</h1>
    <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0;">
        Novaventa / Servicios Nutresa — Fase 1: Análisis Visual con IA
    </p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Configuración")

analysis_mode = st.sidebar.radio(
    "Modo de análisis",
    ["📂 Revisar informes existentes", "🎬 Analizar nuevo video"],
)

# ── Modo: Revisar informes ────────────────────────────────────────────
if analysis_mode == "📂 Revisar informes existentes":
    st.header("📊 Informes Generados")

    # Buscar JSONs de eventos
    json_files = sorted(DATA_DIR.glob("eventos_*.json")) if DATA_DIR.exists() else []

    if not json_files:
        st.info("No hay informes generados aún. Ejecuta el análisis primero:")
        st.code('python -m poc.video_analyzer --video "../Video 1/20260120_133819_tp00053.mp4"')
    else:
        selected_file = st.selectbox(
            "Seleccionar informe",
            json_files,
            format_func=lambda x: x.stem.replace("eventos_", ""),
        )

        if selected_file:
            data = json.loads(selected_file.read_text(encoding="utf-8"))

            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            summary = data.get("summary", {})
            col1.metric("Total Eventos", summary.get("total_events", 0))
            col2.metric("🔴 Alta", summary.get("alta", 0))
            col3.metric("🟡 Media", summary.get("media", 0))
            col4.metric("🔵 Baja", summary.get("baja", 0))

            st.divider()

            # Metadata
            with st.expander("📋 Metadata del Video"):
                meta = data.get("metadata", {})
                mcol1, mcol2 = st.columns(2)
                mcol1.write(f"**Archivo:** {meta.get('filename', 'N/A')}")
                mcol1.write(f"**MicroMarket:** {data.get('mmkt', 'N/A')}")
                mcol2.write(f"**Resolución:** {meta.get('width', '?')}x{meta.get('height', '?')}")
                mcol2.write(f"**FPS:** {meta.get('fps', '?')}")

            # Tabla de eventos
            st.subheader("🚨 Eventos Detectados")
            events = data.get("events", [])
            if events:
                for i, evt in enumerate(events, 1):
                    severity_color = {"alta": "🔴", "media": "🟡", "baja": "🔵"}.get(evt["severity"], "⚪")
                    with st.expander(
                        f"{severity_color} #{i} — {evt['type'].replace('_', ' ').title()} "
                        f"| Persona #{evt['person_id']} | {evt['start_time']:.1f}s"
                    ):
                        st.write(f"**Descripción:** {evt['description']}")
                        st.write(f"**Confianza:** {evt['confidence']:.0%}")
                        st.write(f"**Tiempo:** {evt['start_time']:.1f}s - {evt['end_time']:.1f}s")

                        # Buscar captura asociada
                        video_stem = data.get("video", "")
                        captures = list(CAPTURES_DIR.glob(
                            f"evt_{evt['type']}_{evt['person_id']}_{video_stem}*.jpg"
                        ))
                        if captures:
                            st.image(str(captures[0]), caption="Captura del evento", width=480)

                        # Buscar clip asociado
                        clips = list(CLIPS_DIR.glob(
                            f"clip_{evt['type']}_{evt['person_id']}_{video_stem}*.mp4"
                        ))
                        if clips:
                            st.video(str(clips[0]))
            else:
                st.success("No se detectaron eventos sospechosos en este video.")

            # Link al informe HTML
            html_reports = list(REPORTS_DIR.glob(f"*{data.get('mmkt', '')}*.html"))
            if html_reports:
                st.divider()
                st.write(f"📄 **Informe HTML completo:** `{html_reports[-1]}`")

# ── Modo: Analizar nuevo video ────────────────────────────────────────
elif analysis_mode == "🎬 Analizar nuevo video":
    st.header("🎬 Analizar Video")

    st.info(
        "Para analizar un video, ejecuta desde la terminal:\n\n"
        '```bash\n'
        'python -m poc.video_analyzer --video "../Video 1/20260120_133819_tp00053.mp4"\n'
        '```\n\n'
        "O para analizar todos los videos de una carpeta:\n\n"
        '```bash\n'
        'python -m poc.video_analyzer --folder "../Video 2/"\n'
        '```'
    )

    st.subheader("Videos disponibles")

    # Listar videos disponibles
    video_dirs = [
        Path("../Video 1"),
        Path("../Video 2"),
    ]

    for vdir in video_dirs:
        if vdir.exists():
            videos = list(vdir.glob("*.mp4"))
            if videos:
                st.write(f"**📁 {vdir.name}/** ({len(videos)} videos)")
                for v in videos:
                    size_mb = v.stat().st_size / (1024 * 1024)
                    st.write(f"  - `{v.name}` ({size_mb:.1f} MB)")

# ── Footer ────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "POC Análisis de Mermas MicroMarkets — Servicios Nutresa / Novaventa | "
    f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
)
