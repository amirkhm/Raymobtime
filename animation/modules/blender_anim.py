import bpy
import os
from math import radians, degrees
from .helpers import chooseAngleToRotate # Import relativo


"""
Módulo de Animação e Manipulação de Objetos 3D.
Responsável por importar marcadores (RX), animar veículos do SUMO 
e gerenciar a visualização de raios de propagação.
"""


# Cache de templates de veículos para evitar reabrir o .blend
TEMPLATE_CACHE = {}

def create_line_blender(objname, cList, frame_num, frame_step):
    """Cria um objeto de curva (raio) no Blender."""
    curvedata = bpy.data.curves.new(name='curve', type='CURVE')
    curvedata.dimensions = '3D'

    objectdata = bpy.data.objects.new(objname, curvedata)
    objectdata.location = (0,0,0)
    bpy.context.scene.objects.link(objectdata)
    
    # Força o raio a estar na Camada 1 (principal).
    layers = [False] * 20
    layers[0] = True
    objectdata.layers = layers

    polyline = curvedata.splines.new('POLY')
    polyline.points.add(len(cList)-1)
    
    # Lógica de Material "Shadeless" (correta)
    def create_simple_material(name, color_tuple):
        """Cria um material "shadeless" para o Blender Internal."""
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = color_tuple
        mat.use_shadeless = True  # Garante que o raio brilhe
        mat.use_transparency = False
        mat.alpha = 1.0
        return mat

    # Cores
    mat_red = create_simple_material("PKHG_Red", (1,0,0))
    mat_blue = create_simple_material("PKHG_Blue", (0,0,1))
    mat_green = create_simple_material("PKHG_Green", (0,1,0))
    mat_orange = create_simple_material("PKHG_Orange", (0.8,0.2,0))
    mat_yellow = create_simple_material("PKHG_Yellow", (0.8,0.65,0))
    
    db = cList[-1][3] # dB do último ponto
    
    # Classifica por cor
    if ( db < -220 and db < -193):
        matchoose = mat_blue
    elif ( db < -166):
        matchoose = mat_green
    elif ( db < -151):
        matchoose = mat_yellow
    elif ( db < -138):
        matchoose = mat_orange
    else:
        matchoose = mat_red

    objectdata.data.materials.append(matchoose)
    objectdata.active_material = matchoose
    
    # Adiciona pontos à curva
    for num in range(len(cList)):
        x, y, z, _ = cList[num]
        polyline.points[num].co = (x, y, z, 100) # w=100
    
    
    # Valores de teste para torná-los GIGANTES.
    curvedata.extrude = 0.5         # Aumentado de 0.005
    curvedata.bevel_depth = 0.16     # Espessura add JK - alteração do valor de 0.5 para 0.2
    
    curvedata.fill_mode = 'FULL'        # Garante que seja um tubo sólido
    curvedata.bevel_resolution = 2  # Define a "redondeza"

    # Lógica de Keyframe
    
    # Oculta o raio em todos os frames anteriores
    for i in range(0, frame_num, frame_step):
        bpy.context.scene.frame_set(i)
        objectdata.hide = True
        objectdata.hide_render = True
        objectdata.keyframe_insert(data_path="hide_render")
        objectdata.keyframe_insert(data_path="hide")

    # Mostra o raio no frame atual
    bpy.context.scene.frame_set(frame_num)
    objectdata.hide = False
    objectdata.hide_render = False
    objectdata.keyframe_insert(data_path="hide_render")
    objectdata.keyframe_insert(data_path="hide")

def animate_rays(vectorsPath, frame_num, frame_step):
    """Cria os raios para o frame atual."""
    for ray_id, points in vectorsPath.items():
        objname = f"{frame_num}Ray{ray_id:05d}"
        create_line_blender(objname, points, frame_num, frame_step)

def end_ray_animation(frame_num, frame_step):
    """Oculta todos os raios do frame atual no próximo frame."""
    next_frame = frame_num + frame_step
    bpy.context.scene.frame_set(next_frame)
    
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(str(frame_num) + "Ray"):
            obj.hide_render = True
            obj.hide = True
            obj.keyframe_insert(data_path="hide_render")
            obj.keyframe_insert(data_path="hide")

