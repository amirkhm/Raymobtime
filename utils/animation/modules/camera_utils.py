import bpy
from mathutils import Vector
# add JK - camera_utils.py
"""
Módulo de Gerenciamento de Câmeras para Simulação.
Este módulo permite controlar o enquadramento, tipo de lente e 
comportamento de rastreamento (tracking) dos receptores.
"""

def setup_camera_view(config, scene, coords_insite=None):
    """
    Configura a câmera ativa e define seu comportamento de visualização.

    Args:
        config (dict): Dicionário contendo 'camera_settings' do JSON.
        scene (bpy.types.Scene): A cena atual do Blender.
        coords_insite (list, optional): Coordenadas dos RXs.

    Configurações do JSON (camera_settings):
        active_camera_name (str): Nome do objeto de câmera no Blender.
        use_blender_default (bool): Se True, ignora o script.
        type (str): 'ORTHO' ou 'PERSP'.
        ortho_scale (float): Zoom ortográfico.
        focal_length (float): Lente perspectiva (mm).
        look_at_rx (bool): Se True, a câmera gira para centralizar o RX.
        rx_id_to_focus (int): Qual RX (1, 2...) será o alvo.
        mode (str): 'static' (câmera no lugar do Blender) ou 'follow' (câmera segue o RX).
        relative_position sugestão: Perspectiva de rua [0, -60, 40], Visão Aérea [0, 0, 100] ou visão lateral [-60, 0, 20]

        Nome da camera em Rosslyn 10 fixed: camera, CamPerspRx1265 , CamOrthoTopDown , CamPerspRx43910 , CamPerspRx78, CamPerspStreetTx , CamPerspTx,
         CamPerspTx0, CamPerspTx1, CamPerspTx2, CamPerspTx3
    """
    
    cfg_cam = config.get('camera_settings', {})
    cam_name = cfg_cam.get('active_camera_name', 'Camera')
    
    # --- DEBUG DE CÂMERAS ---
    # Listar no terminal todas as câmeras que existem no .blend
    print("\n--- Verificando Câmeras no Arquivo ---")
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA':
            print("Encontrada: '{}'".format(obj.name))
    
    # Tenta selecionar a câmera do JSON
    cam = bpy.data.objects.get(cam_name)

    if cam:
        scene.camera = cam
        print(">>> SUCESSO: Usando a câmera '{}'".format(cam_name))
    else:
        print(">>> AVISO: Câmera '{}' não encontrada! Usando a padrão da cena.".format(cam_name))
        cam = scene.camera
    # -----------------------

    if cfg_cam.get('use_blender_default', True):
        scene.update()
        return cam

    # Configuração de Tipo e Lente
    cam.data.type = cfg_cam.get('type', 'PERSP')
    if cam.data.type == 'PERSP':
        cam.data.lens = cfg_cam.get('focal_length', 35)
    else:
        cam.data.ortho_scale = cfg_cam.get('ortho_scale', 100)

    # Lógica de Alvo
    target_rx_id = cfg_cam.get('rx_id_to_focus', 1)
    target_obj = bpy.data.objects.get(f"RX_{target_rx_id}")

    if target_obj:
        if cfg_cam.get('mode') == 'follow':
            # 1. Desvincula para resetar
            cam.parent = None
            
            # 2. Faz o parentesco
            cam.parent = target_obj
            
            # 3. ZERA a posição e rotação local (para ela ficar EXATAMENTE onde o carro está)
            cam.location = (0, 0, 0)
            cam.rotation_euler = (0, 0, 0)
            
            # 4. Aplica o deslocamento desejado (ex: 80 metros acima do carro)
            # Para ter a visão de cima, o 'relative_position' no JSON deve ser [0, 0, 80]
            cam.location = Vector(cfg_cam.get('relative_position', [0, 0, 80]))
            
            print(f">>> CÂMERA seguindo: {target_obj.name}")
        else:
            cam.parent = None 
        
        # 5. Para a câmera girar para o carro
        if cfg_cam.get('look_at_rx', True):
            point_at_target(cam, target_obj)
            
    return cam

def point_at_target(camera, target):
    """
    Calcula e aplica a rotação para a câmera focar em um objeto alvo.

    Args:
        camera (bpy.types.Object): A câmera que será rotacionada.
        target (bpy.types.Object): O objeto (RX) que deve ser centralizado.
    """
    target_pos = target.matrix_world.to_translation()
    direction = target_pos - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()