# Simulação de Tráfego e Sensores com Blensor

Este projeto utiliza o **Blensor** (um fork do Blender focado em simulação de sensores) para orquestrar simulações complexas de tráfego, comunicação sem fio e varreduras de sensores (como LiDAR), a partir de dados gerados pelo SUMO.

O objetivo principal é criar animações e datasets de nuvens de pontos (`.pcd`) para pesquisa em redes veiculares (V2X), veículos autônomos e ambientes urbanos inteligentes.

-----

## Funcionalidades

  * **Animação de Tráfego:** Anima veículos, pedestres, ônibus e caminhões no Blender usando dados de posição do SUMO.
  * **Visualização de Raios:** Renderiza raios (linhas 3D) para simular comunicação sem fio, baseando-se em arquivos de *path* (`.p2m`).
  * **Varredura LiDAR:** Utiliza o Blensor para realizar varreduras de sensor, gerando arquivos de nuvem de pontos (`.pcd`) para cada *run*.
  * **Exportação de Vídeo:** Renderiza a animação completa e a compila automaticamente em um vídeo `.mp4` usando FFmpeg.
  * **Modularidade:** O código é totalmente modular, facilitando a manutenção e a adição de novas funcionalidades.
  * **Configuração Centralizada:** Todas as configurações são gerenciadas através do arquivo `config.json` para tarefas gerais ou para rodar com poucas runs.
  * **Processamento em Lote (Batching):** Divide simulações longas em blocos menores (ex: de 10 em 10 ou 500 em 500 runs). O Blender é reiniciado a cada bloco, limpando a memória RAM.
  * **Fila de Datasets:** Permite listar vários cenários no ficheiro (`tarefas.json`) para serem processados em sequência sem intervenção manual.

  * **Retomada:** Se o processo for interrompido, o script identifica os blocos já renderizados e retoma exatamente de onde parou.

  * **Gestão de Ficheiros Temporários:** Cria automaticamente uma pasta (`temp_processing`) para organizar partes parciais dos videos e limpa tudo ao final.

  * **Saída Customizada:** Possibilidade de definir caminhos absolutos diferentes para o vídeo final de cada dataset.
  * **Salvar imagens:** Possibilidade de salvar apenas as imagens
  * **Legenda:** Adiciona legenda (ID e coordenadas de Rx/Tx) nas animações do dataset
  * **Camera:** É possivel escolher a camera do cenário o qual quer gerar o video e/ou a imagem

-----

## Requisitos e Instalação

Para executar este projeto, você precisará de:

1.  **Btensor (AppImage):** Este projeto é feito para rodar com o AppImage do Blensor, que já contém o Blender, o Python (`bpy`) e o add-on Blensor.

      * É recomendado colocar o `Blensor-x64.AppImage` na raiz do projeto.

2.  **FFmpeg:** Necessário para a exportação final do vídeo.

      * **Instalação (Linux):** `sudo apt install ffmpeg`

3.  **ImageMagick:** Necessário para a geração das legendas nos frames.
      * **Instalação (Linux):** `sudo apt install imagemagick`

### Passos de Instalação

1.  Clone este repositório:
    ```bash
    git clone <seu-repositorio-url>
    cd <nome-do-projeto>
    ```
2.  Baixe o `Blensor-x64.AppImage` e coloque-o na pasta raiz (`project_root/`).
3.  Torne o AppImage executável:
    ```bash
    chmod +x Blensor-x64.AppImage
    ```
4.  Certifique-se de que o FFmpeg está instalado em seu sistema e acessível pelo PATH.

-----

## Estrutura do Projeto

```
project_root/
│
├── main.py                 # Script principal (orquestrador)
├── config.json             # Arquivo central de configurações gerais e para um único Dataset
├── auto_main_tarefas.py    # Script principal para gerenciar tarefas de geração de vídeo (em blocos) para multiplos Datasets
├── tarefas.json            # Arquivo de configuração de multiplos datasets
├── README.md               # Este arquivo
│
├── modules/
│   ├── paths_utils.py    # Funções para processar raios (.p2m)
│   ├── sumo_utils.py     # Funções para ler dados do SUMO
│   ├── blender_anim.py   # Lógica de animação de objetos (veículos, raios)
│   ├── blensor_scan.py   # Lógica de varredura Blensor (gera .pcd)
│   ├── helpers.py        # Funções utilitárias (zip, ângulos, pastas)
│   └── video_export.py   # Exportação de vídeo (chamada FFmpeg)
|   └── subtitle_utils.py # Lógica de legendas (Cena, Ep, Tx, Rx)
|   └── camera_utils.py   # Módulo para gerenciamento das Câmeras
|   └── saveImg_utils.py  # Módulo para salvar e renomear as imagens em pasta definida
│
├── vehicles.blend      # Arquivo .blend com os modelos 3D (Carro, Pedestre, etc.)
└── Rx.blend             # Arquivo .blend com objeto para posicionar nos receptores
└── Tx.blend             # Arquivo .blend com objeto para posicionar nos transmissores
└── Blensor-x64.AppImage # (Recomendado) Executável do Blensor
```