def _get_template_object(template_name, config):    # Modificação JK - add do parametro config
    """Função helper para carregar e cachear objetos do vehicles.blend."""
    global TEMPLATE_CACHE
    
    if template_name in TEMPLATE_CACHE:
        return TEMPLATE_CACHE[template_name]
    
    try:
        blend_file_path = config['paths']['vehicles_blend_file']    # Modificação JK - Retirado o caminho fixo no código, agora o caminho está no JSON
        if not os.path.exists(blend_file_path):
            print(f"Erro fatal: 'vehicles.blend' não encontrado em {os.getcwd()}")
            return None

        # Caminho interno no .blend
        internal_path = f"//vehicles.blend/Object/"
        
        with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
            if template_name in data_from.objects:
                data_to.objects = [template_name]
            else:
                print(f"Template '{template_name}' não encontrado em vehicles.blend")
                return None
        
        # O objeto agora está em bpy.data.objects
        src_obj = bpy.data.objects.get(template_name)
        if src_obj:
            TEMPLATE_CACHE[template_name] = src_obj
            print(f"[Cache] Template '{template_name}' carregado.")
            return src_obj
        else:
            print(f"Falha ao carregar '{template_name}' de vehicles.blend")
            return None

    except Exception as e:
        print(f"Erro ao importar {template_name} de vehicles.blend: {e}")
        return None


