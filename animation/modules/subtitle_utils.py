import bpy
from modules.helpers import add_overlay_to_frame, add_rx_label
from bpy_extras.object_utils import world_to_camera_view


def get_vehicle_2d_position(scene, camera, veh_id):
    obj = bpy.data.objects.get(veh_id)
    if not obj: return None

    # No Blender 2.79 usa scene.update()
    scene.update() 
    
    # Pega a localização do objeto
    point = obj.location.copy()
    point.z += 3.0 

    #Converte a posição 3D para um ponto na tela (0.0 a 1.0)
    coords_2d = world_to_camera_view(scene, camera, point)

    if not (0.0 <= coords_2d.x <= 1.0 and 0.0 <= coords_2d.y <= 1.0) or coords_2d.z < 0:
        return None

    render = scene.render
    # Usamos variáveis para garantir que o cálculo seja limpo
    res_x = render.resolution_x * (render.resolution_percentage / 100)
    res_y = render.resolution_y * (render.resolution_percentage / 100)
    
    # Transforma a porcentagem em pixel na tela
    pixel_x = int(coords_2d.x * res_x)
    pixel_y = int((1.0 - coords_2d.y) * res_y)

    return pixel_x, pixel_y


def process_subtitles(frame_path, scene, cam, position_data, run, config):
    # Config da Legenda
    cfg_visualization = config.get('visualization_settings', {})
    cfg_ds = config.get('dataset_config', {"name": "ds", "scenes_per_episode": 50})
    scenes_per_ep = cfg_ds['scenes_per_episode']
    ds_name = cfg_ds['name']


    # Lógica da legenda (Cena e episódio)
    if cfg_visualization.get('show_overlay', False):
        current_episode = run // scenes_per_ep
        current_scene = run % scenes_per_ep
        info_text = "Dataset: {} | Ep: {} | Scene: {}".format(ds_name, current_episode, current_scene)
        add_overlay_to_frame(frame_path, info_text)

    # Lógica das Coordenadas do Rx
    if cfg_visualization.get('show_rx_coordinates', False):
        scene.update()
        for veh_id, info in position_data.items():
            if info.get('isRx', False):
                # Converte 3D -> 2D
                coords = get_vehicle_2d_position(scene, cam, veh_id)
                if coords:
                    px, py = coords
                    texto_rx = "RX: [{:.2f}, {:.2f}]".format(float(info['xinsite']), float(info['yinsite']))
                    add_rx_label(frame_path, texto_rx, px, py)