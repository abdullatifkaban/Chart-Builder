"""Grafik kodu üretimi ve çalıştırma.

Kod **parçalara bölünür**: her özellik (başlık, renk, ızgara…) ayrı bir
bloktur. Arayüz bu blokları sırayla göstererek "kodu büyüterek yazma"
hissini verir. Aynı bloklardan hem kopyalanabilir kod hem de önizleme
üretilir; ikisi arasında kayma olmaz.

Blok yapısı:
    {"ad": "Başlık", "satirlar": ["plt.title('...')"], "aciklama": "..."}
"""

from __future__ import annotations

import re

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

PANDAS = "pandas"
MATPLOTLIB = "matplotlib"
SEABORN = "seaborn"

KUTUPHANELER = {
    PANDAS: "pandas (.plot)",
    MATPLOTLIB: "matplotlib (pyplot)",
    SEABORN: "seaborn (sns)",
}

GRAFIKLER = {
    "line": "Çizgi grafiği",
    "step": "Basamak grafiği",
    "area": "Alan grafiği",
    "bar": "Çubuk grafiği",
    "stacked": "Yığılmış çubuk",
    "pie": "Pasta grafiği",
    "scatter": "Dağılım grafiği",
    "hist": "Histogram",
    "box": "Kutu grafiği",
    "violin": "Keman grafiği",
    "heatmap": "Isı haritası (korelasyon)",
}

# Her grafik her kütüphanede yoktur: seaborn'da pasta/alan/yığılmış çubuk,
# pandas'ta keman grafiği hazır gelmez.
GRAFIK_KUTUPHANELERI: dict[str, set[str]] = {
    "line": {PANDAS, MATPLOTLIB, SEABORN},
    "step": {PANDAS, MATPLOTLIB, SEABORN},
    "area": {PANDAS, MATPLOTLIB},
    "bar": {PANDAS, MATPLOTLIB, SEABORN},
    "stacked": {PANDAS, MATPLOTLIB},
    "pie": {PANDAS, MATPLOTLIB},
    "scatter": {PANDAS, MATPLOTLIB, SEABORN},
    "hist": {PANDAS, MATPLOTLIB, SEABORN},
    "box": {PANDAS, MATPLOTLIB, SEABORN},
    "violin": {MATPLOTLIB, SEABORN},
    "heatmap": {PANDAS, MATPLOTLIB, SEABORN},
}

# matplotlib renk haritası olarak da çalışan, nitel (kategorik) paletler.
PALETLER = [
    "Set2", "Set1", "Set3", "tab10", "tab20",
    "Pastel1", "Pastel2", "Dark2", "Paired", "Accent",
]

CMAPLER = [
    "RdBu_r", "coolwarm", "viridis", "plasma", "cividis",
    "magma", "Blues", "Greens",
]

MARKERLAR = ["o", "s", "^", "D", "v", "x", "+", "P", "*"]

CIZGI_STILLERI = {
    "solid": "düz",
    "dashed": "kesikli",
    "dotted": "noktalı",
    "dashdot": "nokta-çizgi",
}

BASAMAKLAR = {"pre": "basamak önce", "mid": "basamak ortada",
              "post": "basamak sonra"}

IC_GOSTERIM = {"box": "kutu", "quartile": "çeyrekler",
               "point": "nokta", "stick": "çubuk"}

TOPLAMALAR = {
    "mean": "ortalama",
    "sum": "toplam",
    "median": "medyan",
    "count": "satır sayısı",
}

TEMALAR = ["whitegrid", "darkgrid", "white", "dark", "ticks"]

AYLAR = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


def ay_mi(seri: pd.Series) -> bool:
    """Sütun Türkçe ay adlarından oluşuyor mu?"""
    degerler = {str(v).strip() for v in seri.dropna().unique()}
    return len(degerler) >= 3 and degerler.issubset(set(AYLAR))


def kutuphane_grafikleri(kutuphane: str) -> dict[str, str]:
    """Seçilen kütüphanede çizilebilen grafik türleri."""
    return {
        anahtar: ad for anahtar, ad in GRAFIKLER.items()
        if kutuphane in GRAFIK_KUTUPHANELERI[anahtar]
    }


def varsayilan_ayarlar() -> dict:
    """Arayüzün dolduracağı boş ayar sözlüğü."""
    return {
        "kutuphane": SEABORN,
        "grafik": "line",
        "x": None,
        "y": None,
        "hue": None,
        "sutunlar": [],
        # dekorasyon
        "baslik": None,
        "x_etiketi": None,
        "y_etiketi": None,
        "izgara_on": False,
        "boyut_on": False,
        "genislik": 8.0,
        "yukseklik": 4.5,
        "gosterge_on": True,
        "renk_on": False,
        "renk": "#4C72B0",
        "saydamlik_on": False,
        "saydamlik": 0.85,
        # çizgi ailesi
        "isaret_on": False,
        "marker": "o",
        "cizgi_on": False,
        "cizgi_kalinligi": 2.0,
        "stil_on": False,
        "stil": "dashed",
        "basamak_on": False,
        "basamak": "mid",
        "dolg_on": False,
        "dolg_saydamlik": 0.35,
        "yigin_on": True,
        # çubuk ailesi
        "yatay_on": False,
        "cubuk_genislik_on": False,
        "cubuk_genisligi": 0.8,
        "deger_on": False,
        "kenar_on": False,
        "yuzde_yigin_on": False,
        # dağılım
        "nokta_on": False,
        "nokta_boyu": 45.0,
        "bins_on": False,
        "bins": 20,
        "kde_on": False,
        "kumulatif_on": False,
        "yogunluk_on": False,
        # kutu / keman
        "ortalama_on": False,
        "aykiri_gizle_on": False,
        "ic_on": False,
        "ic": "box",
        "kesme_on": False,
        "kesme": 2,
        # pasta
        "pasta_yuzde_on": False,
        "baslangic_on": False,
        "baslangic": 90,
        "patlama_on": False,
        "patlama": 0.05,
        "golge_on": False,
        # ısı haritası
        "cmap_on": False,
        "cmap": "RdBu_r",
        "annot_on": False,
        "ucgen_on": False,
        "hucre_on": False,
        "renk_cubugu_on": False,
        # veri hazırlama
        "sirala_on": True,
        "zaman_on": False,
        "toplama": "mean",
        "palet_on": False,
        "palet": "Set2",
        "tema_on": False,
        "tema": "whitegrid",
        "donus_on": False,
    }


# --------------------------------------------------------------------------- #
# Grafik türüne göre hangi seçenekler anlamlı?
# --------------------------------------------------------------------------- #

def izinli(ayarlar: dict) -> set[str]:
    """Bu grafik + kütüphane için anlamlı özellik anahtarları."""
    lib = ayarlar["kutuphane"]
    ortak = {"baslik", "boyut"}
    if lib == SEABORN:
        ortak |= {"tema"}

    cizgi_ailesi = ortak | {"x_etiketi", "y_etiketi", "izgara", "gosterge",
                            "renk", "saydamlik", "cizgi", "stil", "sirala",
                            "zaman", "palet"}

    grafik = ayarlar["grafik"]
    if grafik == "line":
        return cizgi_ailesi | {"isaret"}
    if grafik == "step":
        return cizgi_ailesi | {"basamak", "isaret"}
    if grafik == "area":
        return cizgi_ailesi | {"dolg", "yigin"}
    if grafik == "bar":
        kume = ortak | {"x_etiketi", "y_etiketi", "izgara", "renk",
                        "saydamlik", "sirala", "donus", "cubuk_genislik",
                        "deger", "kenar", "yatay"}
        return kume
    if grafik == "stacked":
        return ortak | {"x_etiketi", "y_etiketi", "izgara", "gosterge",
                        "saydamlik", "sirala", "donus", "cubuk_genislik",
                        "kenar", "yuzde_yigin", "palet"}
    if grafik == "pie":
        return ortak | {"gosterge", "pasta_yuzde", "baslangic", "patlama",
                        "golge"}
    if grafik == "scatter":
        return ortak | {"x_etiketi", "y_etiketi", "izgara", "gosterge",
                        "renk", "saydamlik", "isaret", "nokta", "palet",
                        "kenar"}
    if grafik == "hist":
        return ortak | {"x_etiketi", "y_etiketi", "izgara", "renk",
                        "saydamlik", "bins", "kde", "kumulatif", "yogunluk",
                        "kenar"}
    if grafik == "box":
        kume = ortak | {"x_etiketi", "y_etiketi", "izgara", "renk",
                        "donus", "ortalama", "aykiri_gizle"}
        if lib != SEABORN:
            kume.add("saydamlik")
        if lib != SEABORN:
            kume.add("yatay")
        return kume
    if grafik == "violin":
        return ortak | {"x_etiketi", "y_etiketi", "izgara", "renk",
                        "saydamlik", "donus", "ic", "kesme"}
    if grafik == "heatmap":
        if lib == PANDAS:
            return {"cmap", "annot"}
        kume = {"baslik", "boyut", "cmap", "annot", "ucgen", "hucre"}
        if lib == SEABORN:
            kume.add("tema")
        else:
            kume.add("renk_cubugu")
        return kume
    return ortak


# --------------------------------------------------------------------------- #
# Küçük yardımcılar
# --------------------------------------------------------------------------- #

def _blok(ad: str, satirlar: list[str], aciklama: str) -> dict:
    return {"ad": ad, "satirlar": satirlar, "aciklama": aciklama}


def _sayi(deger: float) -> str:
    return f"{float(deger):g}"


def _cagri(ad: str, parcalar: list[str]) -> list[str]:
    """Uzun çağrıları iki satıra böler; kısa olanı tek satır bırakır."""
    tek = f"{ad}({', '.join(parcalar)})"
    if len(tek) <= 88 or len(parcalar) <= 2:
        return [tek]
    return [f"{ad}({', '.join(parcalar[:2])},",
            " " * (len(ad) + 1) + ", ".join(parcalar[2:]) + ")"]


def _boyut_arg(ayarlar: dict) -> list[str]:
    if not ayarlar["boyut_on"]:
        return []
    return [f"figsize=({_sayi(ayarlar['genislik'])}, "
            f"{_sayi(ayarlar['yukseklik'])})"]


def _plot_renk(ayarlar: dict, hue: str | None) -> list[str]:
    """Tek renk + saydamlık gibi ortak çizim parametreleri."""
    parcalar: list[str] = []
    if ayarlar["renk_on"] and not hue:
        parcalar.append(f"color={ayarlar['renk']!r}")
    if ayarlar["saydamlik_on"]:
        parcalar.append(f"alpha={ayarlar['saydamlik']}")
    return parcalar


def _cizgi_stil(ayarlar: dict) -> list[str]:
    parcalar: list[str] = []
    if ayarlar["isaret_on"]:
        parcalar.append(f"marker={ayarlar['marker']!r}")
    if ayarlar["cizgi_on"]:
        parcalar.append(f"linewidth={ayarlar['cizgi_kalinligi']}")
    if ayarlar["stil_on"]:
        parcalar.append(f"linestyle={ayarlar['stil']!r}")
    return parcalar