-----

## Configuração 
### (`config.json`)

O arquivo `config.json` controla todos os aspectos da simulação.

```json
{
    "simulation": {
        "use_rays": true,         // (true/false) Desenha os raios de comunicação.
        "use_pedestrians": true,  // (true/false) Carrega dados de pedestres (PedPed.txt).
        "start_run": 0,           // Primeira 'run' a processar.
        "end_run": 3,             // 'run' final (não inclusivo). Processa de start_run até end_run-1.
        "frame_step": 1,          // Quantos frames avançar por 'run'.
        "zip_scan_results": false // (true/false) Compacta os .pcd gerados em .zip.
    },
    "dataset_config": {
        "name": "s006 Rosslyn 10FixedRx 28GHz",         // Nome do dataset na legenda
        "scenes_per_episode": 10,                       // Define o número de cenas por episódio
        "use_fixed_receivers": true                     // Determina se o receptor é fixo ou mobile

    },
    "paths": {
        "output_dir": "saida",                      // Pasta para salvar .pcd e .zip.
        "temp_frames_dir": "blensor_frames",        // Pasta temporária para frames .png.
        "scenario_blend_file": "/home/jessica/Documentos/Raymobtime/raymobtimeV2/raymobtime/animation/bases_files/s006_Rosslyn_10FixedRx_28GHz/teste4rosslyn.blend", // Pasta do cenário
        "video_output_name": "blensor_animation.mp4", // Nome do vídeo final.
        "pedestrian_file_name": "sumoOutputInfoFileName_PedPed.txt",
        "vehicle_file_name": "sumoOutputInfoFileName.txt",
        "wireless_path_file": "study/model.paths.t001_01.r002.p2m",
        "vehicles_blend_file": "/home/jessica/Documentos/Raymobtime/raymobtimeV2/raymobtime/animation/vehicles.blend",  // Indicar onde está o vehicles
        "rx_blend_file": "/home/jessica/Documentos/Raymobtime/raymobtimeV2/raymobtime/animation/Rx.blend",      // Indicar onde está o Rx.blend
        "tx_blend_file": "/home/jessica/Documentos/Raymobtime/raymobtimeV2/raymobtime/animation/Tx.blend"       // Indicar onde está o Tx.blend
    },
    "video": {
        "genarete_video": "true",   // Habilitação do video
        "framerate": 10,          // Taxa de quadros do vídeo final.
        "codec": "libx264",       // Codec de vídeo.
        "pixel_format": "yuv420p" // Formato de pixel (para compatibilidade).
    },
    "image": {
        "save_image": "true",   // Habilitação de salvar as imagens
        "save_img_pathFile": "/home/jessica/Documentos/Raymobtime/raymobtimeV2/raymobtime/animation/bases_files/imagens/t003_Rosslyn_05MobileRx_60GHz"  // Indicar onde quer salvar as imagens
    },
    "visualization_settings": {
        "show_overlay": true,            // (true/false) Ativa ou desativa a legenda - Episódio e cena
        "show_rx_coordinates": true,     // (true/false) Habilita a legenda do Rx com coordenadas
        "show_only_rx_label": false,     // Habilita apenas a identificação do Rx sem a coordenadas
        "show_tx_coordinates": false,    // (true/false) Habilita a legenda do Tx com coordenadas
        "show_only_tx_label": false,     // Habilita apenas a identificação do Tx sem a coordenadas
        "use_occlusion_check": true      // true habilita o uso de Ray cast para retirar legendas de objetos que não está na visão da cãmera
    },
    "camera_settings": {
        "active_camera_name": "CamPerspRx43910",    // Escolher a câmera do cenário no qual quer gerar o vídeo
        "use_blender_default": false,               // true para usar as configurações originais definidas na câmera do cenário 
        "type": "PERSP",                            // Tipo da câmera a qual quer ajustar as configurações. Há o tipo perspectiva e ortogonal
        "ortho_scale": 260,                         // Configuração para câmera tipo ORTHO - quando o blender default é false
        "focal_length": 10,                         // Configuração para câmera tipo PERSP - quando o blender default é false
        "rx_id_to_focus": 4,                        // Focar em um receptor, indicar qual é o número/identificação do ID do Rx - quando look rx é true
        "mode": "static",                           // 'static' (câmera no lugar do Blender) ou 'follow' (câmera segue o RX).
        "look_at_rx": true,                         // Se True, a câmera gira para centralizar o RX.
        "relative_position": [-60, 0, 20]           // Configuração da posição da câmera
    },
    "debug": {
        "animation_logs": true    // (true/false) Imprime logs detalhados da animação.
    }
}
```