def animate_vehicles(vPosition, frame_num, frame_step, step, config, DEBUG_ANIM=False):     # Modificação JK - add o parametro config
    """
    Anima veículos e pedestres no frame atual.
    Usa um cache de templates para otimização.
    """
    global TEMPLATE_CACHE
    step_str = str(step)
    scene = bpy.context.scene
    scene.frame_set(frame_num)

    # --- Oculta objetos que sumiram ---
    # Coleta nomes de objetos ativos (incluindo steps de pedestres)
    active_obj_names = set()
    for vid, vinfo in vPosition.items():
        if abs(float(vinfo['height']) - 1.72) < 1e-3:
            for s in range(1, 4): # Assumindo 3 steps
                active_obj_names.add(f"{vid}_step{s}")
        else:
            active_obj_names.add(vid)

    for obj in scene.objects:
        # Foca apenas em objetos gerenciáveis (evita câmeras, luzes, etc.)
        if obj.name.startswith(('flow', 'dflow', 'ped', '_ped')):
            if obj.name not in active_obj_names and not obj.name.startswith('_'):
                obj.hide = True
                obj.hide_render = True
                obj.keyframe_insert(data_path="hide")
                obj.keyframe_insert(data_path="hide_render")
                # Renomeia para evitar re-processamento
                obj.name = '_' + obj.name 

    # --- Anima objetos atuais ---
    use_fixed = config.get('dataset_config', {}).get('use_fixed_receivers', False) # add JK
    
    for vid, vinfo in vPosition.items():
        # Se for receptor (isRx corrigido) e a configuração for fixa - add JK
        # Não desenhamos o modelo de carro, apenas pulamos (continue) - add JK
        if vinfo.get('isRx', False) and use_fixed:  # add JK
            continue

        height = float(vinfo['height'])
        is_ped = abs(height - 1.72) < 1e-3

        if DEBUG_ANIM:
            print(f"[DEBUG] '{vid}' h={height} step={step_str}")

        # --- PEDESTRES ---
        if is_ped:
            num_steps = 3 
            base_name = vid

            # Garante que todos os clones (steps) existam
            for s in range(1, num_steps + 1):
                step_obj_name = f"{base_name}_step{s}"
                if not bpy.data.objects.get(step_obj_name):
                    template_name = f"pedestrian_step{s}"
                    src_obj = _get_template_object(template_name, config)   # Modificação JK - Foi add o parametro config
                    if not src_obj:
                        continue # Pula se o template falhou ao carregar

                    clone = src_obj.copy()
                    clone.data = src_obj.data.copy()
                    clone.name = step_obj_name
                    scene.objects.link(clone)
                    clone.rotation_euler = (radians(90), 0, 0)
                    
                    # Garante que esteja oculto desde o início
                    scene.frame_set(0)
                    clone.hide = True
                    clone.hide_render = True
                    clone.keyframe_insert(data_path="hide")
                    clone.keyframe_insert(data_path="hide_render")
                    scene.frame_set(frame_num) # Volta ao frame atual
                    
                    if DEBUG_ANIM:
                        print(f"[DEBUG] '{clone.name}' criado.")
            
            # Anima a visibilidade do step correto
            for s in range(1, num_steps + 1):
                step_obj_name = f"{base_name}_step{s}"
                obj = bpy.data.objects.get(step_obj_name)
                if not obj:
                    continue

                visible = (str(s) == step_str)
                obj.hide = not visible
                obj.hide_render = not visible
                
                # Posição e Rotação
                obj.location.xyz = float(vinfo['xinsite']), float(vinfo['yinsite']), float(vinfo['z3'])
                angle_to_rotate = 90 - float(vinfo['angle'])
                angle_to_rotate = chooseAngleToRotate(degrees(obj.rotation_euler.z), angle_to_rotate)
                obj.rotation_euler.z = radians(angle_to_rotate)

                # Keyframes
                obj.keyframe_insert(data_path="hide")
                obj.keyframe_insert(data_path="hide_render")
                obj.keyframe_insert(data_path="location")
                obj.keyframe_insert(data_path="rotation_euler")

                if DEBUG_ANIM and visible:
                    print(f"[DEBUG] '{obj.name}' visível no frame {frame_num}")

        # --- VEÍCULOS ---
        else:
            obj = bpy.data.objects.get(vid)
            if not obj:
                # Identifica o modelo pela altura
                if abs(height - 3.2) < 1e-3: model_name = "Bus"
                elif abs(height - 4.3) < 1e-3: model_name = "Truck"
                elif abs(height - 0.295) < 1e-3: model_name = "Drone"
                else: model_name = "Car" # Suposição padrão
                
                src_obj = _get_template_object(model_name, config)
                if not src_obj:
                    print(f"Pulando '{vid}' (altura {height}), template '{model_name}' não encontrado.")
                    continue
                
                obj = src_obj.copy()
                obj.data = src_obj.data.copy()
                obj.name = vid
                scene.objects.link(obj)
            
            # Define Posição e Rotação
            obj.hide = False
            obj.hide_render = False
            obj.location.xyz = float(vinfo['xinsite']), float(vinfo['yinsite']), float(vinfo['z3'])
            angle_to_rotate = 90 - float(vinfo['angle'])
            angle_to_rotate = chooseAngleToRotate(degrees(obj.rotation_euler.z), angle_to_rotate)
            obj.rotation_euler.z = radians(angle_to_rotate)

            # Keyframes
            obj.keyframe_insert(data_path="hide")
            obj.keyframe_insert(data_path="hide_render")
            obj.keyframe_insert(data_path="location")
            obj.keyframe_insert(data_path="rotation_euler")

            if DEBUG_ANIM:
                print(f"[DEBUG] Veículo '{vid}' animado no frame {frame_num}")


