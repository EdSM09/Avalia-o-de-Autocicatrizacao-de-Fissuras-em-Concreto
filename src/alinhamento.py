"""Sobreposição das fotos de 7, 14 e 21 dias à foto de 0 dias de cada fissura.

Para cada data: (1) correspondência de pontos característicos (SIFT) e transformação de similaridade
(rotação, translação e escala) estimada por RANSAC, direta ou encadeada por uma data intermediária;
(2) refinamento por correlação (ECC) sobre o mapa de escurecimento; (3) escolha da transformação
que melhor sobrepõe o traçado da fissura (menor distância mediana entre esqueletos).
Observação: o RANSAC tem componente aleatório; por isso, as transformações usadas no TCC estão
gravadas em dados/alinhamento.json e são as que medir.py utiliza."""
import json, os, sys
import cv2
import numpy as np
from skimage.morphology import skeletonize
from config import DATAS, PASTA_DADOS
from fotos import carregar_mapa, caminho
from imagem import carregar, escurecimento, mascara_fissura

sift = cv2.SIFT_create(5000)


def prep(im):
    return cv2.createCLAHE(3.0, (8, 8)).apply(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY))


def sift_similaridade(a, b):
    ka, da = sift.detectAndCompute(a, None); kb, db = sift.detectAndCompute(b, None)
    if da is None or db is None or len(ka) < 5 or len(kb) < 5:
        return None, 0
    m = cv2.BFMatcher().knnMatch(da, db, k=2)
    bons = [x[0] for x in m if len(x) == 2 and x[0].distance < 0.8 * x[1].distance]
    if len(bons) < 6:
        return None, 0
    pa = np.float32([ka[x.queryIdx].pt for x in bons]); pb = np.float32([kb[x.trainIdx].pt for x in bons])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=4, maxIters=10000)
    return (None, 0) if M is None else (M, int(inl.sum()))


def transformar(img, M, interp=cv2.INTER_LINEAR):
    return cv2.warpAffine(img, M, (640, 480), flags=interp, borderValue=0)


def compor(M2, M1):
    return (np.vstack([M2, [0, 0, 1]]) @ np.vstack([M1, [0, 0, 1]]))[:2]


def distancia_tracado(mA_em_B, mB):
    sa = skeletonize(mA_em_B > 0); sb = skeletonize(mB > 0)
    if sa.sum() < 20 or sb.sum() < 20:
        return 99.0
    dt = cv2.distanceTransform((1 - sb).astype(np.uint8), cv2.DIST_L2, 5)
    return float(np.median(dt[sa]))


def refinar_ecc(Dd, D0, M):
    Minv = cv2.invertAffineTransform(M)
    a = cv2.GaussianBlur(D0, (0, 0), 2.5); b = cv2.GaussianBlur(Dd, (0, 0), 2.5)
    try:
        _, Wf = cv2.findTransformECC(a, b, Minv.astype(np.float32), cv2.MOTION_AFFINE,
                                     (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), None, 5)
    except cv2.error:
        return None
    return cv2.invertAffineTransform(Wf)


def alinhar(mapa, c):
    ims = {d: carregar(caminho(mapa, c, d)) for d in DATAS}
    Ds = {d: escurecimento(ims[d]) for d in DATAS}
    ms = {d: mascara_fissura(Ds[d]) for d in DATAS}
    P = {d: prep(ims[d]) for d in DATAS}
    par = {(a, b): sift_similaridade(P[a], P[b]) for i, a in enumerate(DATAS) for b in DATAS[:i]}
    res = {DATAS[0]: {'M': [[1, 0, 0], [0, 1, 0]], 'como': 'referência'}}
    for i, d in enumerate(DATAS[1:], 1):
        cands = []
        M, n = par[(d, DATAS[0])]
        if M is not None: cands.append(('direto', M))
        for j in range(1, i):
            M1, _ = par[(d, DATAS[j])]
            if M1 is not None and res.get(DATAS[j]):
                cands.append((f'via {DATAS[j]}', compor(np.array(res[DATAS[j]]['M']), M1)))
        melhor = None
        for como, M in cands:
            for M2, tag in [(M, ''), (refinar_ecc(Ds[d], Ds[DATAS[0]], M), '+ECC')]:
                if M2 is None: continue
                s = float(np.hypot(M2[0][0], M2[1][0]))
                if not 0.9 < s < 1.1: continue
                dist = distancia_tracado(transformar(ms[d], np.array(M2), cv2.INTER_NEAREST), ms[DATAS[0]])
                if melhor is None or dist < melhor['dist']:
                    melhor = {'M': np.array(M2).tolist(), 'como': como + tag, 'dist': dist, 'escala': s}
        res[d] = melhor
    return res


if __name__ == '__main__':
    mapa = carregar_mapa()
    saida = os.path.join(PASTA_DADOS, sys.argv[1] if len(sys.argv) > 1 else 'alinhamento_novo.json')
    out = {c: alinhar(mapa, c) for c in sorted(mapa)}
    json.dump(out, open(saida, 'w'), indent=1)
    print('gravado em', saida)
