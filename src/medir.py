"""Mede a abertura nos 5 pontos fixos de cada fissura, nas 4 datas, e calcula o IC entre 0 e 21 dias.

Uso:  python src/medir.py                # limiar 0,40 (TCC)
      python src/medir.py --limiar 0.35  # análise de sensibilidade
Entradas: fotos (config.PASTA_FOTOS), dados/fotos.json, dados/alinhamento.json, dados/pontos_fixos.json
Saídas:   dados/medicoes_pontos.csv e dados/resultados_fissuras.csv"""
import argparse, csv, json, os
import cv2
import numpy as np
from config import DATAS, PASTA_DADOS, MM_POR_PIXEL, LIMIAR, BUSCA_DIA0, BUSCA_DEMAIS, RENOMEAR, DESCARTADAS, LIMITE_DETECCAO
from fotos import carregar_mapa, caminho
from imagem import carregar, escurecimento, largura


def para_data(pt, normal, M):
    """Leva ponto e normal do quadro de 0 dias para o quadro da data (M leva a data -> 0 dias)."""
    Mi = cv2.invertAffineTransform(np.array(M))
    p = Mi[:, :2] @ np.asarray(pt, float) + Mi[:, 2]
    v = Mi[:, :2] @ np.asarray(normal, float); v = v / np.linalg.norm(v)
    return p, v


def medir(mapa, alin, pontos, limiar):
    res = {}
    for c, pts in pontos.items():
        Ds = {d: escurecimento(carregar(caminho(mapa, c, d))) for d in DATAS}
        res[c] = []
        for p in pts:
            w = {}
            for d in DATAS:
                q, v = para_data([p['x'], p['y']], p['normal'], alin[c][d]['M'])
                busca = BUSCA_DIA0 if d == DATAS[0] else BUSCA_DEMAIS
                w[d] = round(largura(Ds[d], q[0], q[1], v, limiar, busca) * MM_POR_PIXEL, 4)
            res[c].append(w)
    return res


def classificar(w0, w21, zeros21):
    dw = round(w0 - w21, 3)
    if zeros21: return 'T'
    if dw > LIMITE_DETECCAO: return 'P'
    if dw < -LIMITE_DETECCAO: return 'A'
    return 'ND'


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--limiar', type=float, default=LIMIAR); a = ap.parse_args()
    mapa = carregar_mapa()
    alin = json.load(open(os.path.join(PASTA_DADOS, 'alinhamento.json')))
    pontos = json.load(open(os.path.join(PASTA_DADOS, 'pontos_fixos.json'), encoding='utf-8'))
    res = medir(mapa, alin, pontos, a.limiar)
    ordem = sorted(res, key=lambda s: (float(s.split('F')[0][1:].replace(',', '.')), s))
    suf = '' if a.limiar == LIMIAR else f'_limiar_{a.limiar:.2f}'
    with open(os.path.join(PASTA_DADOS, f'medicoes_pontos{suf}.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        wr = csv.writer(f, delimiter=';')
        wr.writerow(['Fissura (foto)', 'Fissura (TCC)', 'Ponto', 'x (px)', 'y (px)'] + [f'{d} (mm)' for d in DATAS])
        for c in ordem:
            for i, (p, w) in enumerate(zip(pontos[c], res[c]), 1):
                wr.writerow([c, '' if c in DESCARTADAS else RENOMEAR.get(c, c), f'P{i}', round(p['x'], 1), round(p['y'], 1)]
                            + [str(w[d]).replace('.', ',') for d in DATAS])
    linhas = []
    with open(os.path.join(PASTA_DADOS, f'resultados_fissuras{suf}.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        wr = csv.writer(f, delimiter=';')
        wr.writerow(['Fissura (TCC)', 'w0 (mm)', 'w21 (mm)', 'Δw (mm)', 'IC (%)', 'Tipo'])
        for c in ordem:
            if c in DESCARTADAS: continue
            w0 = np.mean([w[DATAS[0]] for w in res[c]]); w21 = np.mean([w[DATAS[3]] for w in res[c]])
            ic = (w0 - w21) / w0 * 100
            tipo = classificar(w0, w21, all(w[DATAS[3]] == 0 for w in res[c]))
            linhas.append((c.split('F')[0], ic))
            wr.writerow([RENOMEAR.get(c, c)] + [f'{v:.3f}'.replace('.', ',') for v in (w0, w21, w0 - w21)] + [f'{ic:.1f}'.replace('.', ','), tipo])
    print(f'limiar = {a.limiar:.2f}')
    for t in ['T5', 'T7,5', 'T10']:
        v = [ic for tr, ic in linhas if tr == t]
        print(f'  {t:5s} n = {len(v)}  IC médio = {np.mean(v):.1f}%  desvio-padrão = {np.std(v, ddof=1):.1f}')
