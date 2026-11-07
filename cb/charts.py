"""Grafik üretimi.

Tasarım kararı: her grafik için **önce Python kodu üretilir**, sonra o kod
çalıştırılıp grafik elde edilir. Böylece ekranda görünen grafik ile öğrencinin
kopyalayacağı kod birebir aynı işi yapar; arada kayma olmaz.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

from . import detect  # noqa: E402

PANDAS = "pandas"
MATPLOTLIB = "matplotlib"
SEABORN = "seaborn"

KUTUPHANELER = {
    PANDAS: "pandas (.plot)",
    MATPLOTLIB: "matplotlib (ax)",
    SEABORN: "seaborn (sns)",
}

GRAFIKLER = {
    "line": "Çizgi grafiği",
    "bar": "Çubuk grafiği",
    "scatter": "Dağılım grafiği",
    "hist": "Histogram",
    "box": "Kutu grafiği",
    "heatmap": "Isı haritası (korelasyon)",
}

# Hem matplotlib renk haritası hem seaborn paleti olarak çalışan adlar.
# Böylece aynı seçim üç kütüphanede de kullanılabiliyor.
PALETLER = [
    "Set2", "Set1", "Set3", "tab10", "tab20", "Pastel1", "Pastel2",
    "Dark2", "Paired", "Accent",
    "viridis", "plasma", "cividis", "magma", "mako", "crest", "flare",
]

CMAPLER = [
    "viridis", "plasma", "cividis", "magma", "mako", "crest", "flare",
    "RdBu_r", "coolwarm", "Blues", "Greens", "Set2", "tab10", "Pastel1",
]

MARKERLAR = ["o", "s", "^", "D", "v", "x", "+", "P", "*"]

TOPLAMALAR = {
    "mean": "ortalama",
    "sum": "toplam",
    "median": "medyan",
    "count": "satır sayısı",
}

TEMALAR = ["whitegrid", "darkgrid", "white", "dark", "ticks"]


def varsayilan_ayarlar() -> dict:
    return {
        "grafik": "bar",
        "kutuphane": SEABORN,
        "x": None,
        "y": None,
        "hue": None,
        "sutunlar": [],
        "toplama": "mean",
        "sirala": True,
        "bins": 20,
        "renk": "#4C72B0",
        "palet": "Set2",
        "cmap": "RdBu_r",
        "marker": "o",
        "cizgi_kalinligi": 2.0,
        "nokta_boyu": 45.0,
        "saydamlik": 0.85,
        "izgara": True,
        "gosterge": True,
        "baslik": "",
        "x_etiketi": "",
        "y_etiketi": "",
        "genislik": 8.0,
        "yukseklik": 4.5,
        "tema": "whitegrid",
        "kde": False,
        "annot": True,
    }


# --------------------------------------------------------------------------- #
# Grafik türüne göre hangi seçenekler anlamlı?
# --------------------------------------------------------------------------- #

def secenekler(grafik: str, kutuphane: str | None = None) -> set[str]:
    """Grafik türüne göre arayüzde gösterilecek ayar anahtarları."""
    ortak = {"baslik", "x_etiketi", "y_etiketi", "genislik", "yukseklik"}

    if grafik == "line":
        return ortak | {"marker", "cizgi_kalinligi", "nokta_boyu",
                        "saydamlik", "izgara", "gosterge", "sirala",
                        "palet", "renk", "tema"}
    if grafik == "bar":
        return ortak | {"toplama", "sirala", "izgara", "saydamlik",
                        "renk", "tema"}
    if grafik == "scatter":
        return ortak | {"marker", "nokta_boyu", "saydamlik", "izgara",
                        "gosterge", "renk", "palet", "tema"}
    if grafik == "hist":
        return ortak | {"bins", "saydamlik", "izgara", "renk", "kde", "tema"}
    if grafik == "box":
        return ortak | {"izgara", "saydamlik", "renk", "tema"}
    if grafik == "heatmap":
        return ortak | {"cmap", "annot", "tema"}
    return ortak


# --------------------------------------------------------------------------- #
# Kod kurucuları
# --------------------------------------------------------------------------- #

def _q(ad: str | None) -> str:
    """Sütun adını kod metnine güvenli biçimde gömer."""
    return repr(ad)


def _basliklar(a: dict) -> list[str]:
    satirlar = []
    if a["baslik"]:
        satirlar.append(f"ax.set_title({a['baslik']!r})")
    if a["x_etiketi"]:
        satirlar.append(f"ax.set_xlabel({a['x_etiketi']!r})")
    if a["y_etiketi"]:
        satirlar.append(f"ax.set_ylabel({a['y_etiketi']!r})")
    return satirlar


def _izgara(a: dict) -> list[str]:
    if not a["izgara"]:
        return []
    return ["ax.grid(True, alpha=0.3)", "ax.set_axisbelow(True)"]


def _kapanis() -> list[str]:
    return [
        "plt.tight_layout()",
        "# Defterde göstermek için son satıra plt.show() ekleyebilirsin.",
    ]


def _kurulum(a: dict) -> list[str]:
    if a["kutuphane"] == SEABORN:
        satir = ["import seaborn as sns", "import matplotlib.pyplot as plt",
                 f"sns.set_theme(style={a['tema']!r})", ""]
    else:
        satir = ["import matplotlib.pyplot as plt", "import pandas as pd",
                 "import numpy as np", ""]
    satir.append(
        f"fig, ax = plt.subplots(figsize=({a['genislik']}, {a['yukseklik']}))"
    )
    return satir


def _renk_dongusu(a: dict) -> list[str]:
    """Kategorik gruplar için renk listesi üretir (matplotlib/pandas)."""
    return [
        "from matplotlib.colors import to_hex",
        f"gruplar = list(df[{_q(a['hue'])}].dropna().unique())",
        f"renkler = [to_hex(plt.get_cmap({a['palet']!r})(v))",
        "           for v in np.linspace(0, 1, max(len(gruplar), 1))]",
    ]


# ------------------------------- ÇİZGİ ------------------------------------- #

def _line(a: dict) -> str:
    x, y = _q(a["x"]), _q(a["y"])
    hue = a["hue"]
    s = _kurulum(a)

    if a["kutuphane"] == PANDAS:
        if a["sirala"]:
            s.append(f"df = df.sort_values({x})")
        if hue:
            s += [
                f"veri = df.pivot_table(index={x}, columns={_q(hue)}, "
                f"values={y}, aggfunc={a['toplama']!r})",
                f"veri.plot(ax=ax, marker={a['marker']!r}, "
                f"linewidth={a['cizgi_kalinligi']}, cmap={a['palet']!r})",
            ]
        else:
            s += [
                f"veri = df.set_index({x})[{y}]",
                f"veri.plot(ax=ax, marker={a['marker']!r}, "
                f"linewidth={a['cizgi_kalinligi']}, color={a['renk']!r})",
            ]
        if a["y_etiketi"] == "":
            s.append(f"ax.set_ylabel({y})")
        if a["gosterge"] and hue:
            s.append(f"ax.legend(title={_q(hue)})")

    elif a["kutuphane"] == MATPLOTLIB:
        if a["sirala"]:
            s.append(f"df = df.sort_values({x})")
        if hue:
            s += _renk_dongusu(a)
            s += [
                "for i, ad in enumerate(gruplar):",
                f"    grup = df[df[{_q(hue)}] == ad]",
                f"    ax.plot(grup[{x}], grup[{y}], label=ad,",
                f"            color=renkler[i], marker={a['marker']!r},",
                f"            linewidth={a['cizgi_kalinligi']}, "
                f"markersize={round(a['nokta_boyu'] / 10, 2)}, "
                f"alpha={a['saydamlik']})",
            ]
            if a["gosterge"]:
                s.append(f"ax.legend(title={_q(hue)})")
        else:
            s += [
                f"ax.plot(df[{x}], df[{y}], color={a['renk']!r},",
                f"        marker={a['marker']!r}, "
                f"linewidth={a['cizgi_kalinligi']}, "
                f"markersize={round(a['nokta_boyu'] / 10, 2)}, "
                f"alpha={a['saydamlik']})",
            ]
    else:  # SEABORN
        if a["sirala"]:
            s.append(f"df = df.sort_values({x})")
        hue_arg = f", hue={_q(hue)}" if hue else ""
        stil_arg = f", palette={a['palet']!r}" if hue else f", color={a['renk']!r}"
        s.append(
            f"sns.lineplot(data=df, x={x}, y={y}{hue_arg}, "
            f"marker={a['marker']!r}, linewidth={a['cizgi_kalinligi']}, "
            f"errorbar=None{stil_arg}, ax=ax)"
        )
        if a["gosterge"] and hue:
            s.append(f"ax.legend(title={_q(hue)})")

    s += _basliklar(a) + _izgara(a)
    return "\n".join(s + _kapanis())


# ------------------------------- ÇUBUK ------------------------------------- #

def _bar(a: dict) -> str:
    x, y = _q(a["x"]), _q(a["y"])
    s = _kurulum(a)
    yon = "ascending=False" if a["sirala"] else "ascending=True"

    s.append(f"veri = df.groupby({x}, dropna=False)[{y}].agg({a['toplama']!r})")
    if a["sirala"]:
        s.append(f"veri = veri.sort_values({yon})")

    if a["kutuphane"] == PANDAS:
        s.append(f"veri.plot(kind='bar', ax=ax, color={a['renk']!r}, "
                 f"alpha={a['saydamlik']})")
        s.append('ax.tick_params(axis="x", rotation=45)')
    elif a["kutuphane"] == MATPLOTLIB:
        s += [
            f"ax.bar(veri.index.astype(str), veri.values, "
            f"color={a['renk']!r},",
            f"       alpha={a['saydamlik']}, edgecolor='white')",
            'ax.tick_params(axis="x", rotation=45)',
        ]
    else:  # SEABORN
        s += [
            f"sns.barplot(x=veri.index, y=veri.values, "
            f"color={a['renk']!r},",
            f"            alpha={a['saydamlik']}, ax=ax)",
            'ax.tick_params(axis="x", rotation=45)',
        ]

    if a["y_etiketi"] == "":
        s.append(f"ax.set_ylabel({y})")
    s += _basliklar(a) + _izgara(a)
    return "\n".join(s + _kapanis())


# ------------------------------ DAĞILIM ------------------------------------ #

def _scatter(a: dict) -> str:
    x, y = _q(a["x"]), _q(a["y"])
    hue = a["hue"]
    s = _kurulum(a)

    if a["kutuphane"] in (PANDAS, MATPLOTLIB):
        if hue:
            s += _renk_dongusu(a)
            s.append("for i, ad in enumerate(gruplar):")
            s.append(f"    grup = df[df[{_q(hue)}] == ad]")
            if a["kutuphane"] == PANDAS:
                s += [
                    f"    grup.plot.scatter(x={x}, y={y}, ax=ax, label=ad,",
                    f"        color=renkler[i], "
                    f"alpha={a['saydamlik']},",
                    f"        marker={a['marker']!r}, "
                    f"s={a['nokta_boyu']})",
                ]
            else:
                s += [
                    f"    ax.scatter(grup[{x}], grup[{y}], label=ad,",
                    f"        color=renkler[i], "
                    f"alpha={a['saydamlik']},",
                    f"        marker={a['marker']!r}, "
                    f"s={a['nokta_boyu']})",
                ]
            if a["gosterge"]:
                s.append(f"ax.legend(title={_q(hue)})")
        else:
            if a["kutuphane"] == PANDAS:
                s += [
                    f"df.plot.scatter(x={x}, y={y}, ax=ax, "
                    f"color={a['renk']!r},",
                    f"    alpha={a['saydamlik']}, marker={a['marker']!r}, "
                    f"s={a['nokta_boyu']})",
                ]
            else:
                s += [
                    f"ax.scatter(df[{x}], df[{y}], color={a['renk']!r},",
                    f"    alpha={a['saydamlik']}, marker={a['marker']!r}, "
                    f"s={a['nokta_boyu']})",
                ]
    else:  # SEABORN
        hue_arg = f", hue={_q(hue)}" if hue else ""
        stil_arg = f", palette={a['palet']!r}" if hue else f", color={a['renk']!r}"
        s.append(
            f"sns.scatterplot(data=df, x={x}, y={y}{hue_arg}, "
            f"marker={a['marker']!r}, s={a['nokta_boyu']}, "
            f"alpha={a['saydamlik']}{stil_arg}, ax=ax)"
        )
        if a["gosterge"] and hue:
            s.append(f"ax.legend(title={_q(hue)})")

    s += _basliklar(a) + _izgara(a)
    return "\n".join(s + _kapanis())


# ------------------------------ HİSTOGRAM ---------------------------------- #

def _hist(a: dict) -> str:
    x = _q(a["x"])
    s = _kurulum(a)

    if a["kutuphane"] == PANDAS:
        s += [
            f"df[{x}].plot(kind='hist', bins={a['bins']}, ax=ax,",
            f"    color={a['renk']!r}, alpha={a['saydamlik']}, "
            f"edgecolor='white')",
        ]
    elif a["kutuphane"] == MATPLOTLIB:
        s += [
            f"ax.hist(df[{x}].dropna(), bins={a['bins']},",
            f"    color={a['renk']!r}, alpha={a['saydamlik']}, "
            f"edgecolor='white')",
        ]
    else:  # SEABORN
        kde = ", kde=True" if a["kde"] else ""
        s += [
            f"sns.histplot(data=df, x={x}, bins={a['bins']}{kde},",
            f"    color={a['renk']!r}, alpha={a['saydamlik']}, ax=ax)",
        ]

    if a["x_etiketi"] == "":
        s.append(f"ax.set_xlabel({x})")
    if a["y_etiketi"] == "":
        s.append("ax.set_ylabel('Frekans')")
    s += _basliklar(a) + _izgara(a)
    return "\n".join(s + _kapanis())


# ------------------------------ KUTU --------------------------------------- #

def _box(a: dict) -> str:
    y = _q(a["y"])
    x = _q(a["x"]) if a["x"] else None
    s = _kurulum(a)

    if a["kutuphane"] == PANDAS:
        if x:
            s.append(f"df.boxplot(column={y}, by={x}, ax=ax, grid=False)")
        else:
            s.append(f"df.boxplot(column={y}, ax=ax, grid=False)")
        s.append("fig.suptitle('')  # pandas kendi başlığını ekler, kaldırıyoruz")
        if x:
            s.append('ax.tick_params(axis="x", rotation=45)')

    elif a["kutuphane"] == MATPLOTLIB:
        if x:
            s += [
                f"kategoriler = list(df[{x}].dropna().unique())",
                f"veri = [df.loc[df[{x}] == k, {y}].dropna().values "
                "for k in kategoriler]",
                "ax.boxplot(veri, tick_labels=[str(k) for k in kategoriler],",
                f"    patch_artist=True, boxprops=dict("
                f"facecolor={a['renk']!r}, alpha={a['saydamlik']}))",
                'ax.tick_params(axis="x", rotation=45)',
                f"ax.set_xlabel({x})",
            ]
        else:
            s += [
                f"ax.boxplot(df[{y}].dropna(),",
                f"    patch_artist=True, boxprops=dict("
                f"facecolor={a['renk']!r}, alpha={a['saydamlik']}))",
            ]
    else:  # SEABORN
        if x:
            s += [
                f"sns.boxplot(data=df, x={x}, y={y}, color={a['renk']!r},",
                f"    saturation={a['saydamlik']}, width=0.6, ax=ax)",
                'ax.tick_params(axis="x", rotation=45)',
            ]
        else:
            s += [
                f"sns.boxplot(data=df, y={y}, color={a['renk']!r},",
                f"    saturation={a['saydamlik']}, width=0.4, ax=ax)",
            ]

    if a["y_etiketi"] == "":
        s.append(f"ax.set_ylabel({y})")
    s += _basliklar(a) + _izgara(a)
    return "\n".join(s + _kapanis())


# ------------------------------ ISI HARİTASI ------------------------------- #

def _heatmap(a: dict) -> str:
    sutunlar = ", ".join(repr(s) for s in a["sutunlar"])

    if a["kutuphane"] == PANDAS:
        # pandas'ta hazır ısı haritası yok: Styler ile tablo renklendirilir.
        s = [
            "import pandas as pd",
            "",
            f"sayisal = [{sutunlar}]",
            "korelasyon = df[sayisal].corr()",
            "stil = (korelasyon.style",
            f"    .background_gradient(cmap={a['cmap']!r}, vmin=-1, vmax=1)",
            "    .format('{:.2f}'))",
            "# Defterde hücrenin son satırına `stil` yazınca tablo renklenir.",
        ]
        return "\n".join(s)

    s = _kurulum(a)
    s += [f"sayisal = [{sutunlar}]", "korelasyon = df[sayisal].corr()", ""]

    if a["kutuphane"] == SEABORN:
        s += [
            "sns.heatmap(korelasyon, annot={0}, fmt='.2f',".format(a["annot"]),
            f"    cmap={a['cmap']!r}, vmin=-1, vmax=1, linewidths=0.5, ax=ax)",
        ]
    else:
        s += [
            f"im = ax.imshow(korelasyon, cmap={a['cmap']!r}, vmin=-1, vmax=1)",
            'ax.set_xticks(range(len(korelasyon.columns)), '
            'korelasyon.columns, rotation=45, ha="right")',
            "ax.set_yticks(range(len(korelasyon.index)), korelasyon.index)",
            "fig.colorbar(im, ax=ax, shrink=0.8)",
        ]
        if a["annot"]:
            s += [
                "for i in range(len(korelasyon.index)):",
                "    for j in range(len(korelasyon.columns)):",
                "        ax.text(j, i, f'{korelasyon.iat[i, j]:.2f}',",
                '                ha="center", va="center", fontsize=9)',
            ]

    s += _basliklar(a)
    return "\n".join(s + _kapanis())


_URETICILER = {
    "line": _line,
    "bar": _bar,
    "scatter": _scatter,
    "hist": _hist,
    "box": _box,
    "heatmap": _heatmap,
}


def kod_uret(ayarlar: dict) -> str:
    """Seçilen grafik ve kütüphane için çalıştırılabilir Python kodu üretir."""
    return _URETICILER[ayarlar["grafik"]](ayarlar)


# --------------------------------------------------------------------------- #
# Çalıştırma
# --------------------------------------------------------------------------- #

class CizimHatasi(Exception):
    """Grafik üretilemediğinde fırlatılır."""


def calistir(df: pd.DataFrame, kod: str) -> tuple[str, object]:
    """Üretilen kodu çalıştırır; ("figure" | "styler", nesne) döndürür."""
    plt.close("all")
    # seaborn bir önceki çalıştırmada global rcParams'ı değiştirmiş olabilir;
    # her grafik varsayılan stille başlasın.
    matplotlib.rcdefaults()
    ortam = {"df": df, "pd": pd, "np": np, "plt": plt, "sns": sns}
    try:
        exec(compile(kod, "<uretilen kod>", "exec"), ortam)
    except Exception as hata:
        plt.close("all")
        raise CizimHatasi(f"{type(hata).__name__}: {hata}") from hata

    if ortam.get("stil") is not None:
        return "styler", ortam["stil"]
    fig = ortam.get("fig")
    if fig is None:
        plt.close("all")
        raise CizimHatasi("Kod çalıştı ama bir grafik üretmedi.")
    return "figure", fig


def kapat() -> None:
    """Bellekte biriken grafikleri temizler."""
    plt.close("all")


# --------------------------------------------------------------------------- #
# Hangi grafik çizilebilir?
# --------------------------------------------------------------------------- #

def _kategori_sutunlari(turler: dict[str, str]) -> list[str]:
    """Eksen olabilecek kategorik sütunlar.

    Serbest metin (METIN) bilinçli olarak dışarıda: ad, not, kimlik gibi
    sütunların eksene konması anlamsız ve okunaksız olur.
    """
    return [a for a, t in turler.items()
            if t in (detect.KATEGORIK, detect.TARIH)]


def uygun_grafikler(turler: dict[str, str]) -> dict[str, str]:
    sayisal = [a for a, t in turler.items() if t == detect.SAYISAL]
    kategori = _kategori_sutunlari(turler)

    uygun: dict[str, str] = {}
    if len(sayisal) >= 1:
        uygun["hist"] = GRAFIKLER["hist"]
        uygun["box"] = GRAFIKLER["box"]
    if len(sayisal) >= 2:
        uygun["scatter"] = GRAFIKLER["scatter"]
        uygun["heatmap"] = GRAFIKLER["heatmap"]
    if len(sayisal) >= 1 and kategori:
        uygun["bar"] = GRAFIKLER["bar"]
        uygun["line"] = GRAFIKLER["line"]
    return uygun


def eksen_secenekleri(turler: dict[str, str], grafik: str) -> dict:
    sayisal = [a for a, t in turler.items() if t == detect.SAYISAL]
    kategori = _kategori_sutunlari(turler)

    if grafik == "line":
        return {"x": kategori + sayisal, "y": sayisal, "hue": kategori}
    if grafik == "bar":
        return {"x": kategori, "y": sayisal, "hue": []}
    if grafik == "scatter":
        return {"x": sayisal, "y": sayisal, "hue": kategori}
    if grafik == "hist":
        return {"x": sayisal, "y": [], "hue": []}
    if grafik == "box":
        return {"x": kategori, "y": sayisal, "hue": []}
    if grafik == "heatmap":
        return {"x": sayisal, "y": [], "hue": []}
    return {"x": [], "y": [], "hue": []}
