# Medição da abertura de fissuras por processamento digital de imagens

Código usado no TCC *"Autocicatrização de concretos com adição de sílica ativa"* (IFPA, 2026)
para medir a abertura das fissuras nas fotos da lupa digital e calcular o índice de fechamento
geométrico (IC) entre 0 e 21 dias de cura submersa (seções 3.2.4, 3.2.5 e 4.3 e Apêndice A do TCC).

O código foi desenvolvido com auxílio da ferramenta de inteligência artificial Claude (Anthropic).
Os critérios de medição (o que conta como fissura aberta, a posição dos pontos e a exclusão de
fissuras) foram definidos e conferidos visualmente pelos autores.

## Método

1. **Fotos.** Para cada fissura e data (22/10, 29/10, 05/11 e 12/11/2026 = 0, 7, 14 e 21 dias), foram
   obtidas uma foto sem cotas e uma com as cotas do HiView. A medição usa só as fotos sem cotas.
2. **Alinhamento** (`alinhamento.py`). As fotos de 7, 14 e 21 dias são sobrepostas à de 0 dias por
   correspondência de pontos característicos da superfície (SIFT + RANSAC, transformação de similaridade),
   com refinamento por correlação (ECC). O fator de escala entre datas ficou entre 0,98 e 1,04, o que
   confirma a mesma ampliação nas quatro sessões.
3. **Pontos fixos** (`pontos.py`). Cinco pontos (P1 a P5) ao longo do traçado da fissura, no trecho comum
   às quatro fotos, com a direção normal à fissura. A proposta automática foi conferida e ajustada pelos
   autores; os pontos finais estão em `dados/pontos_fixos.json` (campo `origem`).
4. **Medição** (`imagem.py`, `medir.py`). Em cada ponto, a abertura é a largura, na direção normal, do
   trecho com escurecimento ≥ 40% em relação ao fundo claro local. Material cinza ou esbranquiçado dentro
   da fissura conta como preenchimento. Conversão: 0,0064 mm/píxel. A abertura da fissura (w) é a média
   dos cinco pontos.
5. **Índice de fechamento.** IC = (w0 − w21) / w0 × 100. Variação de até 0,013 mm (≈ 2 píxeis) é
   considerada não detectável (ND).

## Estrutura

```
src/config.py             parâmetros (calibração, limiar, datas, renomeação das fissuras)
src/imagem.py             núcleo: mapa de escurecimento e largura ao longo do perfil
src/fotos.py              identifica a foto sem cotas e a com cotas de cada fissura/data
src/alinhamento.py        sobreposição das fotos de cada fissura
src/pontos.py             proposta automática dos 5 pontos fixos
src/medir.py              medição nos pontos fixos, IC e classificação  -> dados/*.csv
src/validacao_hiview.py   comparação com as leituras do HiView (requer Tesseract OCR)
src/figuras.py            figuras "sem medidas / com medidas" do registro fotográfico
dados/fotos.json          nomes dos arquivos de foto por fissura e data
dados/alinhamento.json    transformações usadas no TCC (data -> 0 dias)
dados/pontos_fixos.json   pontos P1 a P5 usados no TCC (quadro da foto de 0 dias)
dados/medicoes_pontos.csv     aberturas em cada ponto e data (mm)
dados/resultados_fissuras.csv w0, w21, Δw, IC e tipo de fechamento por fissura
```

## Como executar

```bash
pip install -r requirements.txt
export PASTA_FOTOS=/caminho/para/REGISTRO_FOTOGRAFICO   # subpastas 22-10-26, 29-10-26, 05-11-26, 12-11-26
python src/medir.py                  # reproduz as Tabelas 8 e 9 do TCC (limiar 0,40)
python src/medir.py --limiar 0.35    # análise de sensibilidade (também 0.45)
python src/validacao_hiview.py       # validação com o HiView
python src/figuras.py                # figuras do registro fotográfico
```

Para refazer todo o processo a partir das fotos: `python src/fotos.py`, `python src/alinhamento.py`
e `python src/pontos.py`. Como o RANSAC tem componente aleatório, um novo alinhamento pode diferir
em fração de píxel do gravado; por isso `medir.py` usa `dados/alinhamento.json` e `dados/pontos_fixos.json`,
o que reproduz exatamente os 500 valores medidos (25 fissuras × 5 pontos × 4 datas).

## Resultados de referência

| Limiar | T5 (n = 8) | T7,5 (n = 9) | T10 (n = 7) |
|---|---|---|---|
| 0,35 | 44,6% | 57,9% | 55,3% |
| **0,40 (TCC)** | **48,3%** | **61,8%** | **59,3%** |
| 0,45 | 52,4% | 62,2% | 61,0% |

Validação com 137 leituras do HiView nos mesmos locais: correlação 0,855, diferença média +0,005 mm,
diferença absoluta mediana 0,021 mm.

## Observações

- **Nomes das fissuras.** As fotos usam a numeração original. A fissura T10F04 do registro foi descartada,
  e as seguintes foram renumeradas no TCC: T10F05 → T10F04, T10F06 → T10F05, T10F07 → T10F06,
  T10F08 → T10F07 (`config.RENOMEAR`). Os CSV trazem as duas numerações.
- **Ajustes manuais** (`origem` em `pontos_fixos.json`): pontos P1 a P4 da T5F03 (e o percurso dessa
  fissura através do poro), P3 da T10F08 (T10F07 no TCC) e P1 da T10F04 (descartada). Nas fissuras T5F09
  e T10F08, o traçado é o da primeira versão automática, porque a segunda se desviou para um poro.
- **Foto redimensionada.** A foto sem cotas da T5F02 em 22/10 foi salva em 870 × 652 px e é reduzida
  para 640 × 480 px na leitura.
- As fotos não estão incluídas neste pacote. Para que a banca possa reproduzir a medição, inclua a pasta
  `REGISTRO_FOTOGRAFICO` no repositório ou indique onde ela pode ser obtida.