def _veriyi_sirala(a: dict, x_raw: str) -> list[dict]:
    """Çizgi ailesi için sıralama / takvim sırası blokları."""
    x = repr(x_raw)
    if a["zaman_on"]:
        return [_blok(
            "Zaman sırası",
            [f"sira = {AYLAR!r}",
             f"df[{x}] = pd.Categorical(df[{x}], categories=sira, "
             "ordered=True)",
             f"df = df.sort_values({x})"],
            "Ay adları alfabetik değil takvim sırasına göre dizilir.",
        )]
    if a["sirala_on"]:
        return [_blok(
            "Sırala",
            [f"df = df.sort_values({x})"],
            "Çizginin soldan sağa doğru sıralı ilerlemesi için veriyi "
            "x'e göre sıralar.",
        )]
    return []


def _renkler(a: dict) -> tuple[str, list[str]]:
    """Grupları dolaşan kodlar için palet ve renk satırı."""
    palet = a["palet"] if a["palet_on"] else "Set2"
    return palet, [f"renkler = plt.get_cmap({palet!r}).colors",
                   f"for i, (ad, grup) in enumerate(df.groupby({a['hue']!r})):"]


def _deger_etiketleri(ad: str = "veri") -> dict:
    return _blok(
        f"Değerleri yaz",
        [f"for i, deger in enumerate({ad}.values):",
         f"    plt.text(i, deger, f'{{deger:.1f}}',",
         "             ha='center', va='bottom', fontsize=9)"],
        "Her çubuğun üstüne sayısal değeri yazar; tabloya bakmadan "
        "okumayı sağlar.",
    )


# --------------------------------------------------------------------------- #
# Çizgi ailesi
# --------------------------------------------------------------------------- #

def _line(a: dict, df: pd.DataFrame) -> list[dict]:
    bloklar = _veriyi_sirala(a, a["x"])
    x, y, hue = repr(a["x"]), repr(a["y"]), a["hue"]
    stil = _cizgi_stil(a) + _plot_renk(a, hue)

    if a["kutuphane"] == PANDAS:
        if hue:
            bloklar.append(_blok(
                "Veriyi genişlet",
                [f"veri = df.pivot_table(index={x}, columns={hue!r}, "
                 f"values={y}, aggfunc={a['toplama']!r})"],
                "Grupları ayrı sütunlara açar; her grup bir çizgi olur.",
            ))
            arg = ["kind='line'"] + _boyut_arg(a)
            if a["palet_on"]:
                arg.append(f"colormap={a['palet']!r}")
            arg += stil
            bloklar.append(_blok(
                "Çizgiyi çiz", _cagri("veri.plot", arg),
                "pandas her sütunu ayrı bir çizgi olarak çizer.",
            ))
        else:
            arg = [f"x={x}", f"y={y}", "kind='line'"] + _boyut_arg(a) + stil
            bloklar.append(_blok(
                "Çizgiyi çiz", _cagri("df.plot", arg),
                "İki sütunu doğrudan alır; `kind='line'` çizgi ister.",
            ))

    elif a["kutuphane"] == MATPLOTLIB:
        if hue:
            palet, satirlar = _renkler(a)
            satirlar += [
                f"    plt.plot(grup[{x}], grup[{y}], label=ad,",
                "             " + ", ".join(
                    ["color=renkler[i % len(renkler)]"] + stil) + ")",
            ]
            bloklar.append(_blok(
                "Grupları dolaş", satirlar,
                "Her grup için ayrı bir çizgi çizer ve rengi paletten seçer.",
            ))
        else:
            bloklar.append(_blok(
                "Çizgiyi çiz", _cagri("plt.plot", [f"df[{x}]", f"df[{y}]"]
                                      + stil),
                "pyplot'un en temel komutu: x listesi ve y listesi.",
            ))

    else:  # SEABORN
        arg = ["data=df", f"x={x}", f"y={y}", "errorbar=None"]
        if hue:
            arg.append(f"hue={hue!r}")
            if a["palet_on"]:
                arg.append(f"palette={a['palet']!r}")
        arg += stil
        bloklar.append(_blok(
            "Çizgiyi çiz", _cagri("sns.lineplot", arg),
            "Sütun adlarıyla çalışır; `errorbar=None` gölgeli güven "
            "aralığını kapatır.",
        ))
    return bloklar


def _step(a: dict, df: pd.DataFrame) -> list[dict]:
    bloklar = _veriyi_sirala(a, a["x"])
    x, y, hue = repr(a["x"]), repr(a["y"]), a["hue"]
    stil = _cizgi_stil(a) + _plot_renk(a, hue)
    nerede = a["basamak"]

    if a["kutuphane"] == PANDAS:
        if hue:
            bloklar.append(_blok(
                "Veriyi genişlet",
                [f"veri = df.pivot_table(index={x}, columns={hue!r}, "
                 f"values={y}, aggfunc={a['toplama']!r})"],
                "Grupları ayrı sütunlara açar; her grup bir basamak "
                "dizisi olur.",
            ))
            arg = ["kind='line'"] + _boyut_arg(a)
            if a["palet_on"]:
                arg.append(f"colormap={a['palet']!r}")
            arg += [f"drawstyle='steps-{nerede}'"] + stil
            bloklar.append(_blok(
                "Basamakları çiz", _cagri("veri.plot", arg),
                "`drawstyle` çizgiyi basamaklı çizer; sıçramalar net görünür.",
            ))
        else:
            arg = [f"x={x}", f"y={y}", "kind='line'"] + _boyut_arg(a)
            arg += [f"drawstyle='steps-{nerede}'"] + stil
            bloklar.append(_blok(
                "Basamakları çiz", _cagri("df.plot", arg),
                "`drawstyle='steps-...'` değer değişimlerini dik "
                "sıçramalarla gösterir.",
            ))

    elif a["kutuphane"] == MATPLOTLIB:
        if hue:
            palet, satirlar = _renkler(a)
            satirlar += [
                f"    plt.step(grup[{x}], grup[{y}], label=ad,",
                "             " + ", ".join(
                    [f"where={nerede!r}",
                     "color=renkler[i % len(renkler)]"] + stil) + ")",
            ]
            bloklar.append(_blok(
                "Grupları dolaş", satirlar,
                "`plt.step` her grup için basamaklı bir çizgi çizer.",
            ))
        else:
            bloklar.append(_blok(
                "Basamakları çiz",
                _cagri("plt.step", [f"df[{x}]", f"df[{y}]",
                                    f"where={nerede!r}"] + stil),
                "Değer sabit kalır, değiştiği yerde dik sıçrar.",
            ))

    else:  # SEABORN
        arg = ["data=df", f"x={x}", f"y={y}", "errorbar=None",
               f"drawstyle='steps-{nerede}'"]
        if hue:
            arg.append(f"hue={hue!r}")
            if a["palet_on"]:
                arg.append(f"palette={a['palet']!r}")
        arg += stil
        bloklar.append(_blok(
            "Basamakları çiz", _cagri("sns.lineplot", arg),
            "seaborn'un `drawstyle` parametresi çizgiyi basamaklı yapar.",
        ))
    return bloklar


def _area(a: dict, df: pd.DataFrame) -> list[dict]:
    bloklar = _veriyi_sirala(a, a["x"])
    x, y, hue = repr(a["x"]), repr(a["y"]), a["hue"]
    alfa = [f"alpha={a['saydamlik']}"] if a["saydamlik_on"] else [
        f"alpha={a['dolg_saydamlik']}"]

    if a["kutuphane"] == PANDAS:
        if hue:
            bloklar.append(_blok(
                "Veriyi genişlet",
                [f"veri = df.pivot_table(index={x}, columns={hue!r}, "
                 f"values={y}, aggfunc={a['toplama']!r})"],
                "Her grup ayrı bir sütun olur; alanlar üst üste yığılır.",
            ))
            arg = ["kind='area'", f"stacked={a['yigin_on']}"] + _boyut_arg(a)
            if a["palet_on"]:
                arg.append(f"colormap={a['palet']!r}")
            arg += alfa
            bloklar.append(_blok(
                "Alanı boya", _cagri("veri.plot", arg),
                "Çizgi ile x ekseni arasındaki alanı doldurur.",
            ))
        else:
            arg = [f"x={x}", f"y={y}", "kind='area'",
                   "stacked=False"] + _boyut_arg(a)
            if a["renk_on"]:
                arg.append(f"color={a['renk']!r}")
            arg += alfa
            bloklar.append(_blok(
                "Alanı boya", _cagri("df.plot", arg),
                "`kind='area'` çizginin altını doldurur.",
            ))

    else:  # MATPLOTLIB
        if hue:
            palet, _ = _renkler(a)
            bloklar.append(_blok(
                "Veriyi genişlet",
                [f"veri = df.pivot_table(index={x}, columns={hue!r}, "
                 f"values={y}, aggfunc={a['toplama']!r})",
                 f"renkler = plt.get_cmap({palet!r}).colors"],
                "Grupları sütunlara açar; `stackplot` bunları üst üste boyar.",
            ))
            bloklar.append(_blok(
                "Alanları boya",
                ["plt.stackplot(range(len(veri)), veri.T.values,",
                "                labels=veri.columns,",
                "                colors=renkler[:len(veri.columns)],",
                "                " + ", ".join(alfa) + ")",
                "plt.xticks(range(len(veri)), veri.index, rotation=45)"],
                "Her grubun alanını üst üste yığarak toplamı da gösterir.",
            ))
        else:
            bloklar.append(_blok(
                "Alanı boya",
                ["konum = range(len(df))",
                 f"plt.fill_between(konum, df[{y}],",
                 "                 " + ", ".join(
                     (["color=%r" % a["renk"]] if a["renk_on"] else [])
                     + alfa) + ")",
                 f"plt.xticks(konum, df[{x}], rotation=45)"],
                "`fill_between` çizgi ile taban arasındaki alanı doldurur.",
            ))
    return bloklar


# --------------------------------------------------------------------------- #
# Çubuk ailesi
# --------------------------------------------------------------------------- #

def _cubuk_olcu(a: dict, yatay: bool = False, renk: bool = True) -> list[str]:
    """Çubuk genişliği + isteğe bağlı tek renk + kenar çizgisi."""
    arg: list[str] = []
    if a["cubuk_genislik_on"]:
        # Yatay çubukta kalınlık `height`, dikey çubukta `width` ile verilir.
        olcu = "height" if yatay else "width"
        arg.append(f"{olcu}={a['cubuk_genisligi']}")
    if renk:
        arg += _plot_renk(a, None)
    elif a["saydamlik_on"]:
        arg.append(f"alpha={a['saydamlik']}")
    if a["kenar_on"]:
        arg.append("edgecolor='white'")
    return arg


