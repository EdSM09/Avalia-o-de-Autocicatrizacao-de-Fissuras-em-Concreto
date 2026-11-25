"""Gera as figuras do registro fotográfico (seção 4.3.5 do TCC): linha superior sem medidas e linha
inferior com os 5 pontos fixos e as aberturas medidas (mm), aos 0, 7, 14 e 21 dias.
Saída: figuras/<fissura>.jpg. Requer as medições de medir.py (dados/medicoes_pontos.csv)."""
import csv, json, os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from config import DATAS, PASTA_DADOS, RENOMEAR, DESCARTADAS
from fotos import carregar_mapa, caminho
from imagem import carregar
from medir import para_data

ROT = {'22-10-26': '0 d (22/10/2026)', '29-10-26': '7 d (29/10/2026)', '05-11-26': '14 d (05/11/2026)', '12-11-26': '21 d (12/11/2026)'}


def fonte(tam, negrito=True):
    for f in ['/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf', 'arialbd.ttf', 'Arial Bold.ttf', 'DejaVuSans-Bold.ttf']:
        try: return ImageFont.truetype(f, tam)
        except OSError: pass
    return ImageFont.load_default()


def marcar(img, pontos, larguras, M):
    im = img.copy(); rotulos = []
    for i, (p, w) in enumerate(zip(pontos, larguras), 1):
        q, v = para_data([p['x'], p['y']], p['normal'], M)
        for s in (1, -1):
            cv2.arrowedLine(im, tuple(np.int32(q + s * v * 30)), tuple(np.int32(q + s * v * 11)), (0, 0, 255), 2, tipLength=0.45)
        rotulos.append((q + v * 40, f'P{i}: {w:.3f}'.replace('.', ',')))
    pil = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(pil); f = fonte(19)
    for (x, y), t in rotulos:
        x = min(max(4, x - 30), 640 - 110); y = min(max(4, y - 8), 480 - 22)
        d.rectangle((x - 2, y - 1, x + d.textlength(t, font=f) + 2, y + 21), fill=(255, 255, 255)); d.text((x, y), t, font=f, fill=(200, 0, 0))
    return pil


if __name__ == '__main__':
    mapa = carregar_mapa()
    alin = json.load(open(os.path.join(PASTA_DADOS, 'alinhamento.json')))
    pontos = json.load(open(os.path.join(PASTA_DADOS, 'pontos_fixos.json'), encoding='utf-8'))
    med = {}
    for r in list(csv.reader(open(os.path.join(PASTA_DADOS, 'medicoes_pontos.csv'), encoding='utf-8-sig'), delimiter=';'))[1:]:
        med.setdefault(r[0], []).append([float(x.replace(',', '.')) for x in r[5:9]])
    os.makedirs('figuras', exist_ok=True)
    for c in pontos:
        if c in DESCARTADAS: continue
        fig = Image.new('RGB', (2046, 781), 'white'); d = ImageDraw.Draw(fig); fb = fonte(24)
        for k, dt in enumerate(DATAS):
            x0 = 66 + k * 483
            d.text((x0 + 240 - d.textlength(ROT[dt], font=fb) / 2, 6), ROT[dt], font=fb, fill='black')
            img = carregar(caminho(mapa, c, dt))
            fig.paste(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).resize((480, 360), Image.LANCZOS), (x0, 38))
            fig.paste(marcar(img, pontos[c], [w[k] for w in med[c]], alin[c][dt]['M']).resize((480, 360), Image.LANCZOS), (x0, 401))
        for t, y in [('Sem medidas', 38), ('Com medidas', 401)]:
            r = Image.new('RGBA', (int(d.textlength(t, font=fonte(22))) + 6, 32), (255, 255, 255, 0))
            ImageDraw.Draw(r).text((3, 2), t, font=fonte(22), fill='black'); r = r.rotate(90, expand=True)
            fig.paste(r, (33 - r.width // 2, y + 180 - r.height // 2), r)
        fig.save(os.path.join('figuras', RENOMEAR.get(c, c) + '.jpg'), quality=92)
    print('figuras geradas em figuras/')
