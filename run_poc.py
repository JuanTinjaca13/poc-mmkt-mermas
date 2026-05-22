"""
Script rápido para ejecutar el POC sobre los videos de prueba.
Uso: python run_poc.py
"""
import sys
from pathlib import Path

# Agregar el directorio del POC al path
sys.path.insert(0, str(Path(__file__).parent))

from poc.video_analyzer import VideoAnalyzer


def main():
    analyzer = VideoAnalyzer()

    # Video 1 - video individual
    video1 = Path("../Video 1/20260120_133819_tp00053.mp4")
    if video1.exists():
        print("\n" + "=" * 60)
        print("  FASE 1: Análisis de Video Individual")
        print("=" * 60)
        result = analyzer.analyze_video(str(video1), save_annotated=True)
        print(f"\n  Resultado: {result}")

    # Video 2 - carpeta completa
    video2_dir = Path("../Video 2")
    if video2_dir.exists():
        print("\n" + "=" * 60)
        print("  FASE 2: Análisis de Carpeta Completa")
        print("=" * 60)
        results = analyzer.analyze_folder(str(video2_dir))

        # Resumen consolidado
        print("\n" + "=" * 60)
        print("  RESUMEN CONSOLIDADO")
        print("=" * 60)
        for r in results:
            if "error" not in r:
                print(f"  📹 {r['video']}: {r['total_events']} eventos "
                      f"(🔴{r['events_alta']} 🟡{r['events_media']} 🔵{r['events_baja']})")


if __name__ == "__main__":
    main()