def _bar(a: dict, df: pd.DataFrame) -> list[dict]:
    bloklar: list[dict] = []
    x, y = repr(a["x"]), repr(a["y"])
    yatay = a["yatay_on"]

    bloklar.append(_blok(
        "Özetle",
        [f"veri = df.groupby({x}, dropna=False)[{y}]"
         f".agg({a['toplama']!r})"],
        "Çubuk için her kategoriye tek bir değer gerekir.",
    ))
    if a["sirala_on"]:
        bloklar.append(_blok(
            "Sırala",
            ["veri = veri.sort_values(ascending=False)"],
            "Çubukları büyükten küçüğe dizer; okumayı kolaylaştırır.",
        ))

    # pandas'ta `width` hem dikey hem yatay çubukta kalınlıktır.
    arg = _cubuk_olcu(a, yatay=yatay and a["kutuphane"] != PANDAS)
    if a["kutuphane"] == PANDAS:
        tur = "barh" if yatay else "bar"
        if yatay:
            arg = ["kind='barh'"] + _boyut_arg(a) + arg
        else:
            arg = ["kind='bar'"] + _boyut_arg(a) + arg
        bloklar.append(_blok(
            "Çubukları çiz", _cagri("veri.plot", arg),
            f"`kind='{tur}'` hazırlanan özet serisini çizime çevirir.",
        ))
    elif a["kutuphane"] == MATPLOTLIB:
        if yatay:
            bloklar.append(_blok(
                "Çubukları çiz",
                _cagri("plt.barh", ["veri.index", "veri.values"] + arg),
                "`barh` çubukları yatay çizer; uzun adlar daha rahat okunur.",
            ))
        else:
            bloklar.append(_blok(
                "Çubukları çiz",
                _cagri("plt.bar", ["veri.index", "veri.values"] + arg),
                "Kategori adları ve yükseklikler ayrı listeler olarak "
                "verilir.",
            ))
    else:
        arg = ["x=veri.index", "y=veri.values"] + arg
        bloklar.append(_blok(
            "Çubukları çiz", _cagri("sns.barplot", arg),
            "Özetlenmiş değerleri çubuk olarak çizer.",
        ))

    if a["deger_on"] and not yatay:
        bloklar.append(_deger_etiketleri())
    return bloklar


def _stacked(a: dict, df: pd.DataFrame) -> list[dict]:
    x, y, hue = repr(a["x"]), repr(a["y"]), repr(a["hue"])
    bloklar = [_blok(
        "Veriyi genişlet",
        [f"veri = df.pivot_table(index={x}, columns={hue}, "
         f"values={y}, aggfunc={a['toplama']!r}, fill_value=0)"],
        "Satır kategori, sütun ikinci kategori olur; her sütun bir "
        "yığın katmanıdır.",
    )]
    if a["yuzde_yigin_on"]:
        bloklar.append(_blok(
            "Yüzdeye çevir",
            ["veri = veri.div(veri.sum(axis=1), axis=0) * 100"],
            "Her satırı kendi toplamına böler; katmanlar %100'e tamamlanır.",
        ))
    if a["sirala_on"]:
        bloklar.append(_blok(
            "Sırala",
            ["if not veri.empty:",
             "    veri = veri.loc[veri.sum(axis=1).sort_values("
             "ascending=False).index]"],
            "Yığınları toplam büyüklüğe göre dizer.",
        ))

    arg = _cubuk_olcu(a, renk=False)
    if a["kutuphane"] == PANDAS:
        arg = ["kind='bar'", "stacked=True"] + _boyut_arg(a) + arg
        if a["palet_on"]:
            arg.append(f"colormap={a['palet']!r}")
        bloklar.append(_blok(
            "Yığını çiz", _cagri("veri.plot", arg),
            "`stacked=True` katmanları üst üste dizer.",
        ))
    else:  # MATPLOTLIB
        palet, _ = _renkler(a)
        bloklar.append(_blok(
            "Katmanları çiz",
            [f"renkler = plt.get_cmap({palet!r}).colors",
             "alt = None",
             "for i, katman in enumerate(veri.columns):",
             "    plt.bar(veri.index, veri[katman], bottom=alt,",
             "            label=katman,",
             "            color=renkler[i % len(renkler)],",
             "            " + ", ".join(arg) + ")",
             "    alt = (veri[katman] if alt is None",
             "           else alt + veri[katman])"],
            "Her katmanı bir öncekinin üstüne koyar; `bottom` bu işi yapar.",
        ))
    return bloklar


def _pie(a: dict, df: pd.DataFrame) -> list[dict]:
    x, y = repr(a["x"]), repr(a["y"])
    bloklar = [_blok(
        "Özetle",
        [f"veri = df.groupby({x}, dropna=False)[{y}]"
         f".agg({a['toplama']!r})",
         "veri = veri.sort_values(ascending=False)"],
        "Her dilime tek bir değer gerekir.",
    )]

    if a["patlama_on"]:
        bloklar.append(_blok(
            "Dilimleri ayır",
            [f"patlama = [{a['patlama']!r}] * len(veri)"],
            "Dilimleri merkezden hafifçe koparır; bir dilimi vurgulamak "
            "için kullanılır.",
        ))

    arg: list[str] = []
    if a["pasta_yuzde_on"]:
        arg.append("autopct='%1.0f%%'")
    if a["baslangic_on"]:
        arg.append(f"startangle={a['baslangic']}")
    if a["patlama_on"]:
        arg.append("explode=patlama")
    if a["golge_on"]:
        arg.append("shadow=True")

    if a["kutuphane"] == PANDAS:
        arg = ["kind='pie'"] + _boyut_arg(a) + arg
        if a["gosterge_on"]:
            arg.append("legend=True")
        bloklar.append(_blok(
            "Dilimleri çiz", _cagri("veri.plot", arg),
            "pandas indeksteki kategori adlarını etiket olarak kullanır.",
        ))
    else:
        bloklar.append(_blok(
            "Dilimleri çiz",
            _cagri("plt.pie", ["veri.values", "labels=veri.index"] + arg),
            "Her değer bir dilim; `labels` kategori adlarını verir.",
        ))
        if a["gosterge_on"]:
            bloklar.append(_blok(
                "Gösterge", ["plt.legend(title=" + x + ")"],
                "Hangi dilimin hangi kategori olduğunu ayrıca listeler.",
            ))
    return bloklar


# --------------------------------------------------------------------------- #
# Dağılım
# --------------------------------------------------------------------------- #

def _scatter(a: dict, df: pd.DataFrame) -> list[dict]:
    x, y, hue = repr(a["x"]), repr(a["y"]), a["hue"]
    stil: list[str] = []
    if a["isaret_on"]:
        stil.append(f"marker={a['marker']!r}")
    if a["nokta_on"]:
        stil.append(f"s={a['nokta_boyu']}")
    if a["kenar_on"]:
        stil += ["edgecolors='white'", "linewidths=0.5"]
    stil += _plot_renk(a, hue)

    if a["kutuphane"] == PANDAS:
        if hue:
            ortak = ["color=renkler[i % len(renkler)]"] + stil
            return [_blok(
                "Grupları dolaş",
                [f"renkler = plt.get_cmap({a['palet']!r}).colors",
                 f"for i, (ad, grup) in enumerate(df.groupby({hue!r})):",
                 f"    grup.plot.scatter(x={x}, y={y}, ax=plt.gca(), "
                 "label=ad,",
                 "        " + ", ".join(ortak) + ")"],
                "Her grubu ayrı renkte çizer; `label` göstergede görünür.",
            )]
        return [_blok(
            "Noktaları çiz",
            _cagri("df.plot.scatter", [f"x={x}", f"y={y}"]
                   + _boyut_arg(a) + stil),
            "İki sütunu doğrudan alır; her satır bir noktadır.",
        )]

    if a["kutuphane"] == MATPLOTLIB:
        if hue:
            return [_blok(
                "Grupları dolaş",
                [f"renkler = plt.get_cmap({a['palet']!r}).colors",
                 f"for i, (ad, grup) in enumerate(df.groupby({hue!r})):",
                 f"    plt.scatter(grup[{x}], grup[{y}], label=ad,",
                 "                " + ", ".join(
                     ["color=renkler[i % len(renkler)]"] + stil) + ")"],
                "Her grubu ayrı renkte çizer ve göstergede etiketler.",
            )]
        return [_blok(
            "Noktaları çiz",
            _cagri("plt.scatter", [f"df[{x}]", f"df[{y}]"] + stil),
            "x ve y listelerini alır; her satır bir nokta olur.",
        )]

    arg = ["data=df", f"x={x}", f"y={y}"]
    if hue:
        arg.append(f"hue={hue!r}")
        if a["palet_on"]:
            arg.append(f"palette={a['palet']!r}")
    arg += stil
    return [_blok(
        "Noktaları çiz", _cagri("sns.scatterplot", arg),
        "Sütun adlarıyla çalışır; `hue` grupları renkle ayırır.",
    )]


def _hist(a: dict, df: pd.DataFrame) -> list[dict]:
    x = repr(a["x"])
    stil = _plot_renk(a, None)
    ayar: list[str] = []
    if a["bins_on"]:
        ayar.append(f"bins={a['bins']}")
    if a["kumulatif_on"]:
        ayar.append("cumulative=True")
    if a["yogunluk_on"]:
        ayar.append("density=True")
    kenar = ["edgecolor='white'"] if a["kenar_on"] else []

    if a["kutuphane"] == PANDAS:
        arg = ["kind='hist'"] + _boyut_arg(a) + ayar + stil + kenar
        return [_blok(
            "Histogramı çiz", _cagri(f"df[{x}].plot", arg),
            "Tek sütunu aralıklara bölüp her aralığın sıklığını sayar.",
        )]
    if a["kutuphane"] == MATPLOTLIB:
        arg = [f"df[{x}].dropna()"] + ayar + stil + kenar
        return [_blok(
            "Histogramı çiz", _cagri("plt.hist", arg),
            "Değerleri alır, aralıklara böler ve sıklıkları çizer.",
        )]
    arg = ["data=df", f"x={x}"] + ayar
    if a["kde_on"]:
        arg.append("kde=True")
    if a["yogunluk_on"]:
        arg = [p for p in arg if p != "density=True"]
        arg.append("stat='density'")
    arg += stil + kenar
    return [_blok(
        "Histogramı çiz", _cagri("sns.histplot", arg),
        "seaborn histogramı; `stat='density'` alanı 1'e normalize eder.",
    )]


def _box(a: dict, df: pd.DataFrame) -> list[dict]:
    y = repr(a["y"])
    x = repr(a["x"]) if a["x"] else None
    renk = [f"color={a['renk']!r}"] if a["renk_on"] else []
    alfa = [f"alpha={a['saydamlik']}"] if a["saydamlik_on"] else []
    bloklar: list[dict] = []

    if a["kutuphane"] == PANDAS:
        arg = [f"column={y}"]
        if x:
            arg.append(f"by={x}")
        arg.append("grid=False")
        if a["ortalama_on"]:
            arg.append("showmeans=True")
        if a["aykiri_gizle_on"]:
            arg.append("showfliers=False")
        if a["yatay_on"]:
            arg.append("vert=False")
        if renk or alfa:
            arg.append(f"boxprops=dict({', '.join(renk + alfa)})")
        bloklar.append(_blok(
            "Kutuları çiz", _cagri("df.boxplot", arg) + [
                "plt.suptitle('')  # pandas kendi üst başlığını ekler"],
            "Medyan, çeyrekler ve aykırı değerleri gösterir.",
        ))
        return bloklar

    if a["kutuphane"] == MATPLOTLIB:
        if x:
            bloklar.append(_blok(
                "Grupları hazırla",
                [f"kategoriler = df[{x}].dropna().unique()",
                 f"veri = [df.loc[df[{x}] == k, {y}].dropna() "
                 "for k in kategoriler]"],
                "Kutu grafiği her grup için ayrı bir değer listesi ister.",
            ))
            arg = ["veri", "tick_labels=kategoriler", "patch_artist=True"]
        else:
            arg = [f"[df[{y}].dropna()]", "patch_artist=True"]
        if a["ortalama_on"]:
            arg.append("showmeans=True")
        if a["aykiri_gizle_on"]:
            arg.append("showfliers=False")
        if a["yatay_on"]:
            arg.append("vert=False")
        if renk or alfa:
            arg.append(f"boxprops=dict({', '.join(renk + alfa)})")
        bloklar.append(_blok(
            "Kutuları çiz", _cagri("plt.boxplot", arg),
            "Grup başına beş sayı özetini (min, çeyrekler, medyan, maks) "
            "çizer.",
        ))
        return bloklar

    arg = ["data=df"]
    if x:
        arg += [f"x={x}", f"y={y}"]
    else:
        arg.append(f"y={y}")
    arg += renk
    bloklar.append(_blok(
        "Kutuları çiz", _cagri("sns.boxplot", arg),
        "Uzun formattaki veriden grup bazında kutu çizer.",
    ))
    return bloklar


