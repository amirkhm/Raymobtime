import bpy
from modules.helpers import add_overlay_to_frame, add_rx_label
from bpy_extras.object_utils import world_to_camera_view

"""
Módulo de Telemetria Visual com Oclusão Dinâmica Selecionável.

Permite a sobreposição de metadados telemétricos sobre frames renderizados,
com suporte a verificação de linha de visada (Line of Sight) via Raycasting
configurável via arquivo JSON.
"""

def get_2d_position(scene, camera, obj, occupied_slots, use_occlusion=True):
    if not obj: return None

    # --- 1. TESTE DE OCLUSÃO ---
    if use_occlusion:
        origem = camera.matrix_world.to_translation()
        destino = obj.matrix_world.to_translation()
        direcao = destino - origem
        hit, location, normal, index, hit_obj, matrix = scene.ray_cast(origem, direcao)
        if hit and hit_obj != obj:
            return None

    # --- 2. PROJEÇÃO PARA 2D ---
    scene.update() 
    point = obj.matrix_world.to_translation()
    point.z += 0.4 # Mantém perto do objeto Rx

    coords_2d = world_to_camera_view(scene, camera, point)

    if not (0.0 <= coords_2d.x <= 1.0 and 0.0 <= coords_2d.y <= 1.0) or coords_2d.z < 0:
        return None

    render = scene.render
    scale = render.resolution_percentage / 100
    res_x = int(render.resolution_x * scale)
    res_y = int(render.resolution_y * scale)
    
    # 3. AJUSTE PARA A TARJA PRETA (HEADER OFFSET)
    header_h = 30  # Tamanho da tarja preta (ajuste conforme o tamanho do seu cabeçalho)
    
    pixel_x = int(coords_2d.x * res_x)
    
    # Somamos o header_h para que o '0' da cena comece após a tarja
    pixel_y = int((1.0 - coords_2d.y) * res_y) + header_h

    # --- 4. TRAVA DE BORDA COM MARGEM DO HEADER ---
    margin = 10
    label_w = 80
    label_h = 20

    pixel_x = max(margin, min(pixel_x, res_x - label_w - margin))
    
    # Aqui a trava de cima é o header_h + margin! 
    # Isso impede que o RX suba para dentro da tarja preta.
    pixel_y = max(header_h + margin, min(pixel_y, (res_y + header_h) - label_h - margin))

    # --- 5. ANTI-COLISÃO ---
    offset_y = 0
    for _ in range(10):
        collision = False
        current_rect = (pixel_x, pixel_y + offset_y, label_w, label_h)
        for (ox, oy, ow, oh) in occupied_slots:
            if not (current_rect[0] + current_rect[2] < ox or 
                    current_rect[0] > ox + ow or 
                    current_rect[1] + current_rect[3] < oy or 
                    current_rect[1] > oy + oh):
                collision = True
                break
        if collision:
            offset_y -= (label_h + 2)
        else:
            break

    final_y = pixel_y + offset_y
    occupied_slots.append((pixel_x, final_y, label_w, label_h))
    return pixel_x, final_y


def process_subtitles(frame_path, scene, cam, position_data, run, config):
    """
    Gerencia a sobreposição de TX/RX e informações do dataset.
    """
    cfg_visualization = config.get('visualization_settings', {})
    cfg_ds = config.get('dataset_config', {})
    
    use_occlusion = cfg_visualization.get('use_occlusion_check', True)

    # 1. Overlay de informações do dataset (Cabeçalho externo)
    if cfg_visualization.get('show_overlay', False):
        ds_name = cfg_ds.get('name', 'Dataset')
        scenes_per_ep = cfg_ds.get('scenes_per_episode', 10)
        info_text = f"Dataset: {ds_name} | Ep: {run // scenes_per_ep} | Scene: {run % scenes_per_ep}"
        add_overlay_to_frame(frame_path, info_text)

    # 2. Configurações de exibição para TX e RX
    show_rx_coords = cfg_visualization.get('show_rx_coordinates', False)
    show_rx_only = cfg_visualization.get('show_only_rx_label', False)
    
    show_tx_coords = cfg_visualization.get('show_tx_coordinates', False)
    show_tx_only = cfg_visualization.get('show_only_tx_label', False)

    if show_rx_coords or show_rx_only or show_tx_coords or show_tx_only:
        occupied_slots = []
        from modules.helpers import add_tx_label, add_rx_label

        # --- Processamento do Transmissor (TX) ---
        if show_tx_coords or show_tx_only:
            tx_objects = [o for o in bpy.data.objects if o.name.startswith("TX")]
            for obj in tx_objects:
                coords = get_2d_position(scene, cam, obj, occupied_slots, use_occlusion=use_occlusion)
                
                if coords:
                    px, py = coords
                    if show_tx_only:
                        texto = "TX"
                    else:
                        loc = obj.matrix_world.to_translation()
                        texto = f"TX ({loc.x:.0f}, {loc.y:.0f}, {loc.z:.0f})"
                    
                    add_tx_label(frame_path, texto, px, py)

        # --- Processamento dos Receptores (RX) ---
        if show_rx_coords or show_rx_only:
            rx_objects = sorted([o for o in bpy.data.objects if o.name.startswith("RX")], key=lambda x: x.name)
            for obj in rx_objects:
                coords = get_2d_position(scene, cam, obj, occupied_slots, use_occlusion=use_occlusion)
                
                if coords:
                    px, py = coords
                    rx_num = obj.name.split('_')[-1] if '_' in obj.name else obj.get("rx_id", "?")

                    if show_rx_only:
                        texto = f"RX{rx_num}"
                    else:
                        loc = obj.matrix_world.to_translation()
                        texto = f"RX{rx_num} ({loc.x:.0f}, {loc.y:.0f}, {loc.z:.0f})"
                    
                    add_rx_label(frame_path, texto, px, py)