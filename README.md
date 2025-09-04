1. Jeg hentet manuelt ut listen over arter og tilhørende ID ved å se på HTML-kilden for "velg art" på https://www.birdlife.no/fuglekunnskap/fugleatlas/. Listen er å finne i sourcedata/species.csv
2. `download.py` laster ned alle PDF-filene til pdfs/
3. `ocr.py` konverterer pdf til tekstformat (bruker tekstgjenkjenningsprogrammet Tessaract)

# Tesseract

OCR krever installasjon av tesseract med norsk språkpakke

https://tesseract-ocr.github.io/tessdoc/Installation.html

Linux med apt: `sudo apt install tesseract-ocr libtesseract-dev tesseract-ocr-nor`