def _violin(a: dict, df: pd.DataFrame) -> list[dict]:
    y = repr(a["y"])
    x = repr(a["x"]) if a["x"] else None
    renk = [f"color={a['renk']!r}"] if a["renk_on"] else []
    alfa = [f"alpha={a['saydamlik']}"] if a["saydamlik_on"] else []

    if a["kutuphane"] == MATPLOTLIB:
        bloklar: list[dict] = []
        if x:
            bloklar.append(_blok(
                "Grupları hazırla",
                [f"kategoriler = df[{x}].dropna().unique()",
                 f"veri = [df.loc[df[{x}] == k, {y}].dropna() "
                 "for k in kategoriler]"],
                "Keman grafiği her grup için ayrı bir değer listesi ister.",
            ))
            arg = ["veri", "showmeans=" + str(a["ortalama_on"])]
        else:
            arg = [f"[df[{y}].dropna()]",
                   "showmeans=" + str(a["ortalama_on"])]
        bloklar.append(_blok(
            "Kemanları çiz", _cagri("plt.violinplot", arg),
            "Dağılımın yoğunluğunu simetrik bir gövde olarak çizer.",
        ))
        if x:
            bloklar.append(_blok(
                "Etiketleri yaz",
                ["plt.xticks(range(1, len(kategoriler) + 1), kategoriler, "
                 "rotation=45)"],
                "Keman gövdesi 1'den başlar; etiketleri elle yerleştiririz.",
            ))
        return bloklar

    arg = ["data=df"]
    if x:
        arg += [f"x={x}", f"y={y}"]
    else:
        arg.append(f"y={y}")
    if a["ic_on"]:
        arg.append(f"inner={a['ic']!r}")
    if a["kesme_on"]:
        arg.append(f"cut={a['kesme']}")
    if a["saydamlik_on"]:
        arg.append(f"alpha={a['saydamlik']}")
    arg += renk
    return [_blok(
        "Kemanları çiz", _cagri("sns.violinplot", arg),
        "Yoğunluğu gövde genişliğiyle gösterir; `inner` iç özeti seçer.",
    )]


# --------------------------------------------------------------------------- #
# Isı haritası
# --------------------------------------------------------------------------- #

def _heatmap(a: dict, df: pd.DataFrame) -> list[dict]:
    sutunlar = ", ".join(repr(s) for s in a["sutunlar"])
    on = [f"korelasyon = df[[{sutunlar}]].corr()"]

    if a["kutuphane"] == PANDAS:
        stil = ["        .format('{:.2f}'))"]
        return [
            _blok("Korelasyonu hesapla", on,
                  "Seçilen sayısal sütunlar arasındaki ilişkiyi hesaplar."),
            _blok("Tabloyu renklendir",
                  ["stil = (korelasyon.style",
                   f"        .background_gradient(cmap={a['cmap']!r}, "
                   "vmin=-1, vmax=1)"] + stil,
                  "pandas'ta hazır ısı haritası yok; tablo renkle boyanır."),
        ]

    bloklar = [_blok("Korelasyonu hesapla", on,
                     "Seçilen sayısal sütunlar arasındaki ilişkiyi hesaplar.")]
    if a["ucgen_on"]:
        bloklar.append(_blok(
            "Üst üçgeni gizle",
            ["import numpy as np",
             "maske = np.triu(np.ones_like(korelasyon, dtype=bool), k=1)"],
            "Matris simetriktir; üst yarısını gizlemek tekrarı kaldırır.",
        ))

    if a["kutuphane"] == SEABORN:
        arg = ["korelasyon"]
        if a["annot_on"]:
            arg += ["annot=True", "fmt='.2f'"]
        if a["ucgen_on"]:
            arg.append("mask=maske")
        if a["hucre_on"]:
            arg.append("linewidths=0.5")
        arg += [f"cmap={a['cmap']!r}", "vmin=-1", "vmax=1"]
        bloklar.append(_blok(
            "Isı haritasını çiz", _cagri("sns.heatmap", arg),
            "Hücre rengi korelasyonun işaretini ve gücünü gösterir.",
        ))
        return bloklar

    arg = ["korelasyon", f"cmap={a['cmap']!r}", "vmin=-1", "vmax=1"]
    satirlar = _cagri("plt.imshow", arg) + [
        "plt.xticks(range(len(korelasyon.columns)),",
        "           korelasyon.columns, rotation=45, ha='right')",
        "plt.yticks(range(len(korelasyon.index)), korelasyon.index)",
    ]
    if a["renk_cubugu_on"]:
        satirlar.append("plt.colorbar()")
    bloklar.append(_blok(
        "Isı haritasını çiz", satirlar,
        "Matrisi renkli bir görüntü olarak çizer.",
    ))

    if a["annot_on"]:
        bloklar.append(_blok(
            "Değerleri yaz",
            ["for i in range(len(korelasyon.index)):",
             "    for j in range(len(korelasyon.columns)):",
             "        if not maske[i, j]:" if a["ucgen_on"] else
             "        if True:",
             "            plt.text(j, i, f'{korelasyon.iat[i, j]:.2f}',",
             "                     ha='center', va='center')"],
            "Her hücrenin üstüne korelasyon değerini yazar.",
        ))
    return bloklar


_KURUCULAR = {
    "line": _line,
    "step": _step,
    "area": _area,
    "bar": _bar,
    "stacked": _stacked,
    "pie": _pie,
    "scatter": _scatter,
    "hist": _hist,
    "box": _box,
    "violin": _violin,
    "heatmap": _heatmap,
}


# --------------------------------------------------------------------------- #
# Süsleme blokları
# --------------------------------------------------------------------------- #

def _susleme(a: dict) -> list[dict]:
    izin = izinli(a)
    bloklar: list[dict] = []

    if "baslik" in izin and a["baslik"]:
        bloklar.append(_blok(
            "Başlık", [f"plt.title({a['baslik']!r})"],
            "Grafiğin ne anlattığını tek satırda söyler.",
        ))
    if "x_etiketi" in izin and a["x_etiketi"]:
        bloklar.append(_blok(
            "x ekseni etiketi", [f"plt.xlabel({a['x_etiketi']!r})"],
            "Yatay eksenin ne olduğunu yazar (birim varsa ekle).",
        ))
    if "y_etiketi" in izin and a["y_etiketi"]:
        bloklar.append(_blok(
            "y ekseni etiketi", [f"plt.ylabel({a['y_etiketi']!r})"],
            "Dikey eksenin ne olduğunu yazar.",
        ))
    if "izgara" in izin and a["izgara_on"]:
        bloklar.append(_blok(
            "Izgara", ["plt.grid(alpha=0.3)"],
            "Değer okumayı kolaylaştırır; göz almasın diye saydam çizilir.",
        ))
    if "donus" in izin and a["donus_on"]:
        bloklar.append(_blok(
            "Etiketleri döndür", ["plt.xticks(rotation=45)"],
            "Uzun kategori adlarının üst üste binmesini önler.",
        ))
    if a["hue"] and "gosterge" in izin and a["gosterge_on"]:
        bloklar.append(_blok(
            "Gösterge", [f"plt.legend(title={a['hue']!r})"],
            "Hangi rengin hangi gruba ait olduğunu gösterir.",
        ))
    return bloklar


# --------------------------------------------------------------------------- #
# Öğretim alanı: grafiğin amacı, okunması ve veriye dayalı yorum
# --------------------------------------------------------------------------- #

