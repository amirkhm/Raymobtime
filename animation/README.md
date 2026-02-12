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
  * **Configuração Centralizada:** Todas as configurações são gerenciadas através de um único arquivo `config.json`.

-----

## Requisitos e Instalação

Para executar este projeto, você precisará de:

1.  **Btensor (AppImage):** Este projeto é feito para rodar com o AppImage do Blensor, que já contém o Blender, o Python (`bpy`) e o add-on Blensor.

      * É recomendado colocar o `Blensor-x64.AppImage` na raiz do projeto.

2.  **FFmpeg:** Necessário para a exportação final do vídeo.

      * **Instalação (Linux):** `sudo apt install ffmpeg`

3.  **ImageMagick:** Necessário para a geração das legendas (overlay) nos frames.
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
├── main.py             # Script principal (orquestrador)
├── config.json         # Arquivo central de configurações
├── README.md           # Este arquivo
│
├── modules/
│   ├── paths_utils.py    # Funções para processar raios (.p2m)
│   ├── sumo_utils.py     # Funções para ler dados do SUMO
│   ├── blender_anim.py   # Lógica de animação de objetos (veículos, raios)
│   ├── blensor_scan.py   # Lógica de varredura Blensor (gera .pcd)
│   ├── helpers.py        # Funções utilitárias (zip, ângulos, pastas)
│   └── video_export.py   # Exportação de vídeo (chamada FFmpeg)
│
├── vehicles.blend      # Arquivo .blend com os modelos 3D (Carro, Pedestre, etc.)
└── Blensor-x64.AppImage # (Recomendado) Executável do Blensor
```

-----

## Configuração (`config.json`)

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
        "scenes_per_episode": 10                        // Define o número de cenas por episódio

    },
    "paths": {
        "output_dir": "saida",                      // Pasta para salvar .pcd e .zip.
        "temp_frames_dir": "blensor_frames",        // Pasta temporária para frames .png.
        "video_output_name": "blensor_animation.mp4", // Nome do vídeo final.
        "pedestrian_file_name": "sumoOutputInfoFileName_PedPed.txt",
        "vehicle_file_name": "sumoOutputInfoFileName.txt",
        "wireless_path_file": "study/model.paths.t001_01.r002.p2m"
    },
    "video": {
        "framerate": 10,          // Taxa de quadros do vídeo final.
        "codec": "libx264",       // Codec de vídeo.
        "pixel_format": "yuv420p" // Formato de pixel (para compatibilidade).
    },
    "visualization_settings": {
        "show_overlay": true,            // (true/false) Ativa ou desativa a legenda - Episódio e cena
        "show_rx_coordinates": true,     // (true/false) Habilita a legenda do Rx
        "show_tx_coordinates": false,    // (true/false) Habilita a legenda do Tx
        "active_camera": "Camera"        // Implementação futura
    },
    "debug": {
        "animation_logs": true    // (true/false) Imprime logs detalhados da animação.
    }
}
```

-----

## Modo de Uso

A execução é feita inteiramente via linha de comando, usando o Blensor AppImage para rodar o script `main.py` em modo *background*.

### Sintaxe do Comando

```bash
./Blensor-x64.AppImage --background --python main.py -- <caminho_para_pasta_de_dados> [flags_opcionais]
```

### Argumentos

  * `./Blensor-x64.AppImage`: O executável do Blensor.
  * `--background`: Executa o Blensor sem interface gráfica.
  * `--python main.py`: Informa ao Blensor qual script Python executar.
  * `--`: **Separador obrigatório.** Indica ao Blensor que os argumentos a seguir são para o script Python, e não para o Blensor.
  * `<caminho_para_pasta_de_dados>`: (Obrigatório) O caminho para a pasta que contém os diretórios `run00000`, `run00001`, etc.
  * `[flags_opcionais]`:
      * `--scan`: Ativa a geração de nuvem de pontos (`.pcd`). Sem esta flag, apenas o vídeo é gerado.

### Exemplos

Suponha que seus dados do SUMO estejam em `/home/user/simulacoes/cenario_01`.

#### Exemplo 1: Gerar Apenas o Vídeo

(Roda a simulação completa, renderiza os frames e cria o `.mp4`, mas ignora a varredura Blensor).

```bash
./Blensor-x64.AppImage --background --python main.py -- /home/user/simulacoes/cenario_01
```

#### Exemplo 2: Gerar Vídeo E Varredura .pcd

(Roda a simulação, gera os arquivos `.pcd` para cada run e cria o `.mp4`).

```bash
./Blensor-x64.AppImage --background --python main.py -- /home/user/simulacoes/cenario_01 --scan
```

-----

## Saídas (Outputs)

Após a execução, os seguintes arquivos/pastas serão criados na raiz do projeto:

  * **`blensor_animation.mp4`**: O vídeo final da animação (conforme `video_output_name`).
  * **`saida/`**: A pasta de saída principal (conforme `output_dir`).
      * **`saida/run0000X/`**: Se `zip_scan_results` for `false`, contém os arquivos `.pcd` brutos.
      * **`saida/run0000X.zip`**: Se `zip_scan_results` for `true`, contém os arquivos `.pcd` compactados.
  * **`blensor_frames/`**: Pasta temporária contendo todos os frames `.png` renderizados. (Pode ser ignorada ou deletada após a execução).