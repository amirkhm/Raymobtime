import subprocess
import os

def create_video(frame_dir, video_path, video_config):
    """Gera o vídeo final usando FFmpeg a partir dos frames renderizados."""

    ffmpeg_cmd = [
        "ffmpeg",
        "-y", # Sobrescrever arquivo de saída
        "-framerate", str(video_config.get("framerate", 10)),
        "-i", os.path.join(frame_dir, "frame_%05d.png"),
        "-c:v", video_config.get("codec", "libx264"),
        "-pix_fmt", video_config.get("pixel_format", "yuv420p"),
        video_path
    ]

    try:
        subprocess.run(ffmpeg_cmd, 
               check=True, 
               stdout=subprocess.PIPE, 
               stderr=subprocess.PIPE, 
               universal_newlines=True)
        print(f"Vídeo final gerado em: {video_path}")
    except FileNotFoundError:
        print("ffmpeg não encontrado. Instale o ffmpeg e adicione-o ao PATH.")
    except subprocess.CalledProcessError as e:
        print("Falha ao gerar vídeo:")
        print(e.stderr)