### (`tarefas.json`)
```json
[
    {
        "nome_projeto": "s004_comRaios",
        "caminho_dataset": "/home/jessica/Documentos/Raymobtime/raymobtimeV2/raymobtime/animation/bases_files/s004_Rosslyn_10MobileRx_60GHz_5000episodes_scenes1_Ts1s_InSite3.2",
        "caminho_saida_video": "/home/jessica/Documentos/Raymobtime/raymobtimeV2/raymobtime/animation/bases_files/videos/video_final_s004_comRaios.mp4",
        "start_run": 0,
        "end_run": 70,
        "batch_size": 10,
        "config_especifica": {
            "use_rays": true,
            "use_pedestrians": false,
            "scenes_per_episode": 1,
            "use_fixed_receivers": false,
            "scenario_blend_file": "/home/jessica/Documentos/Raymobtime/raymobtimeV2/raymobtime/animation/bases_files/s004_Rosslyn_10MobileRx_60GHz_5000episodes_scenes1_Ts1s_InSite3.2/teste4rosslyn.blend",
            "pedestrian_file_name": "sumoOutputInfoFileName_PedPed.txt"
        },
        "video": {
            "genarete_video": "true"
        },
        "imagem": {
            "save_image": "false",
            "save_img_pathFile": "/home/jessica/Documentos/Raymobtime/raymobtimeV2/raymobtime/animation/bases_files/imagens/t003_Rosslyn_05MobileRx_60GHz"
        },
        "visualization": {
            "show_overlay": true,
            "show_rx_coordinates": true,
            "show_only_rx_label": true,
            "show_tx_coordinates": true,
            "show_only_tx_label": false,
            "use_occlusion_check": true
        },
        "camera": {
            "active_camera_name": "CamPerspRx1265",
            "use_blender_default": true,
            "type": "PERSP",
            "ortho_scale": 260,
            "focal_length": 12,
            "rx_id_to_focus": 4,
            "mode": "static",
            "look_at_rx": false,
            "relative_position": [-60, 0, 20]
        }
    }, // Fim do comando da configuração da primeira tarefa - 1° Dataset

    // Pode adicionar mais {} depois do fim da configuração da primeira tarefa/Dataset
]
```

-----

## Modo de Uso

### 1. Execução para apenas um Dataset

A execução é feita inteiramente via linha de comando, usando o Blensor AppImage para rodar o script `main.py` em modo *background*.

#### Sintaxe do Comando

```bash
./Blensor-x64.AppImage --background --python main.py -- <caminho_para_pasta_de_dados> [flags_opcionais]
```

#### Argumentos

  * `./Blensor-x64.AppImage`: O executável do Blensor.
  * `--background`: Executa o Blensor sem interface gráfica.
  * `--python main.py`: Informa ao Blensor qual script Python executar.
  * `--`: **Separador obrigatório.** Indica ao Blensor que os argumentos a seguir são para o script Python, e não para o Blensor.
  * `<caminho_para_pasta_de_dados>`: (Obrigatório) O caminho para a pasta que contém os diretórios `run00000`, `run00001`, etc.
  * `[flags_opcionais]`:
      * `--scan`: Ativa a geração de nuvem de pontos (`.pcd`). Sem esta flag, apenas o vídeo é gerado.

#### Exemplos

Suponha que seus dados do SUMO estejam em `/home/user/simulacoes/cenario_01`.

##### Exemplo 1: Gerar Apenas o Vídeo

(Roda a simulação completa, renderiza os frames e cria o `.mp4`, mas ignora a varredura Blensor).

```bash
./Blensor-x64.AppImage --background --python main.py -- /home/user/simulacoes/cenario_01
```

##### Exemplo 2: Gerar Vídeo E Varredura .pcd

(Roda a simulação, gera os arquivos `.pcd` para cada run e cria o `.mp4`).

```bash
./Blensor-x64.AppImage --background --python main.py -- /home/user/simulacoes/cenario_01 --scan
```

### 2. Execução para multiplos Datasets ou gerar as Runs em bloco
#### Para Iniciar uma sessão por PC remoto

```bash
screen -S rodar_sessao
```

#### Executar Multi-Dataset ou Runs em Bloco

```bash
python3 auto_main_tarefas.py
```


O script lerá o tarefas.json, dividirá por exemplo, as 2000 runs em blocos de 500 e unirá os vídeos automaticamente ao final.

**Para sair da sessão e deixar rodando:** **Ctrl + A** seguido de **D**

-----

## Saídas (Outputs)

Após a execução, os seguintes arquivos/pastas serão criados na raiz do projeto:

  * **`blensor_animation.mp4`**: O vídeo final da animação (conforme `video_output_name`).
  * **`saida/`**: A pasta de saída principal (conforme `output_dir`).
      * **`saida/run0000X/`**: Se `zip_scan_results` for `false`, contém os arquivos `.pcd` brutos.
      * **`saida/run0000X.zip`**: Se `zip_scan_results` for `true`, contém os arquivos `.pcd` compactados.

      Ou em caso de executar auto_main_tarefas.py:
    * **`temp_processing/`:** Pasta temporária que armazena os vídeos parciais de cada bloco (ex: `parte_s001_0_500.mp4`). É deletada automaticamente após a união
  * **`blensor_frames/`**: Pasta temporária contendo todos os frames `.png` renderizados. (Pode ser ignorada ou deletada após a execução).