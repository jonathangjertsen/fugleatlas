from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from matplotlib import pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Rectangle
from matplotlib.ticker import FixedLocator
import datetime as dt
import json
import numpy as np

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
PRESENTATION_CSV = ROOT / "presentationdata" / "presentation.csv"

@dataclass
class SpeciesConfig:
    name: str

    @classmethod
    def from_line(cls, line: str):
        name, = line.split(",")
        return cls(
            name=line,
        )

@dataclass
class TimeRange:
    earliest: str
    latest: str

    @classmethod
    def from_json(cls, json: dict):
        if json is None:
            return None
        return cls(**json)

@dataclass
class SpeciesData:
    norwegian: str
    latin: str
    migratoriness: str
    remarks: str
    category: str
    arrival: TimeRange | None
    departure: TimeRange | None
    in_norway: TimeRange | None
    eggs_laid: TimeRange | None
    eggs_hatch: TimeRange | None
    eggs: TimeRange | None
    chicks_fledge: TimeRange | None
    chicks: TimeRange | None

    def sort_key(self):
        for attrib in ("eggs_laid", "eggs_hatch", "chicks_fledge", "arrival", "departure"):
            if (attr := getattr(self, attrib)) is not None:
                return mmdd_to_doy(attr.earliest)
        return 1000

    @classmethod
    def from_json(cls, json: dict):
        arrival=TimeRange.from_json(json["arrival"])
        departure=TimeRange.from_json(json["departure"])
        eggs_laid=TimeRange.from_json(json["eggs_laid"])
        eggs_hatch=TimeRange.from_json(json["eggs_hatch"])
        chicks_fledge=TimeRange.from_json(json["chicks_fledge"])

        if arrival is not None and departure is not None:
            in_norway = TimeRange(earliest=arrival.earliest, latest=departure.latest)
        else:
            in_norway = None

        if eggs_laid is not None and eggs_hatch is not None:
            eggs = TimeRange(earliest=eggs_laid.earliest, latest=eggs_hatch.latest)
        else:
            eggs = None

        if eggs_hatch is not None and chicks_fledge is not None:
            chicks = TimeRange(earliest=eggs_hatch.earliest, latest=chicks_fledge.latest)
        else:
            chicks = None

        return cls(
            norwegian=json["norwegian"],
            latin=json["latin"],
            migratoriness=json["migratoriness"],
            remarks=json["remarks"],
            category=json.get("category", None),
            arrival=arrival,
            departure=departure,
            in_norway=in_norway,
            eggs_laid=eggs_laid,
            eggs_hatch=eggs_hatch,
            eggs=eggs,
            chicks_fledge=chicks_fledge,
            chicks=chicks,
        )

def get_species_selection() -> list[SpeciesConfig]:
    lines = PRESENTATION_CSV.read_text().strip().splitlines()
    return [
        SpeciesConfig.from_line(line)
        for line in lines
    ]

def get_species_data(species_sel: list[SpeciesConfig]) -> SpeciesData:
    return [
        SpeciesData.from_json(
            json.loads((DATA_DIR / (species.name + ".json")).read_text())
        )
        for species in species_sel
    ]


def mmdd_to_doy(mmdd):
    m, d = map(int, mmdd.split("-"))
    return (dt.date(2024, m, d) - dt.date(2024, 1, 1)).days + 1

def phase_range(phase):
    return mmdd_to_doy(phase.earliest), mmdd_to_doy(phase.latest)

def draw_fade_bar(ax, x0, x1, y, h, color, fade_in=None, fade_out=None, gamma_in=1.0, gamma_out=1.0, zorder=2.5):
    w = max(2, int(np.ceil(x1 - x0)))
    r, g, b = mpl.colors.to_rgb(color)
    alpha = np.ones(w)

    if fade_in:
        a0, a1 = fade_in
        i0 = max(0, int(np.floor(a0 - x0)))
        i1 = min(w, int(np.ceil(a1 - x0)))
        if i1 > i0:
            t = np.linspace(0, 1, i1 - i0, endpoint=True)
            a = t**gamma_in
            alpha[:i0] = 0
            alpha[i0:i1] = a
            if i1 < w:
                alpha[i1:] = 1

    if fade_out:
        d0, d1 = fade_out
        j0 = max(0, int(np.floor(d0 - x0)))
        j1 = min(w, int(np.ceil(d1 - x0)))
        if j1 > j0:
            t = np.linspace(0, 1, j1 - j0, endpoint=True)
            a = 1 - t**gamma_out
            alpha[j0:j1] = np.minimum(alpha[j0:j1], a)
            if j1 < w:
                alpha[j1:] = 0

    img = np.zeros((1, w, 4))
    img[..., 0] = r
    img[..., 1] = g
    img[..., 2] = b
    img[..., 3] = alpha
    ax.imshow(img, extent=(x0, x1, y - h/2, y + h/2), origin="lower", aspect="auto", interpolation="nearest", zorder=zorder)

