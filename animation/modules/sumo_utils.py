import csv
import numpy as np
import sys

def get_sumo_data(info_file, use_pedestrians):
    """Wrapper para carregar dados de veículos ou pedestres."""
    try:
        if use_pedestrians:
            return get_info_pedestrian(info_file)
        else:
            return get_info_vehicles(info_file)
    except FileNotFoundError:
        print(f"⚠️ Arquivo SUMO não encontrado: {info_file}")
        return {}
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo SUMO {info_file}: {e}")
        return {}


def get_info_vehicles(sumo_info_file):
    """Lê as posições dos veículos do arquivo de info do SUMO."""
    with open(sumo_info_file) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='`')
        vPosition = {}
        for row in reader:
            row['isRx'] = (row['receiverIndex'] != '-1')        # add JK modificado de == '-1' para != '-1'
            thisAngleInRad = np.radians(float(row['angle']))
            deltaX = (float(row['length'])/2.0) * np.sin(thisAngleInRad)
            deltaY = (float(row['length'])/2.0) * np.cos(thisAngleInRad)
            vPosition[row['veh']] = {
                'xinsite': str(float(row['xinsite']) - deltaX),
                'yinsite': str(float(row['yinsite']) - deltaY),
                'height': row[' height'],
                'angle': row['angle'],
                'isRx': row['isRx'], 
                'rx_index': row['receiverIndex'],    # add JK
                'z3': row['z3']
            }
    return vPosition

def get_info_pedestrian(info_file):
    """Lê as posições dos pedestres do arquivo de info do SUMO."""
    with open(info_file) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='`')
        vPosition = {}
        for row in reader:
            row['isRx'] = (row['receiverIndex'] != '-1')
            thisAngleInRad = np.radians(float(row['angle']))
            deltaX = (float(row['length'])/2.0) * np.sin(thisAngleInRad)
            deltaY = (float(row['length'])/2.0) * np.cos(thisAngleInRad)
            vPosition[row['ped']] = {
                'xinsite': str(float(row['xinsite']) - deltaX),
                'yinsite': str(float(row['yinsite']) - deltaY),
                'height': str(1.72), # Altura fixa para pedestre
                'angle': row['angle'],
                'isRx': row['isRx'], 
                'z3': 0
            }
    return vPosition