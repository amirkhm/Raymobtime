import os
import shutil
import zipfile
import time
from math import ceil
import subprocess

def base_run_dir_fn(i):
    """Retorna o nome do diretório para a run 'i' (ex: 'run00001')"""
    return "run{:05d}".format(i)

def setup_directories(frame_dir, output_dir):
    """Limpa e (re)cria diretórios temporários e de saída."""
    if os.path.exists(frame_dir):
        shutil.rmtree(frame_dir)
    os.makedirs(frame_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

def chooseAngleToRotate(previousAngle, nextAngle):
    """Escolhe o menor caminho de rotação (horário ou anti-horário)."""
    cw = nextAngle - previousAngle 
    ccw = - cw 
    cw360 = convert360(cw)
    ccw360 = convert360(ccw)
    if ( cw360 < ccw360 ) :
        return previousAngle + cw360
    else:
        return previousAngle - ccw360
    
def convert360(x):
    """Converte um ângulo para o intervalo [0, 360)."""
    if ( x < 0 ) :
        n = ceil(-x / 360)
        x = x + n*360
    return x % 360

def do_zip(pathdir):
    """Compacta e remove o diretório especificado."""
    if not os.path.exists(pathdir):
        print(f"[Aviso] {pathdir} não existe, impossível compactar.")
        return

    zip_path = pathdir + ".zip"
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(pathdir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Caminho relativo dentro do zip
                    arcname = os.path.relpath(file_path, start=pathdir) 
                    zipf.write(file_path, arcname)
        print(f"Compactado: {zip_path}")
        
        # Aguarda um momento para garantir que o arquivo zip foi fechado
        time.sleep(1) 
        shutil.rmtree(pathdir)
    except Exception as e:
        print(f"Erro ao compactar ou remover {pathdir}: {e}")

#add JK
def add_overlay_to_frame(frame_path, texto):
    if not os.path.exists(frame_path):
        return

    # Monta o texto que aparecerá na imagem
    #texto = "Dataset: {} | Ep: {} | Scene: {}".format(ds_name, episode, scene)
    
    # Comando para o ImageMagick criar a tarja preta com texto no topo
    comando = [
        "convert",
        frame_path,
        "-background", "black",
        "-fill", "white",
        "-font", "DejaVu-Sans",
        "-pointsize", "20",
        "-gravity", "center",
        "label:{}".format(texto),
        "+swap",
        "-append",
        frame_path
    ]
    
    try:
        subprocess.run(comando, check=True)
    except Exception as e:
        print("Erro ao aplicar legenda: {}".format(e))

#add JK
def add_rx_label(image_path, text, x, y):
    # Desenha o rótulo do RX no pixel via ImageMagick
    
    command = [
        'convert', image_path,
        '-fill', '#FFFF00',           # Amarelo
        '-font', 'DejaVu-Sans-Bold',   # Fonte em negrito
        '-pointsize', '16',
        '-stroke', 'black',            # Contorno preto
        '-strokewidth', '1',
        '-draw', "text {},{} '{}'".format(x, y, text),
        image_path
    ]
    subprocess.run(command)