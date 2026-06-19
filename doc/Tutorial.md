## Tutorial geração de dataset para machine learning com Raymobtime

Instalar SUMO e Wireless Insite

Clonar repositórios: 
- [gitlab raymobtime](https://gitlab.lasse.ufpa.br/software/raymobtime-project/raymobtime/-/tree/master?ref_type=heads).

Recomendação de organização de arquivos:
- Na pasta base files de raymobtime, crie uma pasta com o nome do seu cenário
- Dentro dessa pasta crie as pastas: sumo, meshes, wi
- Em sumo serão guardados os arquivos sumo
- Em meshes serão guardados os arquivos 3d exportados do blender para importação no wireless insite
- Em wi será guardado o projeto do wireless insite

### 1. Open street map

1. Abrir site [Open street map](https://www.openstreetmap.org).
1. Ir para a área de interesse, é possivel editar em edit.
1. Ir em export, selecionar area manualmente, selecionar a área, clicar em Exportar. Será gerado um arquivo .OSM
- Obs: Guardar .OSM na pasta do cenário.

### 2. Conversão .OSM --> .NET.XML
Converter o arquivo .OSM para o formato .NET.XML, que descreve os elementos de tráfego.. No terminal utilize o comando a seguir, realizando os ajustes indicados.
- Ajuste o inputFile para o nome do seu arquivo .osm, e o nome do outputFile.
- Deixar ou o keep ou o remove. Se der erro em algum highway, remover o highway problemático. (é possivel retirar o os keeps e highways, ficam todas as ruas)
```bash
netconvert --osm-files inputFile.osm --numerical-ids.edge-start 0 --numerical-ids.node-start 0 --keep-edges.by-type/--remove-edges.by-type highway.secondary, highway.residente -o outputFile.net.xml
```
- Guardar na pasta sumo
- Abrir .NET.XML e ajustar netOffset="X,Y" e projParameter="!". As coordenadas para o netOffset serão obtidas ao fazer placement no raymobtime, não alterar por enquanto.

### 3. Sumo
Instalar sumo normalmente.
1. Abrir o NET.XML no SUMO e ver se está ok as edges, criar caso nescessário
1. Pegar o Id das ruas da rota e ajustar no rustic.py
1. Rodar o rustic.py, irá gerar o .rou.xml
1. Ajustar o .sumo.cfg manualmente (a parte dos arquivos)
1. Conferir o .sumo.cfg como network, analizar o flow
1. Guardar na pasta sumo

### 4. Blender
[blender versão 2.79](https://www.blender.org/download/releases/2-79/)

[Blosm extension](https://github.com/vvoovv/blosm)

[Bash export](https://github.com/mrtripie/Blender-Super-Batch-Export)

1. Importar o .OSM via blosm
    - Option: file, marcar buildings e roads and paths.
1. Excluir elementos desnecessários, ajustar como meshes, criar plano ground, salvar como .blend
1. Exportar meshes como .dae via bash export, guardar na pasta meshes

### 5. Wireless insite
Instalar versão 3.3
1. Colocar o random-line.object e base.object na pasta meshes
1. Para passar de um sistema operacional para outro usar no terminal na pasta meshes
    ```bash
    find . -type f -print0 | xargs -0 -n 1 -P 4 unix2dos
    ```
1. Copiar os arquivos para o windows para a pasta de wi
1. Abrir o WI em geometry: open random.line como object (ele deve aparecer, é um bolco de metal) e import meshes no WI como city.
1. Ajustar materiais, onda (sinusoid), criar antenas, transmissores (nome: Tx)(atrentar para suas posições) e receptores (nome: Rx) em  transceivers (atribuir atenas), área de estudo (nomear como study)(X3D). 

    #### configurações da study area
    - Short description como study.
    - Modelo de propagação X3D.
    - Setar número de raios por par Tx Rx.
    - outputs: (1) propagation paths, (2) received power, (3) complex E-fields, (4) complex impulse response, (5) delay spread.

1. Clicar no botão de run para averiguar os raios
1. Conferir os raios gerados
1. Salvar projeto com o nome model
1. Copiar os arquivos model.txrx como base.txrx e o model.study.xml como base.study.xml
1. Analise onde é o 0, 0 x e y no wireless, abra seu .net.xml e verifique a coordenada do mesmo ponto, ajuste no seu .net.xml na parte netoffset (x,y). Para verificar se está ok precisa rodar o placement no raymobtime.

### 6. Raymobtime
1. Ajustar config.json
1. Rodar placement
    ```bash
    python3 simulation -po
    ```

1. Abrir algumas run gerada, verificar se as posições dos veiculos batem com ajuste de coordenadas.

1. Se tudo estiver ok, rodar traçado de raios 
    ```bash
    python3 simulation -rj
    ```

1. Verificar o traçado de algumas das runs

1. Rodar db, coord, rays, beams, images...