import copy

def get_path_data(path_info_file, num_rays_to_keep=1):
    """Carrega e classifica os dados dos raios."""
    try:
        path_info_list = get_info_path(path_info_file)
        classified_paths = classify_rays(path_info_list, num_rays_to_keep)
        return classified_paths
    except FileNotFoundError:
        print(f"⚠️ Arquivo de raios não encontrado: {path_info_file}")
        return {}
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo de raios {path_info_file}: {e}")
        return {}


def classify_rays(pathInfoList, numCl=2):
    """Filtra os raios, mantendo apenas 'numCl' melhores por receptor."""
    raysCl = {}
    cleanPathInfo = {}

    # Agrupa raios por localização do receptor
    for ray_id, points in pathInfoList.items():
        RxLocation = copy.deepcopy(points[-1]) # Pega o último ponto (receptor)
        dbRx = RxLocation[3]
        RxLocation.pop() # Remove o valor de dB
        
        # Cria uma chave única para a localização
        key = ' '.join([str(coord) for coord in RxLocation])
        
        if key not in raysCl:
            raysCl[key] = []
        raysCl[key].append(dbRx)

        # Adiciona o raio à lista limpa se ainda estiver abaixo do limite
        if raysCl[key].count(dbRx) < numCl:
             cleanPathInfo[ray_id] = points
            
    return cleanPathInfo

def get_info_path(path_info_file):
    """Lê o arquivo .p2m e extrai os pontos de cada raio."""
    with open(path_info_file) as pathfile:
        count = 0
        npoints = 0
        pathInfoList = {}
        previousLine = ''
        raysInfoLine = ''
        for line in pathfile:
            if line.startswith('Tx'):
                tmp = line.split('-')
                npoints = len(tmp)
                pathInfoList[count] = []
                raysInfoLine = previousLine
                count += 1
            elif npoints > 0:
               tmp = line.split(' ')
               # Coordenadas
               tmp[0] = float(tmp[0])
               tmp[1] = float(tmp[1])
               tmp[2] = float(tmp[2])
               # dB (da linha anterior)
               tmp2 = raysInfoLine.split(' ')
               tmp.append(float(tmp2[2]))
               
               pathInfoList[count-1].append(tmp)
               npoints -= 1
            
            previousLine = line
                    
    return pathInfoList