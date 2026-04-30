# Módulo add JK
"""
Módulo auto_main_tarefas.py

Este script automatiza a execução da simulação Raymobtime, permitindo processar
múltiplos datasets em sequência e dividir simulações longas em blocos (batches).
Ao final de cada dataset, ele utiliza o FFmpeg para unir as partes.
"""

import json
import os
import subprocess
import shutil

def unir_videos(lista, caminho_final):
    """Une as partes e salva no caminho absoluto escolhido no tarefas.json."""
    if os.path.isdir(caminho_final) or not caminho_final.endswith('.mp4'):
        print(f"❌ ERRO: O caminho de saída deve ser um ARQUIVO .mp4!")
        return False

    pasta_destino = os.path.dirname(caminho_final)
    if pasta_destino and not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    lista_txt = "lista_partes_ffmpeg.txt"
    try:
        with open(lista_txt, "w") as f:
            for v in lista:
                f.write(f"file '{os.path.abspath(v)}'\n")
        
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lista_txt, "-c", "copy", caminho_final]
        resultado = subprocess.run(cmd, capture_output=True, text=True)

        return resultado.returncode == 0
    finally:
        if os.path.exists(lista_txt):
            os.remove(lista_txt)

def rodar_automacao():
    PASTA_TEMP = "temp_processing"

    if not os.path.exists('tarefas.json'):
        print("❌ Erro: tarefas.json não encontrado.")
        return

    with open('tarefas.json', 'r') as f:
        tarefas = json.load(f)

    for t in tarefas:
        print(f"\n--- 🚀 Iniciando Dataset: {t['nome_projeto']} ---")
        
        # Recria a pasta temporária para cada dataset da lista
        if not os.path.exists(PASTA_TEMP):
            os.makedirs(PASTA_TEMP)

        videos_parciais = []
        
        for i in range(t['start_run'], t['end_run'], t['batch_size']):
            inicio = i
            fim = min(i + t['batch_size'], t['end_run'])
            nome_bloco = os.path.join(PASTA_TEMP, f"parte_{t['nome_projeto']}_{inicio}_{fim}.mp4")
            
            if os.path.exists(nome_bloco):
                print(f"⏭️ Bloco {inicio}-{fim} já existe. Pulando...")
                videos_parciais.append(nome_bloco)
                continue

            caminho_batch_json = os.path.join(PASTA_TEMP, "temp_batch.json")
            batch_cfg = {
                "simulation": {
                    "start_run": inicio, "end_run": fim,
                    "use_rays": t['config_especifica'].get('use_rays', False),
                    "use_pedestrians": t['config_especifica'].get('use_pedestrians', False)
                },
                "dataset_config": {
                    "name": t['nome_projeto'],
                    "scenes_per_episode": t['config_especifica'].get('scenes_per_episode', 10),
                    "use_fixed_receivers": t['config_especifica'].get('use_fixed_receivers', True)
                },
                "paths": {
                    "scenario_blend_file": t['config_especifica'].get('scenario_blend_file', ""),
                    "pedestrian_file_name": t['config_especifica'].get('pedestrian_file_name', "")
                },
                "visualization_settings": t.get('visualization', {}),
                "camera_settings": t.get('camera', {})
            }
            
            with open(caminho_batch_json, "w") as f:
                json.dump(batch_cfg, f)

            print(f"🎬 Renderizando runs {inicio} até {fim}...")
            cmd = ["./Blensor-x64.AppImage", "--background", "--python", "main.py", "--",
                   t['caminho_dataset'], "--batch_config", caminho_batch_json]
            
            subprocess.run(cmd)
            
            video_gerado = "saida/video_final.mp4"
            if os.path.exists(video_gerado):
                shutil.move(video_gerado, nome_bloco)
                videos_parciais.append(nome_bloco)

        if videos_parciais:
            saida_final = t.get('caminho_saida_video', f"{t['nome_projeto']}_COMPLETO.mp4")
            print(f"🔗 Unindo blocos em: {saida_final}")
            
            if unir_videos(videos_parciais, saida_final):
                shutil.rmtree(PASTA_TEMP) # Limpa apenas após sucesso total da tarefa
                print(f"✅ Processo concluído para {t['nome_projeto']}!")
            else:
                print(f"⚠️ Erro ao unir blocos de {t['nome_projeto']}. Verifique o tarefas.json.")

if __name__ == "__main__":
    rodar_automacao()