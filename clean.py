from pathlib import Path

import regex as re

from patches_common import PATCHES_COMMON, MONTHS, HEADINGS, COMMONLY_MERGED
from patches_single import PATCHES_SINGLE

ROOT = Path(__file__).parent
RAW_OCRS_DIR = ROOT / "raw_ocrs"
CLEANED_OCRS_DIR = ROOT / "cleaned"

def main():
    for raw_path in RAW_OCRS_DIR.iterdir():
        text = raw_path.read_text()
        text = common_transforms(text)
        text = do_single_patches(raw_path.name[:-4], text)
        text = text.strip() + "\n"
        (CLEANED_OCRS_DIR / raw_path.name).write_text(text)

def common_transforms(text: str) -> str:
    lines = text.splitlines()
    remove_page_number(lines)
    remove_vree_signature(lines)
    unmerge_words(lines)
    do_common_patches(lines)
    space_before_or_after_number(lines)
    lines = ensure_headings_separated(lines)
    lines = unwrap_lines(lines)
    do_common_patches(lines)
    lines = join_pagesplits(lines)
    return "\n\n".join(lines)

def space_before_or_after_number(lines: list[str]):
    for i in range(len(lines)):
        lines[i] = re.sub(r"(\d)([A-Za-z])", r"\1 \2", lines[i])
        lines[i] = re.sub(r"([A-Za-z])(\d)", r"\1 \2", lines[i])

def unmerge_words(lines: list[str]):
    for i in range(len(lines)):
        line = lines[i]
        for word in COMMONLY_MERGED:
            while word in line and " "+word not in line:
                line = line.replace(word, " "+word)
        lines[i] = line

def join_pagesplits(lines: list[str]) -> str:
    result = []
    for line in lines:
        if line and (line[0].islower() or line[0] == "(") and result:
            result[-1] = result[-1].rstrip() + " " + line
        else:
            result.append(line)
    return result

def do_single_patches(species: str, text: str) -> str:
    fixes = PATCHES_SINGLE.get(species)
    if fixes is None:
        return text
    for (bad, good) in fixes:
        if isinstance(bad, tuple):
            start, end = bad
            starti = text.find(start)
            if starti == -1:
                print(f"missing start of bad text in {species}: {start}")
            endi = text.find(end) + len(end)
            if endi < starti:
                print(f"missing end of bad text in {species}: {end}")
            text = text[:starti] + good + text[endi:]
        elif bad not in text:
            print(f"missing expected bad text in {species}: {bad}")
        else:
            text = text.replace(bad, good)
    return text

def remove_page_number(lines: list[str]):
    idx = None
    for i, line in enumerate(lines):
        try:
            int(line)
        except ValueError:
            continue
        idx = i
    if idx is None or idx < 1 or idx >= len(lines):
        return
    del lines[idx-1:idx+1]

def remove_vree_signature(lines: list[str]):
    idx = None
    for i, line in enumerate(lines):
        if line.startswith(("VEE", "VREE", "EE")):
            idx = i
            break
    if idx is None or idx < 1 or idx >= len(lines):
        return
    del lines[idx-1:idx+1]

def do_common_patches(lines: list[str]):
    for i, line in enumerate(lines):
        for (bad, good) in PATCHES_COMMON:
            while bad in line:
                line = line.replace(bad, good)
                lines[i] = line

def ensure_headings_separated(lines: list[str]) -> list[str]:
    out = []
    for i, line in enumerate(lines):
        out.append(line)
        if line in HEADINGS and lines[i+1].strip():
            out.append("")
    return out

def unwrap_lines(lines: list[str]) -> list[str]:
    out = []
    unwrapped = []
    ord0, ord9 = ord('0'), ord('9')
    lines.append("")
    for i, line in enumerate(lines):
        if line.strip() == "":
            if unwrapped:
                out.append("".join(unwrapped).strip())
            unwrapped = []
        if line.endswith("-"):
            next = lines[i+1]
            if next.startswith(("og", "eller")):
                # ['urte-', 'og buskrike kulturlandskap'] -> 'urte- og buskrike kulturlandskap'
                unwrapped.append(line)
                unwrapped.append(" ")
            elif ord0 <= ord(line[-2]) <= ord9:
                # ['1970-', 'tallet'] -> '1970-tallet'
                unwrapped.append(line)
            elif next and (next[0].isupper() or next.startswith(MONTHS)):
                # ['Sør-', 'Norge'] -> 'Sør-Norge'
                # ['april-', 'mai'] -> 'april-mai'
                unwrapped.append(line)
            else:
                # ['Tett-', 'heten av'] -> 'Tettheten av' 
                unwrapped.append(line[:-1])
        else:
            # ['som regel', 'plassert'] -> 'som regel plassert'
            unwrapped.append(line)
            unwrapped.append(" ")
    return out

if __name__ == "__main__":
    main()
