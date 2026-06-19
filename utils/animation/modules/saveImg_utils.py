import os
import shutil

def copy_and_rename_frame(frame_temp_path, video_frame_index, run, config):
    """
    Copia o frame da pasta temporária para o diretório final indicado pelo usuário,
    renomeando-o para o padrão estabelecido, sem afetar o fluxo de renderização original.
    """
    # Coleta o bloco 'image' do dicionário de configuração
    image_config = config.get('image', {})

    # Se a flag não estiver explícita como string "true", o recurso não é executado
    if str(image_config.get('save_image', "false")).lower() != "true":
        return

    # Recupera o caminho de destino configurado no JSON
    dest_dir = image_config.get('save_img_pathFile')
    if not dest_dir:
        print("⚠️ [Aviso Imagem] O caminho 'save_img_pathFile' não foi definido no arquivo de configuração.")
        return

    # Garante que a pasta informada pelo usuário seja criada de forma permanente
    os.makedirs(dest_dir, exist_ok=True)

    # Extrai o nome do dataset e o nome da câmera ativa de forma precisa do JSON
    nome_dataset = config.get('dataset_config', {}).get('name', 'dataset')
    
    # Busca o nome da câmera de acordo com a chave especificada em camera_settings ou camera
    camera_settings = config.get('camera_settings', config.get('camera', {}))
    camera_nome = camera_settings.get('active_camera_name', 'CamPersp')
    camera_nome = os.path.basename(camera_nome).replace('.', '_')

    # Monta a string do novo nome: imgxxxxx_runxxxx_cameraescolhidaNaGeracao_nomedodataset.png
    new_filename = f"img{video_frame_index:05d}_run{run:04d}_{camera_nome}_{nome_dataset}.png"
    dest_path = os.path.join(dest_dir, new_filename)

    try:
        # Realiza a cópia da imagem temporária criando o novo arquivo renomeado no destino final
        shutil.copy(frame_temp_path, dest_path)
        print(f"📸 [Imagem] Arquivo copiado e organizado em: {new_filename}")
    except Exception as e:
        print(f"❌ [Erro Imagem] Falha ao copiar arquivo para o diretório de imagens: {e}")