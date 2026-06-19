import subprocess
import os

def create_video(frame_dir, video_path, video_config):
    """Gera o vídeo final usando FFmpeg a partir dos frames renderizados."""

    ffmpeg_cmd = [
        "ffmpeg",
        "-y", # Sobrescrever arquivo de saída
        "-framerate", str(video_config.get("framerate", 10)),
        "-i", os.path.join(frame_dir, "frame_%05d.png"),
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",     # Se o tamanho for ímpar vai add 1 pixel para tornar par
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


def join_video_batches(video_list, output_filename):    # add JK
    """
    Une múltiplos arquivos .mp4 em um único vídeo final sem re-renderizar.
    
    Args:
        video_list (list): Lista de strings com os caminhos dos vídeos parciais.
        output_filename (str): Nome (ou caminho completo) do vídeo consolidado.
        
    Docstring JK: Esta função utiliza o FFmpeg Concat Demuxer para unir os 
    lotes de simulação gerados em paralelo ou em sequência.
    """
    if not video_list:
        print("⚠️ Lista de vídeos vazia. Nada para concatenar.")
        return

    # 1. Cria o arquivo de texto temporário exigido pelo FFmpeg
    list_file = "ffmpeg_input_list.txt"
    try:
        with open(list_file, "w") as f:
            for video_path in video_list:
                # O FFmpeg exige o formato: file 'caminho/do/arquivo'
                f.write(f"file '{os.path.abspath(video_path)}'\n")

        # 2. Comando FFmpeg para concatenar usando o codec 'copy'
        # -f concat: indica o uso do demuxer de concatenação
        # -safe 0: permite o uso de caminhos absolutos
        # -c copy: copia os fluxos de vídeo/áudio sem processar (muito rápido)
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_file, "-c", "copy", output_filename
        ]

        print(f"🔗 Concatenando {len(video_list)} lotes no arquivo final: {output_filename}")
        subprocess.run(cmd, check=True)
        print("✅ Vídeo final gerado com sucesso!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao concatenar vídeos com FFmpeg: {e}")
    finally:
        # 3. Limpeza do arquivo temporário de lista
        if os.path.exists(list_file):
            os.remove(list_file)