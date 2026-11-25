"""Validação: compara a largura medida pelo algoritmo com as leituras do HiView nas fotos cotadas.

Em cada foto com cotas, localiza as barras verdes de medição do HiView e lê o valor do rótulo amarelo
por OCR (Tesseract). Descarta leituras cujo comprimento da barra não confere com o valor lido (erro de OCR).
No mesmo local, mede a largura na foto sem cotas da mesma sessão, na direção da barra.
Requer o programa tesseract instalado."""
import json, os, re, subprocess, tempfile
import cv2
import numpy as np
from config import DATAS, PASTA_DADOS, MM_POR_PIXEL, LIMIAR
from fotos import carregar_mapa, caminho
from imagem import carregar, escurecimento, largura


def mascaras(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    verde = ((hsv[..., 0] > 45) & (hsv[..., 0] < 85) & (hsv[..., 1] > 120) & (hsv[..., 2] > 100)).astype(np.uint8)
    amarelo = ((hsv[..., 0] > 20) & (hsv[..., 0] < 40) & (hsv[..., 1] > 100) & (hsv[..., 2] > 120)).astype(np.uint8)
    return verde, amarelo


def ocr(recorte):
    big = 255 - cv2.resize(recorte, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC) * 255
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
        cv2.imwrite(tf.name, big)
        t = subprocess.run(['tesseract', tf.name, '-', '--psm', '7', '-c', 'tessedit_char_whitelist=0123456789.m'],
                           capture_output=True, text=True).stdout
    os.unlink(tf.name)
    m = re.search(r'(\d)\.(\d{4,5})', t.replace(' ', ''))
    return float(m.group(0)) if m else None


def barras(img):
    g, y = mascaras(img)
    n, lab, st, cen = cv2.connectedComponentsWithStats(cv2.dilate(g, np.ones((3, 3), np.uint8)))
    ny, laby, sty, ceny = cv2.connectedComponentsWithStats(cv2.dilate(y, np.ones((5, 9), np.uint8)))
    out = []
    for k in range(1, n):
        if st[k, 4] < 8: continue
        pts = np.column_stack(np.where((lab == k) & (g > 0)))[:, ::-1].astype(float)
        if len(pts) < 6: continue
        mu = pts.mean(0); _, _, vt = np.linalg.svd(pts - mu); ax = vt[0]; pr = (pts - mu) @ ax
        melhor = None
        for j in range(1, ny):
            if sty[j, 2] < 25 or sty[j, 3] > 30: continue
            dist = np.hypot(sty[j, 0] - cen[k][0], ceny[j][1] - cen[k][1])
            if melhor is None or dist < melhor[0]: melhor = (dist, j)
        if not melhor or melhor[0] >= 120: continue
        x0, y0, w, h = sty[melhor[1], :4]
        val = ocr(y[max(0, y0 - 2):y0 + h + 2, max(0, x0 - 2):x0 + w + 2])
        out.append({'cx': float(cen[k][0]), 'cy': float(cen[k][1]), 'eixo': [float(ax[0]), float(ax[1])],
                    'comp_px': float(pr.max() - pr.min()), 'valor_mm': val})
    return out


if __name__ == '__main__':
    mapa = carregar_mapa(); P = []; O = []
    for c in sorted(mapa):
        for d in DATAS:
            cot = cv2.imread(caminho(mapa, c, d, 'com_cotas'))
            if cot.shape[:2] != (480, 640): continue          # foto redimensionada: posições não correspondem
            D = escurecimento(carregar(caminho(mapa, c, d)))
            for b in barras(cot):
                v = b['valor_mm']
                if v is None or not 0.015 < v < 0.5: continue
                if abs(b['comp_px'] - (v / 0.0065 + 2.9)) >= 4: continue   # barra incompatível com o valor lido
                P.append(largura(D, b['cx'], b['cy'], b['eixo'], LIMIAR, 12) * MM_POR_PIXEL); O.append(v)
    P, O = np.array(P), np.array(O); e = P - O
    print(f'leituras comparadas: {len(O)}')
    print(f'correlação: {np.corrcoef(P, O)[0, 1]:.3f}  diferença média: {e.mean():+.4f} mm  '
          f'diferença absoluta mediana: {np.median(np.abs(e)):.4f} mm')