REHBER: dict[str, dict] = {
    "line": {
        "amac": "Bir değerin **sıralı bir eksen** boyunca (genellikle zaman) "
                "nasıl değiştiğini gösterir. Göz, eğimi ve yönü kolayca "
                "yakalar.",
        "ne_zaman": [
            "x ekseni tarih ya da sıralı bir kategori ise (ay, gün, yıl)",
            "Soru \"trend nasıl?\", \"artıyor mu, azalıyor mu?\" ise",
            "Aynı eksende birkaç seriyi karşılaştırmak istiyorsan (hue)",
        ],
        "okuma": [
            "Çizginin **yönü** trendi verir: yukarı eğim artış, aşağı eğim "
            "azalış demektir.",
            "Dik bölümler hızlı değişimi, yatay bölümler durağanlığı "
            "gösterir.",
            "Keskin sıçramaları tek başına yorumlamadan önce veri hatası "
            "olup olmadığını kontrol et.",
        ],
        "dikkat": [
            "Sırasız kategorilerde (şehir, ürün) çizgi yanıltıcıdır; "
            "aralarında olmayan bir süreklilik ima eder.",
            "Kesik y ekseni küçük farkları dev gibi gösterir.",
            "5-6'dan fazla seri çizgiyi okunmaz yapar; vurgulama ya da "
            "küçük çoklu panel düşün.",
        ],
    },
    "step": {
        "amac": "Değerin **basamaklar hâlinde** değiştiğini gösterir. Değer "
                "iki ölçüm arasında sabit kalır, değiştiği anda dik sıçrar.",
        "ne_zaman": [
            "Değer belirli eşiklerde atlıyorsa (tarife, kota, stok seviyesi)",
            "Arada geçiş olmadığını, değerin sabit tutulduğunu "
            "vurgulamak istiyorsan",
            "Sıralı bir eksende ani kırılmaları göstermek istiyorsan",
        ],
        "okuma": [
            "Her yatay parça, o aralıkta değerin **sabit** kaldığını söyler.",
            "Dikey atlamalar değişimin gerçekleştiği noktayı gösterir.",
            "Basamak konumu (`pre` / `mid` / `post`) sıçramanın hangi "
            "ölçüme yazılacağını belirler.",
        ],
        "dikkat": [
            "Düzgün değişen veride basamak grafiği gereksiz kırıklık "
            "yaratır; çizgi daha doğru olur.",
            "Basamak konumunu değiştirmek eğimi kaydırır; aynı grafikte "
            "tutarlı seç.",
            "Çok fazla kırılma varsa sonuç testere dişine döner ve trend "
            "kaybolur.",
        ],
    },
    "area": {
        "amac": "Çizginin altındaki **alanı** doldurarak hem değişimi hem de "
                "büyüklüğü (hacim) gösterir. Yığıldığında parçaların "
                "toplamını da verir.",
        "ne_zaman": [
            "Toplam büyüklük ve birikim önemliyse (satış hacmi, üretim)",
            "Yığılmış hâlde parçaların toplam içindeki payı merak "
            "ediliyorsa",
            "Tek seride trendi vurgulamak istiyorsan",
        ],
        "okuma": [
            "Alanın **yüksekliği** o andaki değeri verir.",
            "Yığılmış alanda toplam, en üstteki çizginin yüksekliğidir; "
            "katman kalınlığı payı gösterir.",
            "Katman sınırlarının eğimi, o parçanın katkısının arttığını ya "
            "da azaldığını söyler.",
        ],
        "dikkat": [
            "Yığılmış alanda yalnızca en alttaki katman ortak bir tabana "
            "sahiptir; üsttekilerin karşılaştırılması zordur.",
            "Değerler negatifse yığma anlamsızlaşır (pandas hata verir).",
            "Birden çok seride alan dolgusu üst üste binerse okunmaz; "
            "saydamlık ya da çizgi tercih et.",
        ],
    },
    "bar": {
        "amac": "**Kategoriler arasındaki büyüklüğü** karşılaştırır. Gözün en "
                "iyi yaptığı iş uzunluk karşılaştırmasıdır.",
        "ne_zaman": [
            "x ekseni kategorik ise (şehir, ürün, bölüm)",
            "Soru \"hangisi daha büyük?\", \"sıralama nedir?\" ise",
            "Her kategori için tek bir özet değer varsa (ortalama, toplam)",
        ],
        "okuma": [
            "Çubuk **uzunluğu** değeri verir; sıfırdan başlamalıdır.",
            "Çubuklar sıralıysa ilk ve son çubuk en uçtaki kategorileri "
            "gösterir.",
            "Yatay çubukta uzun kategori adları daha rahat okunur.",
        ],
        "dikkat": [
            "Kesik eksen farkı abartır; çubuk ekseni daima sıfırdan başlar.",
            "Kategori sayısı 15-20'yi geçerse ilk N kategori ya da yatay "
            "çubuk daha okunur olur.",
            "3B çubuk kullanma; derinlik algısı değeri çarpıtır.",
        ],
    },
    "stacked": {
        "amac": "Her kategorinin **içindeki parçaları** gösterir; bütün ile "
                "payları aynı anda okumayı sağlar.",
        "ne_zaman": [
            "Bir toplamın alt kategorilere nasıl dağıldığını göstermek "
            "istiyorsan",
            "Kategoriler arasında **pay** karşılaştırması yapıyorsan "
            "(%100 normalize)",
            "Az sayıda katman varsa (2-5)",
        ],
        "okuma": [
            "Toplam yükseklik o kategorinin bütününü verir.",
            "Katman kalınlığı payı gösterir; %100 normalize edildiyse her "
            "çubuk aynı yüksekliktedir.",
            "Katmanların sırası grafikten grafiğe değişmemeli; aksi hâlde "
            "göz yanılır.",
        ],
        "dikkat": [
            "Yalnızca en alttaki katman ortak tabana sahiptir; üstteki "
            "katmanların karşılaştırılması zordur.",
            "Çok katman varsa renkler ayırt edilemez; 5'ten sonrası için "
            "küçük çoklu panel düşün.",
            "Paylar %100'e tamamlanıyorsa ham sayılar kaybolur; toplamı "
            "ayrıca belirt.",
        ],
    },
    "pie": {
        "amac": "Bir **bütünün parçalarını** gösterir. Amaç, her dilimin "
                "bütün içindeki payını tek bakışta vermektir.",
        "ne_zaman": [
            "Parçaların toplamı anlamlı bir bütün oluşturuyorsa (paylar)",
            "Dilim sayısı azsa (en çok 4-5)",
            "Yalnızca \"yaklaşık yarısı\", \"üçte biri\" gibi kaba oranlar "
            "yeterliyse",
        ],
        "okuma": [
            "Her dilimin **açısı** (ve alanı) payı gösterir; toplam %100'dür.",
            "Yüzdeler yazılıysa dilim alanına güvenmek yerine sayıyı oku.",
            "Dilimler büyükten küçüğe sıralıysa karşılaştırma kolaylaşır.",
        ],
        "dikkat": [
            "İnsan gözü açıları uzunluklar kadar iyi karşılaştıramaz; "
            "sıralama sorularında çubuk daha doğrudur.",
            "Çok dilimli pastada küçük farklar görünmez.",
            "3B veya patlatılmış dilimler alan algısını bozar; en fazla bir "
            "dilimi vurgula.",
        ],
    },
    "scatter": {
        "amac": "İki sayısal değişken arasındaki **ilişkiyi** gösterir. Her "
                "nokta bir gözlemdir (bir satır).",
        "ne_zaman": [
            "Elimizde iki sayısal sütun varsa",
            "Soru \"x arttıkça y değişiyor mu?\" ise",
            "Aykırı değerleri ve kümeleri gözle bulmak istiyorsan",
        ],
        "okuma": [
            "Noktalar bir **doğru boyunca** yükseliyorsa pozitif, iniyorsa "
            "negatif ilişki vardır.",
            "Bulut ne kadar dar ise ilişki o kadar güçlüdür; dağınık bulut "
            "zayıf ilişki demektir.",
            "Tek başına duran noktalar aykırı değer olabilir; önce "
            "incele, sonra karar ver.",
        ],
        "dikkat": [
            "İlişki **nedensellik demek değildir**; sadece birlikte "
            "değişimi gösterir.",
            "Nokta sayısı çoksa üst üste binme olur; saydamlık ya da daha "
            "küçük nokta kullan.",
            "Nokta boyutunu üçüncü bir değişkene bağlarsan alan algısı "
            "doğrusal değildir.",
        ],
    },
    "hist": {
        "amac": "Tek bir sayısal değişkenin **dağılımını** gösterir: hangi "
                "aralıklarda yığılma var, dağılım simetrik mi?",
        "ne_zaman": [
            "Tek sayısal sütunun genel şeklini merak ediyorsan",
            "Soru \"değerler nerede toplanıyor?\" ise",
            "Veri temizliğinde aykırı değeri ilk gözle bulmak için",
        ],
        "okuma": [
            "Çubukların **yüksekliği** o aralıktaki gözlem sayısıdır "
            "(yoğunluk seçildiyse alan 1'e normalize edilir).",
            "Tek bir tepe varsa dağılım tek modlu; iki tepe varsa iki ayrı "
            "grup karışmış olabilir.",
            "Kuyruk sağa uzuyorsa sağa çarpık (birkaç büyük değer), sola "
            "uzuyorsa sola çarpık.",
        ],
        "dikkat": [
            "**Bin sayısı** sonucu değiştirir: az bins kaba, çok bins "
            "gürültülü görünür. Birkaç değeri dene.",
            "Histogram çubukları arasında boşluk yoktur; her çubuk bir "
            "*aralığı* temsil eder, kategori değil.",
            "Eksik değerler histograma girmez; eksik sayısını ayrıca "
            "kontrol et.",
        ],
    },
    "box": {
        "amac": "Bir sayısal değişkenin dağılımını **özetler**: medyan, "
                "çeyrekler ve aykırı değerler.",
        "ne_zaman": [
            "Grupları dağılım açısından karşılaştıracaksan (şube, bölüm)",
            "Soru \"hangi grup daha değişken?\" ise",
            "Aykırı değerleri işaretlemek istiyorsan",
        ],
        "okuma": [
            "Kutunun ortasındaki çizgi **medyandır**; kutunun alt ve üst "
            "kenarı 1. ve 3. çeyrektir.",
            "Kutunun yüksekliği (çeyrekler arası açıklık) verinin "
            "yayılımını gösterir.",
            "Bıyıkların dışındaki noktalar aykırı değerdir.",
        ],
        "dikkat": [
            "Kutu medyanı ve çeyrekleri gösterir; ortalama görünmez.",
            "Göz, kutu yüksekliklerini çubuk uzunlukları kadar iyi "
            "karşılaştıramaz.",
            "Grup başına gözlem çok azsa (5-10) kutu yanıltıcı olur.",
        ],
    },
    "violin": {
        "amac": "Dağılımın **yoğunluğunu** gövde genişliğiyle gösterir; kutu "
                "grafiğinin özetine dağılımın şeklini ekler.",
        "ne_zaman": [
            "Grupların dağılım **şekli** de önemliyse (tek/çift tepeli)",
            "Grup başına yeterli gözlem varsa",
            "Kutu grafiği iki grubun farklı şekilde dağıldığını "
            "saklıyorsa",
        ],
        "okuma": [
            "Gövdenin **geniş** olduğu yer, değerlerin yığıldığı aralıktır.",
            "İç gösterim (`inner`) medyanı, çeyrekleri ya da ortalamayı "
            "verir.",
            "İki tepeli gövde, veride iki ayrı grubun karıştığını ima eder.",
        ],
        "dikkat": [
            "Az gözlemde gövde pürüzlü ve yanıltıcı olur.",
            "Gövdenin uçlarındaki ince kuyruklar kesme (`cut`) ayarına çok "
            "duyarlıdır.",
            "Alan algısı doğrusal değildir; dilim alanı yerine genişliği "
            "oku.",
        ],
    },
    "heatmap": {
        "amac": "Sayısal değişkenler arasındaki **korelasyon matrisini** "
                "renkle okur. Desen avlamak için hızlı bir genel bakıştır.",
        "ne_zaman": [
            "Çok sayıda sayısal sütunun birbiriyle ilişkisi merak "
            "ediliyorsa",
            "Hangi değişkenlere odaklanacağını arıyorsan (ilk keşif)",
            "İlişkilerin işaretini topluca görmek istiyorsan",
        ],
        "okuma": [
            "Hücre rengi korelasyonun **işaretini ve gücünü** gösterir; "
            "kırmızı-mavi uçlar ±1'e yakın demektir.",
            "Köşegen daima 1'dir (değişken kendisiyle tam ilişkili).",
            "Matris simetriktir; üst üçgeni gizlemek tekrarı kaldırır.",
        ],
        "dikkat": [
            "Korelasyon **nedensellik değildir**; sadece birlikte değişimi "
            "gösterir.",
            "İki değişken de üçüncü bir değişkenle birlikte değişiyorsa "
            "ilişki yanıltıcı olabilir.",
            "Sütun sayısı çoksa etiketler okunmaz; en ilgili değişkenleri "
            "seç.",
        ],
    },
}


def rehber(grafik: str) -> dict:
    """Grafik türünün amacı, kullanımı, okunması ve uyarıları."""
    return REHBER.get(grafik, {
        "amac": "", "ne_zaman": [], "okuma": [], "dikkat": [],
    })


def _metin(deger) -> str:
    """Sayıyı grafikte okunur biçimde yazar."""
    try:
        sayi = float(deger)
    except (TypeError, ValueError):
        return str(deger)
    if sayi != sayi:  # NaN
        return "?"
    if abs(sayi) >= 1000:
        return f"{sayi:,.0f}".replace(",", " ")
    if abs(sayi) >= 100:
        return f"{sayi:.0f}"
    if abs(sayi) >= 10:
        return f"{sayi:.1f}".rstrip("0").rstrip(".")
    return f"{sayi:.2f}".rstrip("0").rstrip(".")


