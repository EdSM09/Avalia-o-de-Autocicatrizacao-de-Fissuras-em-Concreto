"""Localiza, para cada fissura e data, a foto sem cotas e a foto com cotas do HiView."""
import glob, json, os, re
import cv2
from config import PASTA_FOTOS, PASTA_DADOS, DATAS


def codigo(nome):
    m = re.match(r'[Tt](05|5|7,5|10)[Ff](\d\d)', nome)
    traco = {'05': 'T5', '5': 'T5', '7,5': 'T7,5', '10': 'T10'}[m.group(1)]
    return f'{traco}F{m.group(2)}'


def pixels_anotacao(caminho):
    """Conta píxeis amarelos (rótulos) do HiView: a foto com mais anotação é a cotada."""
    hsv = cv2.cvtColor(cv2.imread(caminho), cv2.COLOR_BGR2HSV)
    return int(((hsv[..., 0] > 20) & (hsv[..., 0] < 40) & (hsv[..., 1] > 120) & (hsv[..., 2] > 120)).sum())


def mapear():
    out = {}
    for d in DATAS:
        for f in sorted(glob.glob(os.path.join(PASTA_FOTOS, d, '*.jpg'))):
            out.setdefault(codigo(os.path.basename(f)), {}).setdefault(d, []).append((os.path.basename(f), pixels_anotacao(f)))
    res = {}
    for c, v in sorted(out.items()):
        res[c] = {}
        for d, fs in v.items():
            fs = sorted(fs, key=lambda t: t[1])
            res[c][d] = {'sem_cotas': fs[0][0], 'com_cotas': fs[-1][0]}
    return res


def carregar_mapa():
    return json.load(open(os.path.join(PASTA_DADOS, 'fotos.json'), encoding='utf-8'))


def caminho(mapa, c, d, tipo='sem_cotas'):
    return os.path.join(PASTA_FOTOS, d, mapa[c][d][tipo])


if __name__ == '__main__':
    m = mapear()
    json.dump(m, open(os.path.join(PASTA_DADOS, 'fotos.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(len(m), 'fissuras mapeadas')
