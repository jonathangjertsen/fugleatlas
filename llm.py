from pathlib import Path
import os

import openai

MODEL = "gpt-4.1-mini"
AREA = "Oslo og omegn"

ROOT = Path(__file__).parent
TXT_DIR = ROOT / "cleaned"
JSON_DIR = ROOT / "raw_llm"

def main():
    # TODO: do em in parallel
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    for txt_path in TXT_DIR.iterdir():
        if not txt_path.name.endswith(".txt"):
            print(f"Skipped {txt_path}")
            continue
        json_file = JSON_DIR / (txt_path.name[:-4] + ".json")
        if json_file.exists():
            print(f"Skipped {json_file} (exists)")
            continue
        text = txt_path.read_text()
        response = llm_extract(client, text)
        json_file.write_text(response)
        print(f"Created {json_file}")

def llm_extract(client: openai.OpenAI, text: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[SYSTEM_MSG, {"role": "user", "content": INSTRUCTION}, {"role": "user", "content": text}],
    )
    content = response.choices[0].message.content
    return content


SYSTEM_MSG = {
    "role": "system",
    "content": "Du er en assistent som kun returnerer gyldig JSON. Følg skjemaet og dato-intervallformatet."
}

INSTRUCTION = f"""
Du får en norsk artikkel som beskriver en fugleart i Norge. Artikkelen har avsnitt om utbredelse, hekkebiologi og trekkforhold.

Du skal ekstrahere et JSON-output som så skal brukes i en visualisering av fuglers hekketid i ett bestemt område: {AREA}.

Artikkelen beskriver forhold i hele Norge, så du må tolke hvordan forholdene er i det nevnte området. For eksempel: hvis artikkelen oppgir forholdene i Finnmark og forholdene i {AREA}, så må du bruke datoene som er oppgitt for {AREA}. 

Ekstraher følgende felter og svar kun med gyldig JSON (ingen forklarende tekst). Alle tidspunkt oppgis som intervaller: `{{ "earliest": "01-05", "latest": "03-20"}}`

- norwegian: fuglens norske navn
- latin: fuglens latinske navn
- migratoriness: {{resident, partial_migrant, migrant}}
- arrival: tidspunkt for ankomst til Norge ved trekk
- departure: tidspunkt for avreise fra Norge ved trekk
- eggs_laid: tidspunkt for egglegging (hvis flere kull skal "earliest" referere til første kull, og "latest" referere til siste kull)
- eggs_hatch: tidspunkt når egg klekkes (hvis flere kull, gjør det samme som for eggs_laid)
- chicks_fledge: tidspunkt når ungene er flyvedyktige og/eller selvstendige
- remarks: kommentarer på norsk som påpeker særlige forhold, uklarheter i teksten eller andre ting som kan være av nytte når resultatet skal gjennomgås manuelt. Må være så kortfattet som mulig, gjerne helt tomt dersom det ikke var noe problemer med å ekstrahere feltene.

Hvis informasjon mangler i teksten, bruk null og legg til en kommentar i remarks-feltet.

Eksempel (inkluderer ikke hele teksten)
Tekst: "I siste halvdel av april og i mai bygger sothøna reir... De aller fleste individene trekker imidlertid ut av landet senhøstes."
Output:
{{
  "norwegian": "Sothøne",
  "latin": "Fulica atra",
  "migratoriness": "partial_migrant",
  "arrival": {{ "earliest": "04-15", "latest": "05-01" }},
  "departure": {{ "earliest": "10-15", "latest": "11-30" }},
  "eggs_laid": {{ "earliest": "04-20", "latest": "05-31" }},
  "eggs_hatch": {{ "earliest": "05-15", "latest": "06-20" }},
  "chicks_fledge": {{ "earliest": "06-01", "latest": "07-31" }},
  "remarks": null
}}
"""

if __name__ == "__main__":
    main()