def _korelasyon_ifadesi(r: float) -> str:
    guc = abs(r)
    yon = "pozitif" if r > 0 else ("negatif" if r < 0 else "yok")
    if guc < 0.3:
        derece = "zayıf"
    elif guc < 0.6:
        derece = "orta"
    elif guc < 0.8:
        derece = "güçlü"
    else:
        derece = "çok güçlü"
    return f"{derece}, {yon}"


def _grup_serisi(df: pd.DataFrame, x: str, y: str, toplama: str):
    seri = df.groupby(x, dropna=False)[y].agg(toplama)
    return seri.dropna()


def _yorum_cizgi(a: dict, df: pd.DataFrame) -> list[str]:
    x, y, hue = a["x"], a["y"], a["hue"]
    if not x or not y or x not in df.columns or y not in df.columns:
        return []
    seri = _grup_serisi(df, x, y, a["toplama"])
    if len(seri) < 2:
        return []
    if a["zaman_on"]:
        sira = [ay for ay in AYLAR if ay in set(seri.index.astype(str))]
        if sira:
            seri = seri.reindex(sira).dropna()
    if len(seri) < 2:
        return []
    ad = TOPLAMALAR.get(a["toplama"], a["toplama"])
    ilk, son = seri.iloc[0], seri.iloc[-1]
    if son > ilk:
        yon = "artıyor"
    elif son < ilk:
        yon = "azalıyor"
    else:
        yon = "sabit kalıyor"
    cikti = [
        f"**{x}** boyunca **{y}** {ad} {_metin(ilk)} → {_metin(son)}; "
        f"genel eğilim **{yon}**.",
        f"En yüksek değer **{seri.idxmax()}** ({_metin(seri.max())}), "
        f"en düşük **{seri.idxmin()}** ({_metin(seri.min())}).",
    ]
    if hue and hue in df.columns:
        grup = _grup_serisi(df, hue, y, a["toplama"])
        if len(grup) >= 2:
            cikti.append(
                f"**{hue}** sütunu **{len(grup)} ayrı seriye** ayırıyor; "
                f"en yüksek {ad} **{grup.idxmax()}** "
                f"({_metin(grup.max())})."
            )
    return cikti


def _yorum_bar(a: dict, df: pd.DataFrame) -> list[str]:
    x, y = a["x"], a["y"]
    if not x or not y or x not in df.columns or y not in df.columns:
        return []
    seri = _grup_serisi(df, x, y, a["toplama"])
    if len(seri) < 2:
        return []
    ad = TOPLAMALAR.get(a["toplama"], a["toplama"])
    en_yuksek, en_dusuk = seri.idxmax(), seri.idxmin()
    fark = ""
    if seri.min() != 0:
        oran = (seri.max() - seri.min()) / abs(seri.min()) * 100
        fark = f" Fark yaklaşık **%{_metin(oran)}**."
    return [
        f"**{x}** kategorileri arasında en yüksek **{y}** {ad} "
        f"**{en_yuksek}** ({_metin(seri.max())}), en düşük "
        f"**{en_dusuk}** ({_metin(seri.min())}).{fark}",
        f"Toplam **{len(seri)} kategori** karşılaştırılıyor; "
        + ("çubuklar büyükten küçüğe sıralı." if a["sirala_on"]
           else "kategoriler alfabetik sırada."),
    ]


def _yorum_stacked(a: dict, df: pd.DataFrame) -> list[str]:
    x, y, hue = a["x"], a["y"], a["hue"]
    if not x or not y or not hue:
        return []
    if x not in df.columns or y not in df.columns or hue not in df.columns:
        return []
    veri = df.pivot_table(index=x, columns=hue, values=y,
                          aggfunc=a["toplama"], fill_value=0)
    if veri.empty:
        return []
    toplam = veri.sum(axis=1)
    pay = veri.sum() / veri.sum().sum() * 100
    cikti = [
        f"Her **{x}** için **{hue}** katmanlarının dağılımı gösteriliyor; "
        f"katmanların toplamı en yüksek **{toplam.idxmax()}** "
        f"({_metin(toplam.max())}).",
        f"Bütün içinde en büyük pay **{pay.idxmax()}** "
        f"(**%{_metin(pay.max())}**), en küçük **{pay.idxmin()}** "
        f"(%{_metin(pay.min())}).",
    ]
    if a["yuzde_yigin_on"]:
        cikti.append(
            "Yığın %100'e normalize edildi; çubuk yükseklikleri eşit, "
            "katman kalınlıkları yalnızca payı gösteriyor."
        )
    return cikti


def _yorum_pie(a: dict, df: pd.DataFrame) -> list[str]:
    x, y = a["x"], a["y"]
    if not x or not y or x not in df.columns or y not in df.columns:
        return []
    seri = _grup_serisi(df, x, y, a["toplama"])
    if len(seri) < 2:
        return []
    toplam = seri.sum()
    if toplam == 0:
        return []
    pay = seri / toplam * 100
    return [
        f"**{x}** kategorileri bir bütünün dilimleri; en büyük dilim "
        f"**{pay.idxmax()}** (**%{_metin(pay.max())}**), en küçük "
        f"**{pay.idxmin()}** (%{_metin(pay.min())}).",
        f"Toplam **{len(seri)} dilim** var."
        + (" Dilim sayısı dörtten fazlaysa pasta yerine çubuk daha "
           "okunur olur." if len(seri) > 4 else ""),
    ]


def _yorum_scatter(a: dict, df: pd.DataFrame) -> list[str]:
    x, y = a["x"], a["y"]
    if not x or not y or x not in df.columns or y not in df.columns:
        return []
    veri = df[[x, y]].dropna()
    if len(veri) < 3:
        return []
    r = veri[x].corr(veri[y])
    if r != r:
        return []
    cikti = [
        f"**{x}** ile **{y}** arasındaki korelasyon **r = {r:.2f}** "
        f"({_korelasyon_ifadesi(float(r))}).",
        f"**{len(veri)} gözlem** çiziliyor; her nokta bir satır.",
    ]
    if a["hue"] and a["hue"] in df.columns:
        cikti.append(
            f"**{a['hue']}** sütunu noktaları renkle ayırıyor; renk "
            "grupları ayrı bulutlar oluşturuyorsa ilişki grup içinde "
            "farklı olabilir."
        )
    return cikti


def _yorum_hist(a: dict, df: pd.DataFrame) -> list[str]:
    x = a["x"]
    if not x or x not in df.columns:
        return []
    seri = pd.to_numeric(df[x], errors="coerce").dropna()
    if seri.empty:
        return []
    ortalama, medyan = seri.mean(), seri.median()
    # Ölçekten bağımsız karşılaştırma: medyan 0 ya da negatifse de çalışır.
    esik = abs(medyan) * 0.05
    if ortalama > medyan + esik:
        sekil = "sağa çarpık (birkaç büyük değer ortalamayı yukarı çekiyor)"
    elif medyan > ortalama + esik:
        sekil = "sola çarpık (birkaç küçük değer ortalamayı aşağı çekiyor)"
    else:
        sekil = "yaklaşık simetrik"
    cikti = [
        f"**{x}** dağılımı **{sekil}**: ortalama {_metin(ortalama)}, "
        f"medyan {_metin(medyan)}.",
        f"Gözlemler {_metin(seri.min())} ile {_metin(seri.max())} arasında; "
        f"çoğunluğu {_metin(seri.quantile(0.25))}–"
        f"{_metin(seri.quantile(0.75))} aralığında.",
    ]
    if abs(ortalama - medyan) > esik:
        cikti.append(
            "Ortalama ile medyan arasındaki fark, aykırı değerlerin ya da "
            "çarpık bir kuyruğun varlığına işaret eder."
        )
    return cikti


def _yorum_kutu(a: dict, df: pd.DataFrame, keman: bool = False) -> list[str]:
    y, x = a["y"], a["x"]
    if not y or y not in df.columns:
        return []
    seri = pd.to_numeric(df[y], errors="coerce")
    if not seri.notna().any():
        return []
    tur = "Keman" if keman else "Kutu"
    cikti = []
    if x and x in df.columns:
        gruplar = df.groupby(x, dropna=False)[y]
        medyanlar = gruplar.median().dropna()
        if len(medyanlar) >= 2:
            cikti.append(
                f"**{x}** grupları arasında medyanı en yüksek "
                f"**{medyanlar.idxmax()}** ({_metin(medyanlar.max())}), "
                f"en düşük **{medyanlar.idxmin()}** "
                f"({_metin(medyanlar.min())})."
            )
            yayilim = gruplar.std().dropna()
            if len(yayilim) >= 2:
                cikti.append(
                    f"En değişken grup **{yayilim.idxmax()}** "
                    f"(std {_metin(yayilim.max())}); en tutarlı "
                    f"**{yayilim.idxmin()}** (std {_metin(yayilim.min())})."
                )
    cikti.append(
        f"**{y}** için medyan {_metin(seri.median())}, çeyrekler "
        f"{_metin(seri.quantile(0.25))}–{_metin(seri.quantile(0.75))}."
    )
    q1, q3 = seri.quantile(0.25), seri.quantile(0.75)
    iqr = q3 - q1
    if iqr > 0:
        alt, ust = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        aykiri = int(((seri < alt) | (seri > ust)).sum())
        cikti.append(
            f"1,5 × IQR kuralına göre **{aykiri} aykırı değer** var"
            + ("." if aykiri else " (temiz dağılım).")
        )
    if keman:
        cikti.append(
            "Gövdenin genişlediği yer, değerlerin en sık görüldüğü "
            "aralıktır."
        )
    return cikti


def _yorum_heatmap(a: dict, df: pd.DataFrame) -> list[str]:
    sutunlar = [s for s in a["sutunlar"] if s in df.columns]
    if len(sutunlar) < 2:
        return []
    kor = df[sutunlar].corr()
    if kor.empty:
        return []
    ciftler = []
    for i, s1 in enumerate(sutunlar):
        for s2 in sutunlar[i + 1:]:
            r = kor.loc[s1, s2]
            if r == r:
                ciftler.append((abs(r), r, s1, s2))
    if not ciftler:
        return []
    ciftler.sort(reverse=True)
    _, r, s1, s2 = ciftler[0]
    cikti = [
        f"**{len(sutunlar)} sayısal sütun** karşılaştırılıyor; en güçlü "
        f"ilişki **{s1}** – **{s2}** (r = {r:.2f}, "
        f"{_korelasyon_ifadesi(float(r))}).",
        "Köşegen 1'dir; matris simetrik olduğu için yarısı tekrardır.",
    ]
    if a["ucgen_on"]:
        cikti.append(
            "Üst üçgen maskelendi; tekrar eden hücreler gizleniyor."
        )
    return cikti


def yorumla(a: dict, df: pd.DataFrame) -> list[str]:
    """Seçilen sütunlarla grafiğin fiilen ne gösterdiğini anlatır.

    Tüm hesaplar veriden yapılır ve hata durumunda sessizce boş döner;
    böylece öğretim alanı hiçbir zaman uygulamayı düşürmez.
    """
    g = a["grafik"]
    try:
        if g in ("line", "step", "area"):
            return _yorum_cizgi(a, df)
        if g == "bar":
            return _yorum_bar(a, df)
        if g == "stacked":
            return _yorum_stacked(a, df)
        if g == "pie":
            return _yorum_pie(a, df)
        if g == "scatter":
            return _yorum_scatter(a, df)
        if g == "hist":
            return _yorum_hist(a, df)
        if g == "box":
            return _yorum_kutu(a, df)
        if g == "violin":
            return _yorum_kutu(a, df, keman=True)
        if g == "heatmap":
            return _yorum_heatmap(a, df)
    except Exception:  # yorum, grafiği asla engellemesin
        return []
    return []


