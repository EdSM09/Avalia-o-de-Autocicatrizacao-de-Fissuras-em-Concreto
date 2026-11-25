"""Proposta automática dos 5 pontos fixos de cada fissura (no quadro da foto de 0 dias).

1. Área comum: região coberta pelas quatro fotos após o alinhamento, com margem de 20 px.
2. Traçado: caminho de menor custo pelo mapa de escurecimento (custo = 1/(escurecimento + 0,03))
   entre as extremidades da fissura na área comum (ou por pontos de passagem definidos pelos autores).
3. Pontos: 5 posições ao longo do traçado (8%, 29%, 50%, 71% e 92% do comprimento), deslocadas até
   o píxel mais próximo com abertura mensurável aos 0 dias; normal = perpendicular ao traçado.
A proposta foi conferida visualmente e ajustada pelos autores; o resultado final, usado no TCC,
está em dados/pontos_fixos.json (campo "origem" indica os pontos ajustados)."""
import json, os, sys
import cv2
import numpy as np
from skimage.graph import route_through_array
from config import DATAS, PASTA_DADOS, LIMIAR, N_PONTOS
from fotos import carregar_mapa, caminho
from imagem import carregar, escurecimento, largura, mascara_fissura
from alinhamento import transformar


def area_comum(alin_c):
    v = np.ones((480, 640), np.uint8)
    for d in DATAS[1:]:
        v &= transformar(np.ones((480, 640), np.uint8), np.array(alin_c[d]['M']), cv2.INTER_NEAREST)
    return cv2.erode(v, np.ones((41, 41), np.uint8))


def tracado(D0, pontos_passagem):
    custo = 1.0 / (cv2.GaussianBlur(D0, (0, 0), 1.5) + 0.03)
    out = []
    for a, b in zip(pontos_passagem[:-1], pontos_passagem[1:]):
        r, _ = route_through_array(custo, (int(a[1]), int(a[0])), (int(b[1]), int(b[0])), fully_connected=True, geometric=True)
        out += [(x, y) for y, x in r][(1 if out else 0):]
    p = np.array(out, float); ker = np.ones(7) / 7
    return np.column_stack([np.convolve(p[:, 0], ker, 'valid'), np.convolve(p[:, 1], ker, 'valid')])


def extremidades(D0, area):
    m = mascara_fissura(D0, LIMIAR) & area
    ys, xs = np.nonzero(m); P = np.column_stack([xs, ys]).astype(float)
    mu = P.mean(0); _, _, vt = np.linalg.svd(P - mu, full_matrices=False); pr = (P - mu) @ vt[0]
    return P[np.argmin(pr)], P[np.argmax(pr)]


def normais(path, passo=8):
    n = []
    for i in range(len(path)):
        t = path[min(len(path) - 1, i + passo)] - path[max(0, i - passo)]; t = t / (np.linalg.norm(t) + 1e-9)
        n.append([-t[1], t[0]])
    return np.array(n)


def propor(mapa, alin, c, passagem=None):
    D0 = escurecimento(carregar(caminho(mapa, c, DATAS[0])))
    area = area_comum(alin[c])
    a, b = extremidades(D0, area)
    pp = [a, b] if not passagem else [tuple(b) if w is None else w for w in passagem]
    path = tracado(D0, pp); nrm = normais(path); L = len(path)
    pts = []
    for f in np.linspace(0.08, 0.92, N_PONTOS):
        i0 = int(f * (L - 1)); best = i0
        for di in range(30):
            ok = [i for i in (i0 + di, i0 - di) if 0 <= i < L and largura(D0, *path[i], nrm[i], LIMIAR, 6) > 0]
            if ok: best = ok[0]; break
        pts.append({'x': float(path[best][0]), 'y': float(path[best][1]), 'normal': nrm[best].tolist(), 'origem': 'automático'})
    return pts


if __name__ == '__main__':
    mapa = carregar_mapa(); alin = json.load(open(os.path.join(PASTA_DADOS, 'alinhamento.json')))
    out = {c: propor(mapa, alin, c) for c in sorted(mapa)}
    json.dump(out, open(os.path.join(PASTA_DADOS, 'pontos_propostos.json'), 'w'), indent=1)
    print('proposta gravada em dados/pontos_propostos.json')
