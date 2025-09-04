from pathlib import Path
import sys
from typing import Iterator

import requests

ROOT = Path(__file__).parent
SPECIES_CSV = ROOT / "sourcedata" / "species.csv"
PDF_DIR = ROOT / "pdfs"

URL_BASE = "https://www.birdlife.no/fuglekunnskap/fugleatlas/"
URL_FMT = URL_BASE + "index.php?vis=pdf&taxon_id={id}"

def main():
    species_txt = SPECIES_CSV.read_text()
    species_to_id = get_species_to_id(species_txt)
    for species, id in species_to_id.items():
        page_req = requests.get(URL_FMT.format(id=id))
        pdf_slug = locate_pdf(page_req.iter_lines())
        if pdf_slug is None:
            print(f"No PDF found for {species}", file=sys.stderr)
            continue
        pdf_url = URL_BASE + pdf_slug
        pdf_req = requests.get(pdf_url)
        if not pdf_req.ok:
            print(f"Downloading PDF for {species} reutrned status code {pdf_req.status_code}", file=sys.stderr)
        pdf_filepath = (PDF_DIR / f"{species}.pdf")
        pdf_filepath.write_bytes(pdf_req.content)

"""
Load CSV with species and convert to a mapping from species name to ID 
"""
def get_species_to_id(species_txt: str) -> dict[str, str]:
    lines = species_txt.splitlines()
    id_species_pairs = [line.split(",") for line in lines]
    species_to_id = { species: id for id, species in id_species_pairs }
    return species_to_id

"""
Locate relative url to the HTML

lines: iterator of something that can be converted to str
"""
def locate_pdf(lines) -> str | None:
    for line in lines:
        line = str(line)
        if (start_offset := line.find("<a href=\"pdf/")) != -1:
            start_offset += 9 # len("<a href=\"")
            snipped = line[start_offset:]
            if (end := snipped.find("\">")) != -1:
                snipped = snipped[:end]
                return snipped
            else:
                return None
    return None

if __name__ == "__main__":
    main()