def _amac_cumlesi(a: dict) -> str:
    """Seçilen sütunlarla 'bu grafik ne gösteriyor' cümlesi."""
    g = a["grafik"]
    x, y, hue = a["x"], a["y"], a["hue"]

    if g in ("line", "step", "area"):
        if a["zaman_on"]:
            eksen = f"**{x}** boyunca (takvim sırasıyla)"
        else:
            eksen = f"**{x}** boyunca"
        cumle = f"**{y}** değişkeninin {eksen} nasıl değiştiğini gösterir."
        if hue:
            cumle += (f" **{hue}** sütunu grupları ayrı serilere ayırır; "
                      "böylece grupların aynı eksende karşılaştırılması "
                      "mümkün olur.")
        return cumle
    if g == "bar":
        return (f"**{x}** kategorileri arasında **{y}** değerinin "
                f"({TOPLAMALAR.get(a['toplama'], a['toplama'])}) nasıl "
                "farklılaştığını gösterir.")
    if g == "stacked":
        return (f"Her **{x}** kategorisinde **{y}** toplamının **{hue}** "
                "katmanlarına nasıl dağıldığını gösterir.")
    if g == "pie":
        return (f"**{y}** toplamının **{x}** kategorileri arasındaki "
                "paylarını gösterir; dilimler bütünün parçalarıdır.")
    if g == "scatter":
        cumle = (f"**{x}** ile **{y}** değişkenleri arasındaki ilişkiyi "
                 "gösterir; her nokta bir gözlem.")
        if hue:
            cumle += (f" **{hue}** sütunu noktaları renkle ayırarak "
                      "grupların ilişkisinin farklı olup olmadığını "
                      "gösterir.")
        return cumle
    if g == "hist":
        return (f"**{x}** değişkeninin hangi aralıklarda yığıldığını, "
                "yani dağılımının şeklini gösterir.")
    if g == "box":
        if x:
            return (f"**{x}** gruplarında **{y}** dağılımını medyan ve "
                    "çeyrekler üzerinden karşılaştırır.")
        return f"**{y}** dağılımını medyan, çeyrekler ve aykırı değerlerle özetler."
    if g == "violin":
        if x:
            return (f"**{x}** gruplarında **{y}** dağılımının hem özetini "
                    "hem de yoğunluğunu gösterir.")
        return f"**{y}** dağılımının yoğunluğunu ve özetini gösterir."
    if g == "heatmap":
        adet = len(a["sutunlar"])
        return (f"Seçilen **{adet} sayısal sütun** arasındaki "
                "korelasyonları renkle gösterir; hangi değişkenlerin "
                "birlikte hareket ettiğini ortaya çıkarır.")
    return ""


# --------------------------------------------------------------------------- #
# Giriş noktası
# --------------------------------------------------------------------------- #

def _ice_aktar(a: dict) -> str:
    """Yalnızca kütüphane satırları (önizleme için yeterli)."""
    satirlar = ["import pandas as pd"]
    if a["kutuphane"] == SEABORN:
        satirlar.append("import seaborn as sns")
    satirlar.append("import matplotlib.pyplot as plt")
    return "\n".join(satirlar)


def _giris(a: dict, dosya_adi: str | None) -> str:
    """Her dosyada aynı kalan satırlar: kütüphaneler + veriyi okuma."""
    ad = (dosya_adi or "veri-dosyam.csv").strip()
    if ad.lower().endswith((".xlsx", ".xls")):
        okuma = f"df = pd.read_excel({ad!r})"
    else:
        okuma = f"df = pd.read_csv({ad!r})"
    return f"{_ice_aktar(a)}\n\n{okuma}"


def uret(a: dict, df: pd.DataFrame, dosya_adi: str | None = None) -> dict:
    """Ayarlardan adım bloklarını ve çalıştırılabilir kodu üretir."""
    g = a["grafik"]
    gerekli_hue = g in ("stacked",) or (g in ("line", "step", "area",
                                              "scatter") and a["hue"])
    eksik = None

    if g not in GRAFIK_KUTUPHANELERI or \
            a["kutuphane"] not in GRAFIK_KUTUPHANELERI[g]:
        eksik = "Bu grafik türü seçilen kütüphanede yok."
    elif g in ("line", "step", "area", "bar", "stacked", "pie", "scatter",
               "box") and not a["y"]:
        eksik = "Bir y (değer) sütunu seç."
    elif g in ("line", "step", "area", "bar", "stacked", "pie", "scatter") \
            and not a["x"]:
        eksik = "Bir x sütunu seç."
    elif g == "stacked" and not a["hue"]:
        eksik = "Yığılmış çubuk için renkle ayırma (hue) sütunu da seç."
    elif g in ("line", "step", "scatter") and a["x"] == a["y"]:
        eksik = ("x ve y için aynı sütunu seçtin. İki farklı sütun "
                 "seçmen gerekiyor.")
    elif gerekli_hue and a["hue"] and a["hue"] == a["x"]:
        eksik = ("Renkle ayırma (hue) sütunu x ekseninden farklı olmalı.")
    elif g == "hist" and not a["x"]:
        eksik = "Histogram için bir sayısal sütun seç."
    elif g == "violin" and not a["y"]:
        eksik = "Keman grafiği için bir sayısal sütun seç."
    elif g == "heatmap" and len(a["sutunlar"]) < 2:
        eksik = "Isı haritası için en az iki sayısal sütun seç."

    if eksik:
        return {"hazir": False, "mesaj": eksik, "bloklar": [],
                "giris": "", "kod": "", "tam_kod": "", "calistir_kod": "",
                "anahtarlar": [], "rehber": {}, "amac": "", "yorum": []}

    bloklar: list[dict] = []
    if a["kutuphane"] == SEABORN and a["tema_on"]:
        bloklar.append(_blok(
            "Tema", [f"sns.set_theme(style={a['tema']!r})"],
            "seaborn'un arka plan, ızgara ve yazı stilini seçer.",
        ))
    if a["boyut_on"] and a["kutuphane"] != PANDAS:
        bloklar.append(_blok(
            "Şekil boyutu",
            [f"plt.figure(figsize=({_sayi(a['genislik'])}, "
             f"{_sayi(a['yukseklik'])}))"],
            "Grafiğin inç cinsinden genişliği ve yüksekliği.",
        ))

    bloklar += _KURUCULAR[g](a, df)
    bloklar += _susleme(a)

    kod = "\n\n".join("\n".join(b["satirlar"]) for b in bloklar)
    giris = _giris(a, dosya_adi)
    return {
        "hazir": True,
        "mesaj": None,
        "bloklar": bloklar,
        "giris": giris,
        "kod": kod,
        # Gösterim/indirme için: giriş + grafik
        "tam_kod": f"{giris}\n\n{kod}",
        # Önizleme için: df hazır olduğundan yalnızca içe aktarma + grafik
        "calistir_kod": f"{_ice_aktar(a)}\n\n{kod}",
        "anahtarlar": anahtar_kelimeler(f"{giris}\n\n{kod}"),
        "rehber": rehber(g),
        "amac": _amac_cumlesi(a),
        "yorum": yorumla(a, df),
    }


# --------------------------------------------------------------------------- #
# Öğretim alanı: koddaki anahtar kelimeler
# --------------------------------------------------------------------------- #

