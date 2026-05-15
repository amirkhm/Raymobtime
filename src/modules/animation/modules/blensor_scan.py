import bpy
import raymobtime.src.modules.blensor as blensor
import os
from math import radians
from .helpers import do_zip 

def run_scan(vPosition, pathdir, zip_output):
    """Realiza varredura Blensor e compacta os resultados se zip_output=True."""
    
    os.makedirs(pathdir, exist_ok=True)
    
    # --- ADIÇÃO 1: Contador ---
    rx_found_count = 0 
    
    scanner = bpy.data.objects.get("Camera") # Assume que o scanner é a câmera
    if not scanner:
        print("❌ Erro de Varredura: Objeto 'Camera' não encontrado.")
        return

    for vid, vinfo in vPosition.items():
        if vinfo['isRx']:
            
            # --- ADIÇÃO 2: Incremento e Log ---
            rx_found_count += 1
            print(f"🔵 [Scan] Receptor encontrado: '{vid}'. Tentando escanear...")
            # ----------------------------------

            # Tenta encontrar o objeto receptor (carro, pedestre, etc.)
            car_to_hide = bpy.data.objects.get(vid)
            
            # Se não achar o 'vid' (ex: é um pedestre 'ped0'), 
            # tenta achar suas partes ('ped0_step1')
            if not car_to_hide:
                 # Procura por qualquer objeto que COMECE com o vid
                ped_parts = [obj for obj in bpy.data.objects if obj.name.startswith(vid)]
                if ped_parts:
                    car_to_hide = ped_parts[0] # Pega o primeiro que achar
                else:
                    print(f"⚠️ [Scan] Objeto '{vid}' ou suas partes não encontrados. Pulando varredura.")
                    continue
            
            # Oculta o próprio veículo/pedestre receptor
            car_to_hide.hide_render = True
            
            height = float(vinfo['height']) + 1 # Posição Z do scanner
            scanner.location.xyz = float(vinfo['xinsite']), float(vinfo['yinsite']), height
            scanner.rotation_euler = (radians(0), radians(0), radians(0))

            output_pcd = os.path.join(pathdir, f"{vid}.pcd")
            
            try:
                blensor.blendodyne.scan_advanced(
                    scanner,
                    rotation_speed=10.0,
                    simulation_fps=24,
                    angle_resolution=0.1728,
                    max_distance=120,
                    evd_file=output_pcd,
                    noise_mu=0.0,
                    noise_sigma=0.03,
                    start_angle=0.0,
                    end_angle=360.0,
                    evd_last_scan=True,
                    add_blender_mesh=False,
                    add_noisy_blender_mesh=False,
                    world_transformation=scanner.matrix_world,
                )
                print(f"Gerado: {output_pcd}")
            except Exception as e:
                print(f"❌ Erro durante a varredura Blensor: {e}")
            
            # Re-exibe o veículo/pedestre
            car_to_hide.hide_render = False

    # --- ADIÇÃO 3: Verificação Final ---
    if rx_found_count == 0:
        print("⚠️ [Scan] AVISO: Nenhuma varredura foi executada.")
        print("   Motivo: Nenhum veículo ou pedestre foi marcado como receptor (isRx=True) nos dados desta run.")
    # -----------------------------------

    # Só compacta a pasta se a flag for True
    if zip_output:
        # Verifica se algo foi gerado antes de tentar compactar
        if rx_found_count > 0 and os.listdir(pathdir):
            print(f"Compactando resultados em {pathdir}...")
            do_zip(pathdir)
        elif rx_found_count == 0:
            print("Nenhum arquivo .pcd gerado para compactar.")
        else:
             print(f"Pasta {pathdir} está vazia, nada para compactar.")
    else:
        print(f"Resultados da varredura mantidos em {pathdir} (sem zip).")