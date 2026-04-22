import sys
import os

# --- Configuração Inicial do Path ---
# Adiciona o diretório raiz ao sys.path para que o Blender
# possa encontrar a pasta 'modules'.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# --- Importações dos Módulos do Projeto ---
import bpy
import shutil
import json
from datetime import datetime
from modules.subtitle_utils import process_subtitles    # add JK
from modules.camera_utils import setup_camera_view      # add JK

from modules.helpers import base_run_dir_fn, setup_directories
from modules.sumo_utils import get_sumo_data
from modules.paths_utils import get_path_data
from modules.blender_anim import (
    animate_vehicles, 
    animate_rays, 
    end_ray_animation,
    carregar_coordenadas_txrx,      # add JK
    posicionar_rx,                  # add JK
    posicionar_tx,                  # add JK
)

from modules.blensor_scan import run_scan
from modules.video_export import create_video

def main():
    startTime = datetime.now()

    # --- 1. Carregar Configuração ---
    config_path = os.path.join(project_root, "config.json")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"❌ Erro: 'config.json' não encontrado em {project_root}")
        sys.exit(1)

    cfg_sim = config['simulation']
    cfg_paths = config['paths']
    cfg_video = config['video']
    cfg_debug = config['debug']


    # --- CARREGAR O CENÁRIO .BLEND ---
    scenario_path = cfg_paths.get("scenario_blend_file")
    if scenario_path and os.path.exists(scenario_path):
        try:
            bpy.ops.wm.open_mainfile(filepath=scenario_path)
            print(f"✅ Cenário carregado: {scenario_path}")
        except Exception as e:
            print(f"❌ Falha ao carregar o cenário {scenario_path}: {e}")
            sys.exit(1)
    elif scenario_path:
        print(f"⚠️ Aviso: Caminho do cenário não encontrado: {scenario_path}")
        print("Continuando com o cenário padrão do Blender.")
    else:
        print("⚠️ Aviso: 'scenario_blend_file' não definido no config.json.")
        print("Continuando com o cenário padrão do Blender.")

    
    scene = bpy.context.scene
    
    # 1. Garante que está sendo usado o motor "Blender Internal"
    # (necessário para os materiais 'shadeless' dos raios)
    scene.render.engine = 'BLENDER_RENDER'
    
    # 2. Pega a camada de render ativa
    active_layer = scene.render.layers.active
    
    # 3. Desativa passes de dados
    active_layer.use_pass_ambient_occlusion = False
    active_layer.use_pass_mist = False
    active_layer.use_pass_z = False
    
    # 4. ATIVA o passe principal (a imagem colorida)
    active_layer.use_pass_combined = True
    
    # 5. Garante que "sólidos" e "fios" (curvas) sejam renderizados
    active_layer.use_solid = True
    active_layer.use_strand = True # Importante para curvas
    
    print("✅ Configurações de render para Cor (Combined Pass).")
    # ----------------------------------------------------


    # --- 2. Processar Argumentos de Linha de Comando ---
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    if not argv:
        print("❌ Uso: blender --background --python main.py -- <pasta_de_entrada>")
        sys.exit(1)

    use_scan = "--scan" in argv
    if "--scan" in argv:
        argv.remove("--scan")
    folder_scanned_name = argv[0]

    print(f"📁 Pasta de entrada: {folder_scanned_name}")
    print(f"🚶 Pedestres: {'ativados' if cfg_sim['use_pedestrians'] else 'desativados'}")
    print(f"🔦 Raios: {'ativados' if cfg_sim['use_rays'] else 'desativados'}")
    print(f"📡 Varredura .pcd: {'ativada' if use_scan else 'desativada'}")

    # --- 3. Configurar Ambiente (Pastas e Cena) ---
    tmp_frame_dir = os.path.join(project_root, cfg_paths['temp_frames_dir'])
    saida_dir = os.path.join(project_root, cfg_paths['output_dir'])
    setup_directories(tmp_frame_dir, saida_dir)

    # A cena já foi carregada, apenas re-atribui a variável
    scene = bpy.data.scenes['Scene']
    scene.frame_start = 0
    scene.frame_end = cfg_sim['end_run'] - 1
    
    cam = bpy.data.objects.get("Camera") or [o for o in bpy.data.objects if o.type=="CAMERA"][0]
    scene.camera = cam

    # --- 4. Loop de Processamento Principal ---
    frame_num = 0
    step = 0
    step_direction = 1
    frame_step = cfg_sim['frame_step']
    
    # Pega a flag de zip (com um padrão True para segurança)
    zip_results = cfg_sim.get("zip_scan_results", True) 

    # Identifica se o receptor é fixo ou móvel - add JK
    cfg_ds = config.get('dataset_config', {})       #add JK
    is_fixed = cfg_ds.get('use_fixed_receivers', True)      #add JK

    for run in range(cfg_sim['start_run'], cfg_sim['end_run']):
        print(f"\n🌀 Processando run {run} ...")
        for o in bpy.data.objects:      #add JK
            if o.name.startswith(("RX", "TX", "DEBUG_LBL")):
                bpy.data.objects.remove(o, do_unlink=True)

        scene_path = os.path.join(folder_scanned_name, base_run_dir_fn(run))
        if not os.path.exists(scene_path):
            print(f"⚠️ Pasta {scene_path} não encontrada. Pulando run {run}.")
            continue

        # --- Coleta de Dados ---
        sumo_file_name = cfg_paths['pedestrian_file_name'] if cfg_sim['use_pedestrians'] else cfg_paths['vehicle_file_name']
        sumo_file = os.path.join(scene_path, sumo_file_name)
        path_file = os.path.join(scene_path, cfg_paths['wireless_path_file'])
        
        # Caminho para os dados do Wireless Insite desta run
        caminho_txrx = os.path.join(scene_path, "model.txrx")   #Add JK
        
        # add JK - Carrega o dicionário com Tx e Rx
        dados_antena = carregar_coordenadas_txrx(caminho_txrx) 
        coords_tx = dados_antena['tx'] 
        coords_rx = dados_antena['rx']  

        # add JK - Define o ponto do TX (pega o primeiro ponto da lista de TXs)
        if len(coords_tx) > 0:
            ponto_do_tx = coords_tx[0]
        else:
            ponto_do_tx = (0, 0, 10) # Posição reserva
            print(f"❗ Atenção Run {run}: Nenhum TX encontrado no .txrx!")

        #testar se está sendo lido o txrx
        #print("DEBUG: Encontrei {} receptores no arquivo .txrx".format(len(coords_insite)))

        position_data = get_sumo_data(sumo_file, cfg_sim['use_pedestrians'])
        path_vectors = get_path_data(path_file)

        # --- Lógica de Animação de Pedestres ---
        if step == 2:
            step_direction = -1
        elif step == 0:
            step_direction = 1
        step += step_direction

        # --- Animação e Renderização ---
        animate_vehicles(position_data, run, frame_step, step, config, cfg_debug['animation_logs'])     # add JK - Inclusão do parametro config

        #add JK - Posiciona o objeto Rx e Tx no lugar antes de renderizar
        posicionar_rx(coords_rx, is_fixed, position_data, config)
        posicionar_tx(ponto_do_tx, config)

        # add JK - Chamada do módulo camera_utils.py para decidir o enquadramento
        cam_ativa = setup_camera_view(config, scene, coords_rx)

        if cfg_sim['use_rays']:
            animate_rays(path_vectors, frame_num, frame_step)
            end_ray_animation(frame_num, frame_step)

        # Renderiza frame
        
        scene.frame_set(frame_num)
        
        frame_path = os.path.join(tmp_frame_dir, f"frame_{frame_num:05d}.png")
        bpy.context.scene.render.filepath = frame_path
        bpy.ops.render.render(write_still=True)
        
        # Chamada para Legenda - add JK
        process_subtitles(frame_path, scene, cam_ativa, position_data, run, config)
        # --- Varredura (Opcional) ---
        if use_scan:
            scan_output_dir = os.path.join(saida_dir, base_run_dir_fn(run))
            run_scan(position_data, scan_output_dir, zip_results)

        frame_num += frame_step

    # --- 5. Exportação de Vídeo ---
    print("\n🎬 Todas as runs processadas. Gerando vídeo final...")
    video_path = os.path.join(project_root, cfg_paths['video_output_name'])
    create_video(tmp_frame_dir, video_path, cfg_video)

    print(f"⏱ Tempo total: {datetime.now() - startTime}")


if __name__ == '__main__':
    main()