@dataclass
class PlotConfig:
    ready: bool = False

    # Figure sizing
    fig_w: int = 18                          # Figure width in inches
    min_fig_h: int = 8                       # Minimum figure height in inches
    max_fig_h: int = 120                     # Maximum figure height in inches

    # Vertical layout
    row_gap_small: float = 1.2               # Row spacing for few species
    row_gap_medium: float = 1.0              # Row spacing for medium number of species
    row_gap_large: float = 0.9               # Row spacing for many species

    # Fonts
    font_large: int = 14                     # Font size for species labels (few species)
    font_medium: int = 11                    # Font size for species labels (medium species count)
    font_small: int = 9                      # Font size for species labels (many species)
    phase_font: int = 10                     # Font size for phase labels

    # Bar layout
    band_height_frac: float = 0.9            # Fraction of row used for bars
    bar_gap_frac: float = 0.08               # Fraction of row gap used as spacing between bars

    # Label positioning
    label_x_offset: int = 6                  # X-offset in days for species labels from y-axis

    # Transparency
    label_box_alpha: float = 0.65            # Opacity of species label background
    phase_box_alpha: float = 0.7             # Opacity of phase label background
    background_alpha_even: float = 0.06      # Shading for even rows
    background_alpha_odd: float = 0.18       # Shading for odd rows
    month_bg_alpha: float = 0.03             # Shading for alternating months

    # Styling
    line_width: float = 1.2                  # Width of plot borders
    category_bg_alpha: float = 0.14
    category_font: int = 14

    # Global style settings for matplotlib
    rcparams: dict = field(default_factory=lambda: {
        "font.size": 15,
        "font.family": "DejaVu Sans",
        "axes.titlesize": 22,
        "axes.labelsize": 14,
        "svg.fonttype": "none"
    })

    # Phases
    phases: list = field(default_factory=lambda: ["in_norway", "eggs", "chicks"])
    phase_labels: dict = field(default_factory=lambda: {
        "in_norway": "Hos oss",
        "eggs": "Egg",
        "chicks": "Fugleunger"
    })
    phase_colors: dict = field(default_factory=lambda: {
        "in_norway": "#B2DCDC",
        "eggs": "#F6D265",
        "chicks": "#C88397"
    })

    # Month names in Norwegian
    months_no: list = field(default_factory=lambda: [
        "januar","februar","mars","april","mai","juni",
        "juli","august","september","oktober","november","desember"
    ])


