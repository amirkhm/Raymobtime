import os
import shutil
import zipfile
import time
from math import ceil

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