"""Grafik Atölyesi — adım adım grafik kodu yazma aracı.

Çalıştırmak için bu klasörde:
    streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from cb import detect, grafik_kodu, loader

st.set_page_config(
    page_title="Grafik Atölyesi",
    page_icon="📊",
    layout="wide",
)

KLASOR = Path(__file__).resolve().parent
ORNEK_KLASORU = KLASOR / "Data"
YOK = "(yok)"


# --------------------------------------------------------------------------- #
# Yardımcılar
# --------------------------------------------------------------------------- #

def _fig_goster(fig, alt: str) -> None:
    try:
        st.pyplot(fig, width="stretch", alt=alt)
    except TypeError:
        st.pyplot(fig)


def _tablo_goster(df, alt: str) -> None:
    try:
        st.dataframe(df, width="stretch", hide_index=True, alt=alt)
    except TypeError:
        st.dataframe(df, width="stretch", hide_index=True)


def _ornek_dosyalar() -> list[Path]:
    if not ORNEK_KLASORU.exists():
        return []
    return sorted(ORNEK_KLASORU.glob("*.csv"))


def _varsayilan(secenekler: list[str], tercih: list[str]) -> int:
    for ad in tercih:
        if ad in secenekler:
            return secenekler.index(ad)
    return 0


def _yuvarla(seri: pd.Series, ondalik: int = 2):
    if not seri.notna().any():
        return None
    return round(float(seri.mean()), ondalik)


def _ozet_sayisal(df: pd.DataFrame, turler: dict[str, str]) -> pd.DataFrame:
    satirlar = []
    for ad in [a for a, t in turler.items() if t == detect.SAYISAL]:
        s = df[ad]
        satirlar.append({
            "Sütun": ad,
            "Dolu": int(s.notna().sum()),
            "Eksik": int(s.isna().sum()),
            "Benzersiz": int(s.nunique()),
            "Ortalama": _yuvarla(s),
            "Medyan": round(float(s.median()), 2) if s.notna().any() else None,
            "Std": round(float(s.std()), 2) if s.notna().sum() > 1 else None,
            "Min": round(float(s.min()), 2) if s.notna().any() else None,
            "Maks": round(float(s.max()), 2) if s.notna().any() else None,
        })
    return pd.DataFrame(satirlar)


def _ozet_kategorik(df: pd.DataFrame, turler: dict[str, str]) -> pd.DataFrame:
    satirlar = []
    for ad in [a for a, t in turler.items() if t == detect.KATEGORIK]:
        s = df[ad]
        sayim = s.value_counts(dropna=True)
        satirlar.append({
            "Sütun": ad,
            "Benzersiz": int(s.nunique()),
            "Eksik": int(s.isna().sum()),
            "En sık değer": str(sayim.index[0]) if len(sayim) else None,
            "Sıklık": int(sayim.iloc[0]) if len(sayim) else None,
        })
    return pd.DataFrame(satirlar)


def _ozet_metin(df: pd.DataFrame, turler: dict[str, str]) -> pd.DataFrame:
    satirlar = []
    for ad in [a for a, t in turler.items() if t == detect.METIN]:
        s = df[ad].dropna().astype(str)
        satirlar.append({
            "Sütun": ad,
            "Benzersiz": int(s.nunique()),
            "Eksik": int(df[ad].isna().sum()),
            "Ort. uzunluk": round(float(s.str.len().mean()), 1) if len(s) else None,
            "Örnek": ", ".join(s.head(2).tolist()),
        })
    return pd.DataFrame(satirlar)


def _ozet_tarih(df: pd.DataFrame, turler: dict[str, str]) -> pd.DataFrame:
    satirlar = []
    for ad in [a for a, t in turler.items() if t == detect.TARIH]:
        s = df[ad]
        satirlar.append({
            "Sütun": ad,
            "Benzersiz": int(s.nunique()),
            "Eksik": int(s.isna().sum()),
            "En erken": str(s.min()) if s.notna().any() else None,
            "En geç": str(s.max()) if s.notna().any() else None,
        })
    return pd.DataFrame(satirlar)


def _secim(etiket: str, adaylar: list[str], tercih: list[str],
           anahtar: str, bos: bool = False,
           yardim: str | None = None) -> str | None:
    if not adaylar:
        return None
    secenekler = ([YOK] + adaylar) if bos else list(adaylar)
    indeks = 0 if bos else _varsayilan(secenekler, tercih)
    secim = st.selectbox(etiket, options=secenekler, index=indeks,
                         key=anahtar, help=yardim)
    return None if secim == YOK else secim


def _uygun_grafikler(turler: dict[str, str]) -> dict[str, str]:
    """Veri türlerine göre çizilebilecek tüm grafik türleri.

    Veri türlerine göre çizilebilecek türleri belirler; iki sayısal
    sütun gerektiren grafikler ayrıca koşullandırılır.
    """
    sayisal = [a for a, t in turler.items() if t == detect.SAYISAL]
    kategori = [a for a, t in turler.items()
                if t in (detect.KATEGORIK, detect.TARIH)]

    uygun: dict[str, str] = {}
    if sayisal:
        uygun["hist"] = grafik_kodu.GRAFIKLER["hist"]
        uygun["box"] = grafik_kodu.GRAFIKLER["box"]
        uygun["violin"] = grafik_kodu.GRAFIKLER["violin"]
    if len(sayisal) >= 2:
        uygun["scatter"] = grafik_kodu.GRAFIKLER["scatter"]
        uygun["heatmap"] = grafik_kodu.GRAFIKLER["heatmap"]
    if sayisal and kategori:
        for anahtar in ("line", "step", "area", "bar", "pie"):
            uygun[anahtar] = grafik_kodu.GRAFIKLER[anahtar]
    if sayisal and len(kategori) >= 2:
        uygun["stacked"] = grafik_kodu.GRAFIKLER["stacked"]
    return uygun


def _eksen_secenekleri(turler: dict[str, str], grafik: str) -> dict:
    """Grafik türüne göre eksen adaylarını döndürür.

    Basamak, alan, pasta, yığılmış çubuk ve keman için de aday listesi
    üretilir; grafik üreticisi kodunu kendi içinde tutar.
    """
    sayisal = [a for a, t in turler.items() if t == detect.SAYISAL]
    kategori = [a for a, t in turler.items()
                if t in (detect.KATEGORIK, detect.TARIH)]

    if grafik in ("line", "step", "area"):
        return {"x": kategori + sayisal, "y": sayisal, "hue": kategori}
    if grafik == "bar":
        return {"x": kategori, "y": sayisal, "hue": []}
    if grafik == "stacked":
        return {"x": kategori, "y": sayisal, "hue": kategori}
    if grafik == "pie":
        return {"x": kategori, "y": sayisal, "hue": []}
    if grafik == "scatter":
        return {"x": sayisal, "y": sayisal, "hue": kategori}
    if grafik == "hist":
        return {"x": sayisal, "y": [], "hue": []}
    if grafik in ("box", "violin"):
        return {"x": kategori, "y": sayisal, "hue": []}
    if grafik == "heatmap":
        return {"x": sayisal, "y": [], "hue": []}
    return {"x": [], "y": [], "hue": []}


# --------------------------------------------------------------------------- #
# 0 · Veri kaynağı
# --------------------------------------------------------------------------- #

st.title("📊 Grafik Atölyesi")
st.caption(
    "Veriyi tanı, sütun türlerini düzelt, sonra grafiği adım adım kur: "
    "her özellik koda yeni bir satır ekler."
)

with st.sidebar:
    st.header("0 · Veri")
    yuklenen = st.file_uploader(
        "CSV veya Excel dosyası", type=["csv", "xlsx", "xls"], key="aa_dosya"
    )
    ornekler = _ornek_dosyalar()
    secilen_ornek = None
    if ornekler and yuklenen is None:
        secilen_ornek = st.selectbox(
            "…ya da örnek veri setlerinden biri",
            options=[p.name for p in ornekler],
            key="aa_ornek",
        )

icerik: bytes | None = None
dosya_adi: str | None = None
if yuklenen is not None:
    icerik = yuklenen.getvalue()
    dosya_adi = yuklenen.name
elif secilen_ornek:
    yol = ORNEK_KLASORU / secilen_ornek
    icerik = yol.read_bytes()
    dosya_adi = yol.name

if icerik is None or dosya_adi is None:
    st.info(
        "Başlamak için soldan bir dosya yükle ya da örnek "
        "verilerden birini seç."
    )
    st.markdown(
        """
        **Akış nasıl işliyor?**

        1. Dosya okunur, her sütunun türü tahmin edilir.
        2. Sayısal, kategorik, metin ve tarih sütunları ayrı ayrı listelenir.
        3. Kütüphaneyi ve grafik türünü seçersin.
        4. Başlık, renk, işaretçi gibi özellikleri tek tek açtıkça kod
           büyür; her adımın ne yaptığını yanında okursun.
        """
    )
    st.stop()

try:
    sayfalar = loader.oku(icerik, dosya_adi)
except loader.OkumaHatasi as hata:
    st.error(str(hata))
    st.stop()

with st.sidebar:
    if len(sayfalar) > 1:
        sayfa = st.selectbox("Excel sayfası", options=list(sayfalar),
                             key="aa_sayfa")
    else:
        sayfa = next(iter(sayfalar))
    ham = loader.bos_satirlari_at(sayfalar[sayfa])
    st.caption(f"{ham.shape[0]} satır · {ham.shape[1]} sütun")

if ham.empty:
    st.error("Tabloda okunabilir satır kalmadı; dosyayı kontrol et.")
    st.stop()


# --------------------------------------------------------------------------- #
# 1 · Veriyi tanı
# --------------------------------------------------------------------------- #

st.subheader("1 · Veriyi tanı")
st.markdown(
    "Her sütun bir türe ayrıldı. Yanlış bulduğun türü aşağıdan değiştir; "
    "hem istatistikler hem grafik seçenekleri anında güncellenir."
)

imza = f"{dosya_adi}|{sayfa}|{ham.shape[0]}x{ham.shape[1]}"
tanima = detect.tanima_tablosu(ham)

with st.expander("Sütun türlerini düzelt", expanded=False):
    duzenlenen = st.data_editor(
        tanima,
        hide_index=True,
        key=f"aa_tur_{imza}",
        disabled=["Sütun", "pandas türü", "Benzersiz", "Eksik",
                  "Örnek değerler"],
        column_config={
            "Tür": st.column_config.SelectboxColumn(
                "Tür",
                help="Grafik seçeneklerini ve istatistikleri bu belirler.",
                options=detect.TURLER,
                required=True,
                width="small",
            ),
            "Benzersiz": st.column_config.NumberColumn(width="small"),
            "Eksik": st.column_config.NumberColumn(width="small"),
            "Örnek değerler": st.column_config.TextColumn(width="large"),
        },
    )

turler = dict(zip(duzenlenen["Sütun"], duzenlenen["Tür"]))
df, donusum_uyarilari = detect.uygula(ham, turler)
for uyari in donusum_uyarilari:
    st.warning(uyari, icon="⚠️")

sekme_s, sekme_k, sekme_m, sekme_t = st.tabs(
    ["Sayısal", "Kategorik", "Metin", "Tarih"]
)

with sekme_s:
    st.caption(
        "Histogram ve kutu grafiği tek başına; dağılım ve ısı haritası iki "
        "sayısal sütun ister."
    )
    ozet = _ozet_sayisal(df, turler)
    if ozet.empty:
        st.info("Sayısal sütun yok.")
    else:
        _tablo_goster(ozet, "Sayısal sütunların özet istatistikleri")

with sekme_k:
    st.caption(
        "Çubuk ve çizgi grafiğinde x ekseni olur; dağılım ve çizgide "
        "renkle gruplama (hue) için kullanılır."
    )
    ozet = _ozet_kategorik(df, turler)
    if ozet.empty:
        st.info("Kategorik sütun yok.")
    else:
        _tablo_goster(ozet, "Kategorik sütunların özeti")

with sekme_m:
    st.caption(
        "Serbest metin (ad, not, açıklama) eksene konmaz; temizleme ve "
        "sayım için uygundur."
    )
    ozet = _ozet_metin(df, turler)
    if ozet.empty:
        st.info("Metin sütunu yok.")
    else:
        _tablo_goster(ozet, "Metin sütunlarının özeti")

with sekme_t:
    st.caption(
        "Çizgi grafiğinde zaman ekseni olur. Tarih değilse türü buradan "
        "düzeltebilirsin."
    )
    ozet = _ozet_tarih(df, turler)
    if ozet.empty:
        st.info("Tarih sütunu yok.")
    else:
        _tablo_goster(ozet, "Tarih sütunlarının aralığı")


# --------------------------------------------------------------------------- #
# 2 · Kütüphane, grafik ve eksenler
# --------------------------------------------------------------------------- #

uygun_tum = _uygun_grafikler(turler)
if not uygun_tum:
    st.error(
        "Bu tabloyla çizilebilecek bir grafik bulunamadı. En az bir "
        "**sayısal** sütun gerekiyor; yukarıdan türleri düzeltmeyi dene."
    )
    st.stop()

ayarlar = grafik_kodu.varsayilan_ayarlar()

with st.sidebar:
    st.header("1 · Kütüphane")
    ayarlar["kutuphane"] = st.selectbox(
        "Hangi kütüphaneyle çizelim?",
        options=list(grafik_kodu.KUTUPHANELER),
        format_func=lambda k: grafik_kodu.KUTUPHANELER[k],
        key="aa_kutuphane",
        help="Kod, seçtiğin kütüphanenin sözdizimiyle yazılır.",
    )

kutuphane = ayarlar["kutuphane"]
kutuphane_grafik = grafik_kodu.kutuphane_grafikleri(kutuphane)
uygun = {k: v for k, v in uygun_tum.items() if k in kutuphane_grafik}

if not uygun:
    st.warning(
        f"Bu tabloyla **{grafik_kodu.KUTUPHANELER[kutuphane]}** kullanılarak "
        "çizilebilecek grafik yok. Başka bir kütüphane seçmeyi dene."
    )
    st.stop()

with st.sidebar:
    st.header("2 · Grafik türü")
    secenekler = list(uygun)
    if st.session_state.get("aa_grafik") not in secenekler:
        st.session_state["aa_grafik"] = secenekler[
            _varsayilan(secenekler,
                        ["line", "bar", "scatter", "hist", "box", "heatmap",
                         "step", "area", "pie", "violin"])
        ]
    ayarlar["grafik"] = st.selectbox(
        "Ne çizeceğiz?",
        options=secenekler,
        format_func=lambda k: uygun[k],
        key="aa_grafik",
    )
    eksik_turler = [
        grafik_kodu.GRAFIKLER[k] for k in grafik_kodu.GRAFIKLER
        if k not in kutuphane_grafik
    ]
    if eksik_turler:
        st.caption(
            f"Bu kütüphanede yok: {', '.join(e.lower() for e in eksik_turler)}."
        )

grafik = ayarlar["grafik"]
eksen = _eksen_secenekleri(turler, grafik)

with st.sidebar:
    st.header("3 · Eksenler")

    if grafik == "heatmap":
        varsayilan_sutunlar = list(eksen["x"][: min(8, len(eksen["x"]))])
        ayarlar["sutunlar"] = st.multiselect(
            "Korelasyonu hesaplanacak sayısal sütunlar",
            options=eksen["x"],
            default=varsayilan_sutunlar,
            key="aa_sutunlar",
            help="En az iki sütun seç.",
        )
        ayarlar["x"] = ayarlar["y"] = ayarlar["hue"] = None

    elif grafik in ("box", "violin"):
        ayarlar["y"] = _secim(
            "y ekseni (değer)", eksen["y"],
            ["vize_notu", "adet", "ciro", "musteri_bin"],
            anahtar=f"aa_{grafik}_y",
        )
        ayarlar["x"] = _secim(
            "Gruplama sütunu (x)", eksen["x"],
            ["bolum", "sehir", "urun"],
            anahtar=f"aa_{grafik}_x", bos=True,
            yardim="Boş bırakırsan tek bir gövde çizilir.",
        )
        ayarlar["hue"] = None

    elif grafik == "hist":
        ayarlar["x"] = _secim(
            "Değer sütunu (x)", eksen["x"],
            ["adet", "yas", "vize_notu", "calisma_saati", "haftalik_kahve"],
            anahtar="aa_hist_x",
        )
        ayarlar["y"] = ayarlar["hue"] = None

    else:
        ayarlar["x"] = _secim(
            "x ekseni", eksen["x"],
            ["ay", "date", "tarih", "sehir", "urun", "bolum"],
            anahtar=f"aa_x_{grafik}",
        )
        y_tercih = [
            c for c in ["adet", "ciro", "musteri_bin", "vize_notu",
                        "birim_fiyat", "yas", "haftalik_kahve"]
            if c != ayarlar["x"]
        ]
        y_adaylar = [c for c in eksen["y"] if c != ayarlar["x"]]
        ayarlar["y"] = _secim(
            "y ekseni", y_adaylar, y_tercih,
            anahtar=f"aa_y_{grafik}",
            yardim="x için seçtiğin sütun burada görünmez.",
        )
        hue_adaylar = [c for c in eksen["hue"] if c != ayarlar["x"]]
        hue_zorunlu = grafik == "stacked"
        if hue_adaylar:
            ayarlar["hue"] = _secim(
                "Renkle ayır (hue)", hue_adaylar, [],
                anahtar=f"aa_hue_{grafik}", bos=not hue_zorunlu,
                yardim=("Yığılmış çubuk için zorunlu: ikinci kategori "
                        "katmanları belirler." if hue_zorunlu else
                        "Grupları renkle ayırmak istersen bir sütun seç."),
            )
        else:
            ayarlar["hue"] = None


# --------------------------------------------------------------------------- #
# 3 · Özellikler (her biri koda satır ekler)
# --------------------------------------------------------------------------- #

a = ayarlar
izin = grafik_kodu.izinli(a)
hue = a["hue"]
ay_var = bool(a["x"]) and a["x"] in df.columns and grafik_kodu.ay_mi(df[a["x"]])

with st.sidebar:
    st.header("4 · Özellikler")
    st.caption(
        "Hiçbirini işaretlemezsen sadece çizim satırı olur. Her işaret "
        "koda yeni bir satır ekler."
    )

    # --- veriyi hazırlama ---
    if "toplama" in izin:
        a["toplama"] = st.selectbox(
            "Özetleme", options=list(grafik_kodu.TOPLAMALAR),
            format_func=lambda k: grafik_kodu.TOPLAMALAR[k],
            key="aa_toplam",
            help="Her kategori için tek bir değer hesaplanır.",
        )
    if "zaman" in izin and ay_var:
        a["zaman_on"] = st.checkbox(
            "Ayları takvim sırasına diz", value=False,
            key="aa_zaman_on",
            help="Ay adları metin olduğu için varsayılan sıralama "
                 "alfabetiktir; bu seçenek Ocak→Aralık sırasını kurar.",
        )
        a["sirala_on"] = False
    elif "sirala" in izin:
        a["sirala_on"] = st.checkbox("Sırala", value=True, key="aa_sirala_on")

    # --- grafiğe özel ---
    if "toplama" in izin:
        a["toplama"] = st.selectbox(
            "Özetleme", options=list(grafik_kodu.TOPLAMALAR),
            format_func=lambda k: grafik_kodu.TOPLAMALAR[k],
            key="aa_toplam",
            help="Her kategori için tek bir değer hesaplanır.",
        )

    ozel = izin & {"bins", "kde", "kumulatif", "yogunluk", "isaret",
                   "nokta", "kenar", "stil", "basamak", "dolg", "yigin",
                   "cizgi", "yatay", "cubuk_genislik", "deger",
                   "yuzde_yigin", "pasta_yuzde", "baslangic", "patlama",
                   "golge", "cmap", "annot", "ucgen", "hucre",
                   "renk_cubugu", "ortalama", "aykiri_gizle", "ic",
                   "kesme", "palet"}
    if ozel:
        st.markdown("**Grafiğe özel**")

    # çizgi ailesi
    if "isaret" in izin:
        a["isaret_on"] = st.checkbox("İşaretçi (marker)", value=False,
                                     key="aa_isaret_on")
        if a["isaret_on"]:
            a["marker"] = st.selectbox(
                "İşaretçi biçimi", grafik_kodu.MARKERLAR, key="aa_marker"
            )
    if "cizgi" in izin:
        a["cizgi_on"] = st.checkbox("Çizgi kalınlığı", value=False,
                                    key="aa_cizgi_on")
        if a["cizgi_on"]:
            a["cizgi_kalinligi"] = st.slider(
                "Kalınlık", 0.5, 6.0, 2.0, 0.5, key="aa_cizgi"
            )
    if "stil" in izin:
        a["stil_on"] = st.checkbox("Çizgi biçimi", value=False,
                                   key="aa_stil_on")
        if a["stil_on"]:
            a["stil"] = st.selectbox(
                "Biçim", options=list(grafik_kodu.CIZGI_STILLERI),
                format_func=lambda k: grafik_kodu.CIZGI_STILLERI[k],
                key="aa_stil",
            )
    if "basamak" in izin:
        a["basamak"] = st.selectbox(
            "Basamak konumu", options=list(grafik_kodu.BASAMAKLAR),
            format_func=lambda k: grafik_kodu.BASAMAKLAR[k],
            key="aa_basamak",
        )
    if "dolg" in izin:
        a["dolg_on"] = st.checkbox("Alan saydamlığı", value=False,
                                   key="aa_dolg_on")
        if a["dolg_on"]:
            a["dolg_saydamlik"] = st.slider(
                "Dolgu saydamlığı", 0.1, 1.0, 0.35, 0.05, key="aa_dolg"
            )
    if "yigin" in izin:
        a["yigin_on"] = st.checkbox("Alanları yığ", value=True,
                                    key="aa_yigin_on")

    # çubuk ailesi
    if "yatay" in izin:
        a["yatay_on"] = st.checkbox("Yatay çubuk", value=False,
                                    key="aa_yatay_on")
    if "cubuk_genislik" in izin:
        a["cubuk_genislik_on"] = st.checkbox(
            "Çubuk genişliği", value=False, key="aa_cgen_on")
        if a["cubuk_genislik_on"]:
            a["cubuk_genisligi"] = st.slider(
                "Genişlik", 0.2, 1.0, 0.8, 0.05, key="aa_cgen"
            )
    if "deger" in izin and not a["yatay_on"]:
        a["deger_on"] = st.checkbox("Değerleri çubuk üstüne yaz",
                                    value=False, key="aa_deger_on")
    if "kenar" in izin:
        a["kenar_on"] = st.checkbox("Kenar çizgisi", value=False,
                                    key="aa_kenar_on")
    if "yuzde_yigin" in izin:
        a["yuzde_yigin_on"] = st.checkbox("Yığını %100'e normalize et",
                                          value=False,
                                          key="aa_yuzde_on")

    # dağılım
    if "nokta" in izin:
        a["nokta_on"] = st.checkbox("Nokta boyu", value=False,
                                    key="aa_nokta_on")
        if a["nokta_on"]:
            a["nokta_boyu"] = st.slider(
                "Boyut", 5.0, 200.0, 45.0, 5.0, key="aa_nokta"
            )
    if "bins" in izin:
        a["bins_on"] = st.checkbox("Aralık sayısı (bins)", value=False,
                                   key="aa_bins_on")
        if a["bins_on"]:
            a["bins"] = st.slider("bins", 3, 100, 20, key="aa_bins")
    if "kde" in izin:
        a["kde_on"] = st.checkbox("Yoğunluk eğrisi (kde)", value=False,
                                  key="aa_kde_on")
    if "kumulatif" in izin:
        a["kumulatif_on"] = st.checkbox("Birikimli (kümülatif)",
                                        value=False, key="aa_kum_on")
    if "yogunluk" in izin:
        a["yogunluk_on"] = st.checkbox("Yoğunluğa normalize et",
                                       value=False, key="aa_yog_on")

    # kutu / keman
    if "ortalama" in izin:
        a["ortalama_on"] = st.checkbox("Ortalamayı göster", value=False,
                                       key="aa_ort_on")
    if "aykiri_gizle" in izin:
        a["aykiri_gizle_on"] = st.checkbox("Aykırı değerleri gizle",
                                           value=False,
                                           key="aa_aykiri_on")
    if "ic" in izin:
        a["ic_on"] = st.checkbox("İç gösterimi seç", value=False,
                                 key="aa_ic_on")
        if a["ic_on"]:
            a["ic"] = st.selectbox(
                "İç gösterim", options=list(grafik_kodu.IC_GOSTERIM),
                format_func=lambda k: grafik_kodu.IC_GOSTERIM[k],
                key="aa_ic",
            )
    if "kesme" in izin:
        a["kesme_on"] = st.checkbox("Gövdeyi uçlardan kes", value=False,
                                    key="aa_kesme_on")
        if a["kesme_on"]:
            a["kesme"] = st.slider("Kesme", 0, 5, 2, key="aa_kesme")

    # pasta
    if "pasta_yuzde" in izin:
        a["pasta_yuzde_on"] = st.checkbox("Dilimlere yüzde yaz",
                                          value=False, key="aa_pyuzde_on")
    if "baslangic" in izin:
        a["baslangic_on"] = st.checkbox("Başlangıç açısı", value=False,
                                        key="aa_pbas_on")
        if a["baslangic_on"]:
            a["baslangic"] = st.slider("Açı", 0, 360, 90, 15,
                                       key="aa_pbas")
    if "patlama" in izin:
        a["patlama_on"] = st.checkbox("Dilimleri ayır (explode)",
                                      value=False, key="aa_pat_on")
        if a["patlama_on"]:
            a["patlama"] = st.slider("Ayrılma", 0.0, 0.3, 0.05, 0.01,
                                     key="aa_pat")
    if "golge" in izin:
        a["golge_on"] = st.checkbox("Gölge", value=False, key="aa_golge_on")

    # ısı haritası
    if "cmap" in izin:
        a["cmap"] = st.selectbox(
            "Renk haritası", grafik_kodu.CMAPLER, key="aa_cmap"
        )
    if "annot" in izin:
        a["annot_on"] = st.checkbox("Hücre değerlerini yaz", value=False,
                                    key="aa_annot_on")
    if "ucgen" in izin:
        a["ucgen_on"] = st.checkbox("Üst üçgeni gizle", value=False,
                                    key="aa_ucgen_on")
    if "hucre" in izin:
        a["hucre_on"] = st.checkbox("Hücre çizgileri", value=False,
                                    key="aa_hucre_on")
    if "renk_cubugu" in izin:
        a["renk_cubugu_on"] = st.checkbox("Renk çubuğu (colorbar)",
                                          value=False,
                                          key="aa_cbar_on")

    # palet (gruplu grafikler)
    if "palet" in izin and hue:
        a["palet_on"] = st.checkbox("Renk paleti", value=False,
                                    key="aa_palet_on")
        if a["palet_on"]:
            a["palet"] = st.selectbox(
                "Palet", grafik_kodu.PALETLER, key="aa_palet"
            )

    # --- eksenler ve başlıklar ---
    st.markdown("**Başlık ve eksenler**")
    if "baslik" in izin:
        if st.checkbox("Grafik başlığı", value=False, key="aa_baslik_on"):
            a["baslik"] = st.text_input("Başlık metni", key="aa_baslik") or None
    if "x_etiketi" in izin:
        if st.checkbox("x ekseni etiketi", value=False, key="aa_xe_on"):
            a["x_etiketi"] = st.text_input(
                "x etiketi", key="aa_xe"
            ) or None
    if "y_etiketi" in izin:
        if st.checkbox("y ekseni etiketi", value=False, key="aa_ye_on"):
            a["y_etiketi"] = st.text_input(
                "y etiketi", key="aa_ye"
            ) or None

    # --- görünüm ---
    st.markdown("**Görünüm**")
    if "renk" in izin and not hue:
        a["renk_on"] = st.checkbox("Renk seç", value=False,
                                   key="aa_renk_on")
        if a["renk_on"]:
            a["renk"] = st.color_picker("Renk", "#4C72B0", key="aa_renk")
    if "saydamlik" in izin:
        a["saydamlik_on"] = st.checkbox("Saydamlık", value=False,
                                        key="aa_saydamlik_on")
        if a["saydamlik_on"]:
            a["saydamlik"] = st.slider(
                "Değer", 0.2, 1.0, 0.85, 0.05, key="aa_saydamlik"
            )
    if "izgara" in izin:
        a["izgara_on"] = st.checkbox("Izgara çizgileri", value=False,
                                     key="aa_izgara_on")
    if "donus" in izin:
        a["donus_on"] = st.checkbox("Etiketleri 45° döndür", value=False,
                                    key="aa_donus_on")
    if hue and "gosterge" in izin:
        a["gosterge_on"] = st.checkbox("Gösterge (legend)", value=True,
                                       key="aa_gosterge_on")
    if "boyut" in izin:
        a["boyut_on"] = st.checkbox("Şekil boyutu", value=False,
                                    key="aa_boyut_on")
        if a["boyut_on"]:
            a["genislik"] = st.slider(
                "Genişlik (inç)", 4.0, 20.0, 8.0, 0.5, key="aa_genislik"
            )
            a["yukseklik"] = st.slider(
                "Yükseklik (inç)", 2.5, 14.0, 4.5, 0.5, key="aa_yukseklik"
            )
    if "tema" in izin:
        a["tema_on"] = st.checkbox("seaborn teması", value=False,
                                   key="aa_tema_on")
        if a["tema_on"]:
            a["tema"] = st.selectbox(
                "Tema", grafik_kodu.TEMALAR, key="aa_tema",
                help="Yalnızca seaborn kodu için geçerli.",
            )


# --------------------------------------------------------------------------- #
# 4 · Kod ve önizleme
# --------------------------------------------------------------------------- #

st.subheader("2 · Kodu adım adım yaz")

sonuc = grafik_kodu.uret(a, df, dosya_adi=dosya_adi)

if not sonuc["hazir"]:
    st.info(sonuc["mesaj"])
    st.stop()

# 1 · Sabit giriş satırları --------------------------------------------------
with st.container(border=True):
    st.markdown("**1 · Sabit giriş satırları**")
    st.caption(
        "Her dosyada aynı kalan satırlar: kütüphaneleri içe aktarır ve "
        "yüklediğin dosyayı okur."
    )
    st.code(sonuc["giris"], language="python")
    st.caption(
        "Dosya adı yüklediğin dosyadan gelir; Excel yüklediysen okuma "
        "satırı kendiliğinden `pd.read_excel` olur. Kodun çalışacağı "
        "klasörde dosya bu adla bulunmalı."
    )

# 2 · Grafik kodu ------------------------------------------------------------
with st.container(border=True):
    st.markdown("**2 · Grafik kodu**")
    st.caption("Yalnızca grafiği üreten satırlar. Yukarıdan özellik "
               "ekledikçe burası büyür.")
    st.code(sonuc["kod"] or "# Henüz grafik satırı yok.", language="python")

# 3 · Grafik önizleme --------------------------------------------------------
with st.container(border=True):
    st.markdown("**3 · Grafik önizleme**")
    try:
        tur, nesne = grafik_kodu.calistir(df, sonuc["calistir_kod"])
    except grafik_kodu.CizimHatasi as hata:
        st.error("Bu ayarlarla grafik üretilemedi.")
        st.exception(hata)
        st.caption("Eksik değerler ya da tek gruplu veri neden olabilir.")
    else:
        if tur == "figure":
            _fig_goster(nesne, "Seçilen ayarlarla üretilen grafik önizlemesi")
            grafik_kodu.kapat()
        else:
            st.caption(
                "pandas'ta hazır ısı haritası yok; aynı bilgi "
                "**renklendirilmiş tablo** olarak gösteriliyor."
            )
            _tablo_goster(nesne, "Korelasyon tablosu")

# 4 · Tam kod ----------------------------------------------------------------
with st.container(border=True):
    st.markdown("**4 · Tam kod (kopyalamaya hazır)**")
    st.caption("Giriş satırları + grafik kodu. Defterde tek hücreye "
               "yapıştırıp çalıştırabilirsin.")
    st.code(sonuc["tam_kod"], language="python")
    st.download_button(
        "Kodu indir",
        data=sonuc["tam_kod"],
        file_name="grafik.py",
        mime="text/x-python",
        icon=":material/download:",
    )

# 5 · Öğretim alanı ----------------------------------------------------------
with st.container(border=True):
    st.markdown("**5 · Öğretim alanı**")
    st.caption(
        "Grafiğin ne için kullanıldığı, seçtiğin sütunlarla ne gösterdiği, "
        "nasıl okunacağı ve koddaki komutlar."
    )

    rehber = sonuc["rehber"]
    if sonuc["amac"]:
        st.markdown("**Bu grafik ne için kullanılır?**")
        st.markdown(sonuc["amac"])
        if rehber.get("ne_zaman"):
            st.markdown("Uygun olduğu durumlar:")
            for madde in rehber["ne_zaman"]:
                st.markdown(f"- {madde}")

    if sonuc["yorum"]:
        st.markdown("**Seçtiğin sütunlarla bu grafik ne gösteriyor?**")
        st.caption(
            "Aşağıdaki sayılar yüklediğin veriden hesaplandı; sütun ya da "
            "ayar değişince güncellenir."
        )
        for madde in sonuc["yorum"]:
            st.markdown(f"- {madde}")

    if rehber.get("okuma"):
        st.markdown("**Nasıl okunur?**")
        for madde in rehber["okuma"]:
            st.markdown(f"- {madde}")

    if rehber.get("dikkat"):
        st.markdown("**Dikkat**")
        for madde in rehber["dikkat"]:
            st.markdown(f"- {madde}")

    st.divider()
    st.markdown("**Koddaki komutlar**")
    if sonuc["anahtarlar"]:
        for anahtar in sonuc["anahtarlar"]:
            st.markdown(f"- `{anahtar['ad']}` — {anahtar['aciklama']}")
    else:
        st.caption("Kodda açıklanacak özel bir komut yok.")

    st.markdown("**Eklediğin adımlar**")
    if len(sonuc["bloklar"]) <= 1:
        st.caption(
            "Henüz tek adım var: çizim satırı. Yukarıdan özellik ekledikçe "
            "liste büyüyecek."
        )
    for i, blok in enumerate(sonuc["bloklar"], start=1):
        st.markdown(f"{i}. **{blok['ad']}** — {blok['aciklama']}")

st.divider()
st.caption(
    "Grafik Atölyesi · Her özellik koda bir satır ekler · "
    "Kodu kopyalayıp kendi defterinde `df` hazırken çalıştırabilirsin."
)
