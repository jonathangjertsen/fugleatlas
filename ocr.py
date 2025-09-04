from pathlib import Path
import sys

import pdf2image
import pytesseract

ROOT = Path(__file__).parent
SPECIES_CSV = ROOT / "sourcedata" / "species.csv"
PDF_DIR = ROOT / "pdfs"
RAW_OCRS_DIR = ROOT / "raw_ocrs"

def main():
    for pdf_path in PDF_DIR.iterdir():
        if pdf_path.suffix != ".pdf":
            continue
        text_file_path = (RAW_OCRS_DIR / (pdf_path.name[:-4]+".txt"))
        if text_file_path.exists():
            print(f"Already exists: {text_file_path}")
            continue
        try:
            pages = pdf2image.convert_from_path(pdf_path)
        except Exception as e:
            print(f"Exception converting {pdf_path} to image: {e}", file=sys.stderr)
            continue
        if len(pages) != 2:
            print(f"Expect exactly 2 pages")
        main_page = pages[0]
        text = pytesseract.image_to_string(main_page, lang="nor")
        text_file_path.write_text(text)

if __name__ == "__main__":
    main()
