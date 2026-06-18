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