# (kodda aranan parça, başlık, açıklama)
_SOZLUK: list[tuple[str, str, str]] = [
    ("import pandas as pd", "import pandas as pd",
     "pandas'ı `pd` kısa adıyla içe aktarır. Tablo işlemlerinin tamamı "
     "buradan gelir."),
    ("import seaborn as sns", "import seaborn as sns",
     "seaborn'u `sns` adıyla içe aktarır; istatistiksel grafikler "
     "sütun adlarıyla çalışır."),
    ("import matplotlib.pyplot as plt", "import matplotlib.pyplot as plt",
     "matplotlib'in `pyplot` arayüzünü `plt` adıyla içe aktarır. "
     "`plt.title` gibi komutlar buradan gelir."),
    ("pd.read_csv(", "pd.read_csv(...)",
     "CSV dosyasını tabloya (DataFrame) okur. Excel için pd.read_excel "
     "kullanılır."),
    ("pd.read_excel(", "pd.read_excel(...)",
     "Excel dosyasını okur; sayfa adı vermezsen ilk sayfayı alır."),
    ("sns.set_theme(", "sns.set_theme(...)",
     "seaborn'un arka plan, ızgara ve yazı stilini tek çağrıda ayarlar."),
    ("plt.figure(", "plt.figure(...)",
     "Yeni ve boş bir grafik tuvali açar; `figsize` inç cinsinden "
     "genişlik ve yüksekliktir."),
    ("plt.get_cmap(", "plt.get_cmap(...)",
     "Bir renk paletini renk listesine çevirir; grupları sırayla "
     "renklendirmek için kullanılır."),
    ("pd.Categorical(", "pd.Categorical(...)",
     "Ay adları gibi metinleri belirli bir sıraya bağlar; böylece "
     "alfabetik değil takvim sırasıyla dizilir."),
    ("pivot_table(", "pivot_table(...)",
     "Bir sütunu satır, diğerini sütun yapar; her grubu ayrı bir "
     "seriye (çizgiye) çevirir."),
    ("sort_values(", "sort_values(...)",
     "Satırları bir sütuna göre sıralar. Çizgi grafiğinde çizginin "
     "soldan sağa doğru ilerlemesini sağlar."),
    ("groupby(", "groupby(...)",
     "Satırları bir kategoriye göre gruplar; ardından özet hesap "
     "yapılır."),
    (".agg(", ".agg(...)",
     "Her grup için tek bir özet değer hesaplar: ortalama, toplam, "
     "medyan ya da satır sayısı."),
    (".corr()", ".corr()",
     "Sayısal sütunlar arasındaki korelasyon matrisini hesaplar "
     "(-1 ile +1 arası)."),
    ("plt.plot(", "plt.plot(x, y)",
     "En temel çizgi komutu: önce x listesi, sonra y listesi gelir."),
    ("plt.step(", "plt.step(x, y, where=)",
     "Basamaklı çizgi: değer sabit kalır, değiştiği yerde dik sıçrar."),
    ("plt.fill_between(", "plt.fill_between(x, y)",
     "Çizgi ile taban arasındaki alanı doldurur."),
    ("plt.stackplot(", "plt.stackplot(...)",
     "Birden çok alanı üst üste yığar; toplamı da gösterir."),
    ("plt.bar(", "plt.bar(x, y)",
     "Kategori adlarını ve yükseklikleri ayrı listeler olarak alır."),
    ("plt.barh(", "plt.barh(x, y)",
     "Çubukları yatay çizer; uzun kategori adları daha rahat okunur."),
    ("plt.scatter(", "plt.scatter(x, y)",
     "Her satırı bir nokta olarak çizer; iki sayısal değişkenin "
     "ilişkisini gösterir."),
    ("plt.hist(", "plt.hist(değerler)",
     "Değerleri aralıklara böler ve her aralıktaki sıklığı çizer."),
    ("plt.boxplot(", "plt.boxplot(veri)",
     "Grup başına medyan, çeyrekler ve aykırı değerleri çizer."),
    ("plt.violinplot(", "plt.violinplot(veri)",
     "Dağılımın yoğunluğunu simetrik bir gövde olarak çizer."),
    ("plt.pie(", "plt.pie(değerler, labels=)",
     "Her değeri bir dilim olarak çizer; `labels` kategori adlarını verir."),
    ("plt.imshow(", "plt.imshow(matriks)",
     "Bir matrisi renkli görüntü olarak çizer; ısı haritasının "
     "temelidir."),
    ("sns.lineplot(", "sns.lineplot(...)",
     "Çizgi grafiği; `x=` ve `y=` sütun adlarıyla verilir."),
    ("sns.barplot(", "sns.barplot(...)",
     "Çubuk grafiği; hazırlanmış özet değerlerle çalışır."),
    ("sns.scatterplot(", "sns.scatterplot(...)",
     "Dağılım grafiği; `hue=` ile gruplar ayrı renge ayrılır."),
    ("sns.histplot(", "sns.histplot(...)",
     "Histogram; `kde=True` yumuşatılmış yoğunluk eğrisi ekler."),
    ("sns.boxplot(", "sns.boxplot(...)",
     "Kutu grafiği; `x` ve `y` sütun adlarıyla verilir."),
    ("sns.violinplot(", "sns.violinplot(...)",
     "Keman grafiği; `inner=` gövdenin içindeki özeti seçer."),
    ("sns.heatmap(", "sns.heatmap(...)",
     "Korelasyon matrisini renkli hücreler olarak çizer."),
    ("kind='line'", "kind='line'",
     "pandas'ın `.plot()` çağrısına çizgi grafiği çizmesini söyler."),
    ("kind='area'", "kind='area'",
     "pandas'ın `.plot()` çağrısına alan grafiği çizmesini söyler."),
    ("kind='barh'", "kind='barh'",
     "pandas'a yatay çubuk grafiği çizmesini söyler."),
    ("kind='bar'", "kind='bar'",
     "pandas'ın `.plot()` çağrısına çubuk grafiği çizmesini söyler."),
    ("kind='hist'", "kind='hist'",
     "pandas'ın `.plot()` çağrısına histogram çizmesini söyler."),
    ("kind='pie'", "kind='pie'",
     "pandas'a pasta grafiği çizmesini söyler."),
    ("stacked=True", "stacked=True",
     "Alan veya çubukları üst üste yığar; katmanların toplamı görünür."),
    ("drawstyle=", "drawstyle=",
     "Çizgiyi basamaklı çizer: 'steps-pre', 'steps-mid' ya da "
     "'steps-post'."),
    ("where=", "where=",
     "Basamağın hangi noktada kırılacağını belirler."),
    ("plt.text(", "plt.text(x, y, ...)",
     "Grafiğin içine, verilen konuma yazı yazar. Değer etiketleri "
     "böyle eklenir."),
    (".plot(", ".plot(...)",
     "pandas'ın hazır çizim arayüzü; arka planda matplotlib'i kullanır. "
     "Hızlı bakış için pratiktir, ince ayarda sınırlıdır."),
    (".plot.scatter(", ".plot.scatter(x=, y=)",
     "pandas'ın dağılım grafiği; iki sütun adı doğrudan verilir."),
    ("autopct=", "autopct=",
     "Pasta dilimlerinin üstüne yüzde yazar ('%1.0f%%' gibi)."),
    ("startangle=", "startangle=",
     "İlk dilimin başlangıç açısı; 90 ile saat 12'den başlar."),
    ("explode=", "explode=",
     "Dilimleri merkezden koparır; vurgulanacak dilim öne çıkar."),
    ("shadow=True", "shadow=True",
     "Pasta grafiğine hafif gölge ekler."),
    ("plt.title(", "plt.title(...)",
     "Grafiğin başlığını yazar. Ne anlattığını tek satırda söyler."),
    ("plt.xlabel(", "plt.xlabel(...)",
     "Yatay eksenin etiketini yazar; birim varsa buraya eklenir."),
    ("plt.ylabel(", "plt.ylabel(...)",
     "Dikey eksenin etiketini yazar."),
    ("plt.grid(", "plt.grid(...)",
     "Izgara çizgilerini açar; `alpha` saydamlığıdır."),
    ("plt.legend(", "plt.legend(...)",
     "Hangi rengin hangi gruba ait olduğunu gösteren göstergedir."),
    ("plt.xticks(", "plt.xticks(...)",
     "x ekseni etiketlerini düzenler; `rotation=45` uzun adları "
     "yatırır."),
    ("plt.colorbar(", "plt.colorbar()",
     "Renk skalasının yanına değer ölçeği ekler."),
    ("plt.suptitle(", "plt.suptitle('')",
     "pandas'ın kendiliğinden eklediği üst başlığı temizler."),
    ("for i, (ad, grup) in enumerate(", "for ... in enumerate(...)",
     "Grupları tek tek dolaşır; her grup için ayrı renkte bir seri "
     "çizer."),
    ("for i, katman in enumerate(", "for ... in enumerate(...)",
     "Her yığın katmanını sırayla çizer ve bir öncekinin üstüne koyar."),
    ("for i, deger in enumerate(", "for ... in enumerate(...)",
     "Değerleri sırayla dolaşır; her birinin üstüne etiket yazar."),
    ("bottom=", "bottom=",
     "Yığılmış çubukta katmanın oturacağı taban yüksekliği."),
    ("marker=", "marker=",
     "Çizgi veya nokta için işaret biçimi: 'o' daire, 's' kare, "
     "'^' üçgen."),
    ("linewidth=", "linewidth=",
     "Çizginin kalınlığı."),
    ("linestyle=", "linestyle=",
     "Çizgi biçimi: düz, kesikli, noktalı ya da nokta-çizgi."),
    ("s=", "s=",
     "Noktanın alanı (boyutu)."),
    ("color=", "color=",
     "Tek bir renk verir; hex kodu (#4C72B0) ya da renk adı olabilir."),
    ("alpha=", "alpha=",
     "Saydamlık: 0 görünmez, 1 tam opak. Kalabalık veride üst üste "
     "binen noktaları ayırır."),
    ("width=", "width=",
     "Çubuğun genişliği; aralarında boşluk bırakmak için küçültülür."),
    ("bins=", "bins=",
     "Histogramdaki aralık sayısı. Az bins kaba, çok bins gürültülü "
     "görünür."),
    ("kde=True", "kde=True",
     "Dağılımın yumuşatılmış yoğunluk eğrisini ekler."),
    ("cumulative=True", "cumulative=True",
     "Eşik altında kalan gözlemlerin toplamını gösterir (birikimli "
     "dağılım)."),
    ("density=True", "density=True",
     "Alanı 1'e normalize eder; farklı örneklemler karşılaştırılabilir."),
    ("stat='density'", "stat='density'",
     "seaborn'da histogramı yoğunluğa çevirir."),
    ("palette=", "palette=",
     "Kategorilerin renk paletini seçer."),
    ("cmap=", "cmap=",
     "Isı haritasının renk skalası."),
    ("annot=True", "annot=True",
     "Isı haritasında hücrelerin üstüne sayısal değeri yazar."),
    ("vmin=", "vmin=, vmax=",
     "Renk skalasının alt ve üst sınırı. Korelasyonda -1..+1 "
     "sabitlenir."),
    ("mask=", "mask=",
     "Matrisin belirtilen hücrelerini gizler; üst üçgeni kaldırmak "
     "için kullanılır."),
    ("np.triu(", "np.triu(...)",
     "Matrisin üst üçgenini seçer; tekrar eden yarıyı gizlemek için "
     "maske üretir."),
    ("linewidths=", "linewidths=",
     "Isı haritasında hücreler arasına ince ayırıcı koyar."),
    ("hue=", "hue=",
     "Grupları renkle ayırır; göstergesi kendiliğinden gelir."),
    ("inner=", "inner=",
     "Keman gövdesinin içinde gösterilecek özet: kutu, çeyrek, nokta "
     "veya çubuk."),
    ("cut=", "cut=",
     "Keman gövdesinin uçlardan ne kadar taşacağını belirler."),
    ("showmeans=True", "showmeans=True",
     "Kutu/keman grafiğinde ortalamayı ayrıca işaretler."),
    ("showfliers=False", "showfliers=False",
     "Aykırı değerleri gizler; gövde daha okunur olur."),
    ("vert=False", "vert=False",
     "Kutuları yatay çizer."),
    ("errorbar=None", "errorbar=None",
     "seaborn'un çizgiye eklediği güven aralığı gölgesini kapatır."),
    ("patch_artist=True", "patch_artist=True",
     "Kutu grafiğinde kutuların içini renklendirmeyi mümkün kılar."),
    ("edgecolor=", "edgecolor=",
     "Çubukların kenar rengi; beyaz ince ayırıcı okumayı kolaylaştırır."),
    ("edgecolors=", "edgecolors=",
     "Noktaların kenar rengi; beyaz kenar kalabalıkta ayrımı artırır."),
    ("rotation=45", "rotation=45",
     "Uzun kategori adlarını 45 derece yatırır; üst üste binmeyi önler."),
    ("figsize=", "figsize=",
     "Grafiğin inç cinsinden (genişlik, yükseklik) değeri."),
]


def anahtar_kelimeler(kod: str) -> list[dict]:
    """Kodda geçen önemli komutları, kısa açıklamalarıyla döndürür.

    Sözlükteki her parça kodda aranır; bulunanlar temelden ayrıntıya doğru
    sözlük sırasıyla döner. `color=` gibi parçaların `edgecolor=` içinde
    yanlışlıkla eşleşmemesi için özel adların önünde kelime sınırı aranır.
    """
    bulunanlar: list[dict] = []
    for parca, ad, aciklama in _SOZLUK:
        if parca.endswith("="):
            desen = r"(?<![\w.])" + re.escape(parca)
        else:
            desen = re.escape(parca)
        if re.search(desen, kod):
            bulunanlar.append({"ad": ad, "aciklama": aciklama})
    return bulunanlar


# --------------------------------------------------------------------------- #
# Çalıştırma
# --------------------------------------------------------------------------- #

class CizimHatasi(Exception):
    """Üretilen kod çalışmadığında fırlatılır."""


def calistir(df: pd.DataFrame, kod: str) -> tuple[str, object]:
    """Kodu çalıştırır; ("figure" | "styler", nesne) döndürür."""
    plt.close("all")
    matplotlib.rcdefaults()
    ortam = {"df": df, "pd": pd, "np": np, "plt": plt, "sns": sns}
    try:
        exec(compile(kod, "<adım adım kod>", "exec"), ortam)
    except Exception as hata:
        plt.close("all")
        raise CizimHatasi(f"{type(hata).__name__}: {hata}") from hata

    if ortam.get("stil") is not None:
        return "styler", ortam["stil"]
    fig = plt.gcf()
    if not fig.get_axes():
        plt.close("all")
        raise CizimHatasi("Kod çalıştı ama bir grafik üretmedi.")
    return "figure", fig


def kapat() -> None:
    plt.close("all")