#Add JK  - Obter coordenadas do Rx e posicionar o objeto Rx.blend com ou sem o veículo
def carregar_coordenadas_txrx(arquivo_caminho):
    """
    Lê o arquivo .txrx e separa as coordenadas de TX e RX.
    Retorna: dict {'tx': [(x,y,z)], 'rx': [(x,y,z), ...]}
    """
    resultado = {'tx': [], 'rx': []}
    if not os.path.exists(arquivo_caminho):
        return resultado

    with open(arquivo_caminho, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()
        
        # Detecta bloco de TX ou RX
        tipo = None
        if "begin_<points> Tx" in linha: tipo = 'tx'
        elif "begin_<points> Rx" in linha: tipo = 'rx'

        if tipo:
            # Procura o nVertices dentro deste bloco
            while i < len(linhas) and "nVertices" not in linhas[i]:
                i += 1
            
            if i < len(linhas) and "nVertices" in linhas[i]:
                num_pontos = int(linhas[i].split()[1])
                for k in range(1, num_pontos + 1):
                    coords = linhas[i + k].split()
                    if len(coords) >= 3:
                        resultado[tipo].append((float(coords[0]), float(coords[1]), float(coords[2])))
        i += 1
    return resultado

#Add JK
def posicionar_rx(coords_insite, is_fixed, vPosition, config):
    """
        Importa e posiciona os Rx.blend de recepção (RX) no cenário.
        
        Args:
            projeto_root (str): Caminho base do projeto.
            coords_insite (list): Lista de tuplas (x, y, z) vindas do arquivo .txrx.
            is_fixed (bool): Define se o RX é estático ou segue um veículo.
            vPosition (dict): Dados de posição dos veículos para sincronização.
    """

    # 1. Limpa os RXs da rodada anterior
    for obj in bpy.data.objects:
        if obj.get("tipo_comunicacao") == "RX":
            bpy.data.objects.remove(obj, do_unlink=True)

    caminho_rx_blend = config['paths']['rx_blend_file']
    
    # Verifica se o arquivo Rx.blend existe antes de tentar abrir
    if not os.path.exists(caminho_rx_blend):
        print("Erro: Arquivo Rx.blend nao encontrado em: " + caminho_rx_blend)
        return

    for idx, ponto in enumerate(coords_insite):
        id_num = idx + 1
        
        # 2. Importa o objeto
        # Nota: O 'filename' deve ser o nome exato do objeto DENTRO do Rx.blend
        bpy.ops.wm.append(
            directory=os.path.join(caminho_rx_blend, "Object/"),
            filepath=caminho_rx_blend,
            filename="Rx" 
        )
        
        # 3. Procura o objeto que acabou de ser importado
        # O Blender costuma manter o nome 'Rx' ou adiciona .001, .002...
        marcador = None
        for obj in bpy.data.objects:
            if obj.name.startswith("Rx") and obj.get("tipo_comunicacao") is None:
                marcador = obj
                break

        if marcador is None:
            print("⚠️ Aviso: Nao consegui encontrar o objeto importado para o RX_{}".format(id_num))
            continue

        # 4. Configura o marcador
        marcador.name = "RX_{}".format(id_num)
        marcador["tipo_comunicacao"] = "RX"
        marcador["rx_id"] = id_num 
        
        if is_fixed:
            marcador.location = ponto
        else:
            # Lógica Móvel Corrigida:
            for veh_id, info in vPosition.items():
                # Verificamos se o índice do veículo no SUMO bate com o ID do receptor atual
                if info.get('isRx', False) and info.get('rx_index') == str(id_num):
                    carro_obj = bpy.data.objects.get(veh_id)
                    if carro_obj:
                        marcador.parent = carro_obj
                        # posicionar o Rx.blend conforme a altura do receptor
                        height = float(info.get('height', 0))
                        
                        # Define a altura da antena dinamicamente baseada no tipo de veículo
                        if abs(height - 3.2) < 1e-3:    # Ônibus
                            z_antena = 3.3
                        elif abs(height - 4.3) < 1e-3:  # Caminhão
                            z_antena = 4.4
                        elif abs(height - 0.295) < 1e-3:# Drone
                            z_antena = 0.4
                        else:                           # Carro padrão
                            z_antena = 1.6
                        
                        # Posiciona a antena exatamente acima do teto de cada modelo
                        marcador.location = (0, 0, z_antena)
                        break

#add JK
def posicionar_tx(ponto_tx, config):
    caminho_tx_blend = config['paths']['tx_blend_file']
    print(f"DEBUG: Tentando importar TX de: {caminho_tx_blend}")

    try:
        bpy.ops.wm.append(
            directory=os.path.join(caminho_tx_blend, "Object/"),
            filepath=caminho_tx_blend,
            filename="Tx" # O NOME AQUI TEM QUE SER IGUAL AO DO BLENDER
        )
    except Exception as e:
        print(f"ERRO no Append do TX: {e}")

    # Verifica se ele realmente entrou na cena
    marcador = next((o for o in bpy.data.objects if o.name.startswith("Tx") and o.get("tipo_comunicacao") is None), None)

    if marcador:
        marcador.name = "TX_1"
        marcador["tipo_comunicacao"] = "TX"
        marcador.location = ponto_tx
        print(f"✅ TX_1 posicionado com sucesso em {ponto_tx}")
    else:
        print("❌ ERRO: O objeto 'Tx' não foi encontrado na cena após o append!")