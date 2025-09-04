# Tekstscanning av Norsk FugleAtlas

Dette repoet inneholder skript for å laste ned PDFer fra https://www.birdlife.no/fuglekunnskap/fugleatlas/ og konvertere dem til tekstfiler.

1. `download.py` laster ned alle PDF-filene
2. `ocr.py` konverterer PDF-filene til tekstformat
3. `clean.py` renser opp tekstfilene

```mermaid
flowchart TD
    sourcedata -->|download.py| pdfs
    pdfs -->|ocr.py| raw_ocrs
    raw_ocrs -->|clean.py| cleaned
```

## Detaljer om skriptene

### `download.py`

Laster ned filer fra birdlife.no til mappen `pdfs`.

Jeg hentet manuelt ut listen over arter og tilhørende ID ved å se på HTML-kilden for "velg art" på nettsiden. Listen er å finne i `sourcedata/species.csv`, det er også denne som brukes av `download.py`

Skriptet krever pakken `requests`

### `ocr.py`

Kjører tekstgjenkjenning på PDF-filene og oppretter tekstfiler i mappen `raw_ocrs`.

Tekstgjennkjenning (OCR) krever installasjon av tesseract med norsk språkpakke.

https://tesseract-ocr.github.io/tessdoc/Installation.html

Hvis du har Linux med apt:

```sh
sudo apt install tesseract-ocr libtesseract-dev tesseract-ocr-nor
```

I tillegg kreves Python-pakkene `pdf2image` og `pytesseract`.

### `clean.py`

OCR gjør det meste riktig, men det er noen feil, for eksempel blir `fôr` konsekvent til `för`. Dette skriptet finner slike ting og fikser. Her gjøres også manuelle fikser for ting jeg fant da jeg leste gjennom filene.

