"""Parâmetros do método de medição (seção 3.2.4 do TCC)."""
import os

# Pasta com as fotos da lupa, organizada por data: <PASTA_FOTOS>/22-10-26, 29-10-26, 05-11-26, 12-11-26
PASTA_FOTOS = os.environ.get('PASTA_FOTOS', 'REGISTRO_FOTOGRAFICO')
PASTA_DADOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dados')

DATAS = ['22-10-26', '29-10-26', '05-11-26', '12-11-26']     # 0, 7, 14 e 21 dias
ROTULO_DATA = {'22-10-26': '0 d', '29-10-26': '7 d', '05-11-26': '14 d', '12-11-26': '21 d'}

MM_POR_PIXEL = 0.0064      # calibração da lupa (imagens de 640 x 480 píxeis)
LIMIAR = 0.40              # escurecimento mínimo, relativo ao fundo, para o píxel contar como fissura aberta
BUSCA_DIA0 = 6             # busca do ponto mais escuro ao longo da normal, em píxeis (imagem de referência)
BUSCA_DEMAIS = 14          # idem, nas imagens de 7, 14 e 21 dias (tolera pequenos erros de alinhamento)
N_PONTOS = 5               # pontos fixos por fissura
LIMITE_DETECCAO = 0.013    # mm (cerca de 2 píxeis)

# A fissura T10F04 do registro fotográfico foi descartada; as seguintes foram renumeradas no TCC.
RENOMEAR = {'T10F05': 'T10F04', 'T10F06': 'T10F05', 'T10F07': 'T10F06', 'T10F08': 'T10F07'}
DESCARTADAS = ['T10F04']
