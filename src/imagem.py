"""Núcleo da medição: mapa de escurecimento e largura da fissura ao longo de um perfil."""
import cv2
import numpy as np


def carregar(caminho):
    """Lê a foto e a padroniza em 640 x 480 píxeis (uma foto do dia 0 foi salva em 870 x 652)."""
    im = cv2.imread(caminho)
    if im is None:
        raise FileNotFoundError(caminho)
    if im.shape[:2] != (480, 640):
        im = cv2.resize(im, (640, 480), interpolation=cv2.INTER_AREA)
    return im


def escurecimento(img):
    """Escurecimento de cada píxel em relação ao fundo claro local
    (0 = fundo, 1 = preto). Fundo estimado por fechamento morfológico
    (disco de 91 px), que remove as feições escuras."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (91, 91))
    fundo = cv2.morphologyEx(cv2.GaussianBlur(g, (0, 0), 2), cv2.MORPH_CLOSE, k)
    fundo = cv2.GaussianBlur(fundo, (0, 0), 15)
    return np.clip((fundo - g) / np.maximum(fundo, 1), 0, 1)


def perfil(D, cx, cy, direcao, meio=45, passo=0.25):
    """Escurecimento ao longo da reta que passa por (cx, cy) na direção dada
    (interpolação bilinear)."""
    t = np.arange(-meio, meio + passo, passo)
    xs = (cx + t * direcao[0]).astype(np.float32).reshape(1, -1)
    ys = (cy + t * direcao[1]).astype(np.float32).reshape(1, -1)
    v = cv2.remap(D, xs, ys, cv2.INTER_LINEAR, borderValue=0)[0]
    return t, v


def largura(D, cx, cy, normal, limiar, busca):
    """Largura (px) do trecho contínuo com escurecimento >= limiar que contém
    o píxel mais escuro a até `busca` px do ponto, na direção normal à fissura.
    Bordas por interpolação linear entre amostras. Retorna 0 quando não há
    trecho escuro (abertura preenchida)."""
    t, v = perfil(D, cx, cy, normal)
    janela = np.abs(t) <= busca
    k = int(np.argmax(np.where(janela, v, -1)))
    if v[k] < limiar:
        return 0.0
    i = k
    while i > 0 and v[i - 1] >= limiar:
        i -= 1
    j = k
    while j < len(v) - 1 and v[j + 1] >= limiar:
        j += 1

    def borda(a, b):
        if v[a] == v[b]:
            return t[a]
        return t[a] + (limiar - v[a]) * (t[b] - t[a]) / (v[b] - v[a])
    lo = borda(i - 1, i) if i > 0 else t[i]
    hi = borda(j, j + 1) if j < len(v) - 1 else t[j]
    return float(hi - lo)


def normal_local(D, cx, cy, r=10):
    """Direção normal à fissura pelo tensor de estrutura do mapa de escurecimento."""
    gx = cv2.Sobel(D, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(D, cv2.CV_32F, 0, 1, ksize=3)
    x0, x1 = int(max(0, cx - r)), int(min(D.shape[1], cx + r + 1))
    y0, y1 = int(max(0, cy - r)), int(min(D.shape[0], cy + r + 1))
    jxx = (gx[y0:y1, x0:x1] ** 2).sum(); jyy = (gy[y0:y1, x0:x1] ** 2).sum()
    jxy = (gx[y0:y1, x0:x1] * gy[y0:y1, x0:x1]).sum()
    ang = 0.5 * np.arctan2(2 * jxy, jxx - jyy)
    return [float(np.cos(ang)), float(np.sin(ang))]


def mascara_fissura(D, limiar=0.40, comp_min=40):
    """Componentes escuros alongados (fissura), descartando poros arredondados."""
    m = (D >= limiar).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    out = np.zeros_like(m)
    for k in range(1, n):
        w, h = st[k, 2], st[k, 3]
        if max(w, h) >= comp_min and st[k, 4] / (w * h + 1) < 0.6:
            out[lab == k] = 1
    return out