def plot_species(grouped: OrderedDict[str, list[SpeciesData]], cfg: PlotConfig = PlotConfig()):
    plt.rcParams.update(cfg.rcparams)

    n = sum(len(v) + 1 for v in grouped.values())
    row_gap = cfg.row_gap_small if n <= 25 else (cfg.row_gap_medium if n <= 80 else cfg.row_gap_large)
    fig_h = max(cfg.min_fig_h, min(3 + n * 0.6, cfg.max_fig_h))

    fig, ax = plt.subplots(figsize=(cfg.fig_w, fig_h), constrained_layout=True)
    fig.set_constrained_layout_pads(w_pad=0.2, h_pad=1.5, hspace=0.15)

    months = list(range(1, 13))
    month_edges = [(dt.date(2024, m, 1) - dt.date(2024, 1, 1)).days + 1 for m in months] + [366]
    month_centers = [(month_edges[k] + month_edges[k + 1]) / 2 for k in range(12)]

    ax.set_xlim(1, 366)
    yticks, yticklabels = [], []

    band_h = cfg.band_height_frac * row_gap
    gap = cfg.bar_gap_frac * row_gap
    bar_h = (band_h - 2 * gap) / 3

    row = 0
    for category, species_list in grouped.items():
        base = row * row_gap

        for s in reversed(species_list):
            base = row * row_gap
            y0 = base - band_h/2 + bar_h/2

            for i, ph in enumerate(reversed(cfg.phases)):
                rng = getattr(s, ph)
                if rng and rng.earliest is not None and rng.latest is not None:
                    start, end = phase_range(rng)
                    y = y0 + i * (bar_h + gap)

                    if not s.arrival:
                        y += bar_h / 2

                    fade_in = fade_out = None
                    if ph == "in_norway":
                        if s.arrival:
                            fade_in = phase_range(s.arrival)
                        if s.departure:
                            fade_out = phase_range(s.departure)
                    elif ph == "eggs":
                        if s.eggs_laid:
                            fade_in = phase_range(s.eggs_laid)
                        if s.eggs_hatch:
                            fade_out = phase_range(s.eggs_hatch)
                    elif ph == "chicks":
                        if s.eggs_hatch:
                            fade_in = phase_range(s.eggs_hatch)
                        if s.chicks_fledge:
                            fade_out = phase_range(s.chicks_fledge)

                    if fade_in or fade_out:
                        draw_fade_bar(ax, start, end, y, bar_h, cfg.phase_colors[ph],
                                      fade_in=fade_in, fade_out=fade_out, zorder=2.5)
                    else:
                        ax.add_patch(Rectangle((start, y - bar_h/2), max(0, end - start), bar_h,
                                               facecolor=cfg.phase_colors[ph], edgecolor="none", zorder=2))

                    ax.text((start + end)/2, y, cfg.phase_labels[ph], ha="center", va="center",
                            fontsize=cfg.phase_font, zorder=3,
                            bbox=dict(boxstyle="round,pad=0.25", fc="none", ec="none", alpha=cfg.phase_box_alpha))

            yticks.append(base)
            yticklabels.append("")
            ax.text(cfg.label_x_offset, base, f"{s.norwegian}\n{s.migratoriness}",
                    va="center", ha="left",
                    fontsize=(cfg.font_large if n <= 25 else cfg.font_medium if n <= 80 else cfg.font_small),
                    zorder=4,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=cfg.label_box_alpha))
            row += 1
        base += row_gap
        ax.axhspan(base - row_gap/2, base + row_gap/2, alpha=0.14, zorder=0.5)
        ax.text(366/2, base, category, va="center", ha="center",
        fontsize=cfg.font_large, fontweight="bold", zorder=3,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=cfg.label_box_alpha))

        row += 1

    for k in range(12):
        if k % 2 == 0:
            ax.axvspan(month_edges[k], month_edges[k + 1], alpha=cfg.month_bg_alpha, zorder=1)

    ax.xaxis.set_major_locator(FixedLocator(month_edges[:-1]))
    ax.set_xticklabels([""] * 12)
    ax.xaxis.set_minor_locator(FixedLocator(month_centers))
    ax.set_xticks(month_centers, cfg.months_no, minor=True)
    ax.tick_params(axis="x", which="both", top=True, labeltop=True)

    ax.set_ylim(-row_gap/2, (n - 1) * row_gap + row_gap/2)
    ax.grid(axis="x", which="major", linestyle=":", linewidth=0.6, zorder=0)

    sep_y = [-row_gap/2 + k * row_gap for k in range(n + 1)]
    for y in sep_y:
        ax.hlines(y, 1, 366, linewidth=max(0.5, cfg.line_width * 0.6), color="0.3", alpha=0.4, zorder=1.5)

    # Axis labels and title
    ax.set_title("Tider for trekk, egg og fugleunger i Oslo")

    # add sources text
    fig.text(0.01, 0.01,
            """Kilder:
1) Norsk fugleatlas (1994). Norsk Ornitologisk Forening, Klæbu.
2) Egne observasjoner og journaler i FugleAdvokatene
3) Store Norske Leksikon (snl.no)
4) Artsdatabanken (artsdatabanken.no)
""",
            ha="left", va="bottom", fontsize=8, linespacing=1.5)
    

    fig.text(0.90, 0.01,
            """Utviklet av Jonathan Reichelt Gjertsen i FugleAdvokatene
Kildekode: github.com/jonathangjertsen/fugleatlas
""",
            ha="right", va="bottom", fontsize=8, linespacing=1.5)

    # Equal visible borders on all sides
    for side in ["top", "right", "bottom", "left"]:
        ax.spines[side].set_visible(True)
        ax.spines[side].set_linewidth(cfg.line_width)

    # Hide y-axis ticks and labels (species labels drawn manually)
    ax.tick_params(axis="y", which="both", left=False, right=False, labelleft=False)

    # Small margins for spacing
    ax.margins(x=0.01, y=0.02)
    
    if not cfg.ready:
        ax.text(0.5, 0.5, "DEMO\nIKKE BRUK",
            transform=ax.transAxes,
            ha="center", va="center",
            fontsize=150, color="red",
            alpha=0.4, rotation=30,
            zorder=10)
    
    # Save and show plot
    plt.savefig("bird_timeline.svg", format="svg", bbox_inches="tight")

def main():
    species_sel = get_species_selection()
    species_data = get_species_data(species_sel)
    species_data = sorted(species_data, key=lambda s: s.sort_key())
    grouped = OrderedDict()
    for s in species_data:
        grouped.setdefault(s.category, []).append(s)
    del grouped[None]
    plot_species(grouped)

if __name__ == "__main__":
    main()
