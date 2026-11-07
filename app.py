"""Grafik Atölyesi — yükle, tanı, çiz, kodu öğren.

Çalıştırmak için bu klasörde:
    streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from cb import charts, detect, kilavuz, loader

st.set_page_config(
    page_title="Grafik Atölyesi",
    page_icon="📊",
    layout="wide",
)

KLASOR = Path(__file__).resolve().parent
ORNEK_KLASORU = KLASOR / "Data"


# --------------------------------------------------------------------------- #
# Yardımcılar
# --------------------------------------------------------------------------- #

def _fig_goster(fig) -> None:
    """Streamlit sürümüne göre genişlik parametresini uyarlar."""
    try:
        st.pyplot(fig, width="stretch")
    except TypeError:
        st.pyplot(fig, use_container_width=True)


def _tablo_goster(df) -> None:
    try:
        st.dataframe(df, width="stretch")
    except TypeError:
        st.dataframe(df, use_container_width=True)


def _ornek_dosyalar() -> list[Path]:
    if not ORNEK_KLASORU.exists():
        return []
    return sorted(ORNEK_KLASORU.glob("*.csv"))


def _varsayilan(secenekler: list[str], tercih: list[str]) -> int:
    """Listeden ilk uygun tercihi seçer; yoksa 0 döndürür."""
    for ad in tercih:
        if ad in secenekler:
            return secenekler.index(ad)
    return 0


# --------------------------------------------------------------------------- #
# 1. Veri kaynağı
# --------------------------------------------------------------------------- #

st.title("📊 Grafik Atölyesi")
st.caption(
    "Bir CSV ya da Excel dosyası yükle; sütunları tanısın, çizilebilecek "
    "grafikleri göstersin ve her grafiğin Python kodunu üç kütüphanede "
    "ayrı ayrı yazsın."
)

with st.sidebar:
    st.header("1 · Veri")
    yuklenen = st.file_uploader(
        "CSV veya Excel dosyası", type=["csv", "xlsx", "xls"]
    )
    ornekler = _ornek_dosyalar()
    secilen_ornek = None
    if ornekler and yuklenen is None:
        secilen_ornek = st.selectbox(
            "…ya da dersteki örnek verilerden biri",
            options=[p.name for p in ornekler],
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
        "Başlamak için soldan bir dosya yükle ya da dersteki örnek "
        "verilerden birini seç."
    )
    st.markdown(
        """
        **Bu araç ne yapar?**

        1. Dosyayı okur ve her sütunun türünü tahmin eder
           (sayısal, kategorik, metin, tarih).
        2. Seçtiğin türe göre anlamlı grafikleri listeler.
        3. Aynı grafiği **pandas**, **matplotlib** ve **seaborn** ile
           çizer; üçünün kodunu yan yana gösterir.
        4. Grafiğin başlığını, rengini, paletini, işaretçisini
           özelleştirmene izin verir; kod anında buna göre yenilenir.
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
        sayfa = st.selectbox("Excel sayfası", options=list(sayfalar))
    else:
        sayfa = next(iter(sayfalar))
    ham = loader.bos_satirlari_at(sayfalar[sayfa])
    st.caption(f"{ham.shape[0]} satır · {ham.shape[1]} sütun")

if ham.empty:
    st.error("Tabloda okunabilir satır kalmadı; dosyayı kontrol et.")
    st.stop()


# --------------------------------------------------------------------------- #
# 2. Sütun tanıma
# --------------------------------------------------------------------------- #

# Dosya değişince düzenleyici durumu sıfırlansın diye anahtar üretiyoruz.
imza = f"{dosya_adi}|{sayfa}|{ham.shape[0]}x{ham.shape[1]}"

st.subheader("2 · Sütunları tanıyalım")
st.markdown(
    "Aşağıdaki türler **tahmin**. Yanlış bulduğun varsa değiştir; "
    "grafik seçenekleri anında buna göre güncellenir."
)

tanima = detect.tanima_tablosu(ham)
duzenlenen = st.data_editor(
    tanima,
    hide_index=True,
    key=f"tur_duzenleyici_{imza}",
    disabled=["Sütun", "pandas türü", "Benzersiz", "Eksik", "Örnek değerler"],
    column_config={
        "Tür": st.column_config.SelectboxColumn(
            "Tür",
            help="Grafik seçeneklerini bu belirler.",
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

dagilim = {t: sum(1 for x in turler.values() if x == t) for t in detect.TURLER}
st.caption(
    " · ".join(f"**{t}:** {n}" for t, n in dagilim.items() if n)
)

with st.expander(f"Veriyi dataframe olarak gör ({ham.shape[0]} satır × "
                 f"{ham.shape[1]} sütun)"):
    st.caption(
        "Tür dönüşümleri uygulanmış hâli. Boş hücreler `NaN` demektir; "
        "pandas bunları sayısal işlemlerde atlar."
    )
    _tablo_goster(df.head(100))
    if len(df) > 100:
        st.caption(f"İlk 100 satır gösteriliyor (toplam {len(df)}).")
    st.markdown("**Sütun türleri (uygulanmış)**")
    st.code(
        "\n".join(f"{ad}: {str(df[ad].dtype)}" for ad in df.columns),
        language="text",
    )


# --------------------------------------------------------------------------- #
# 3. Grafik seçimi ve ayarlar
# --------------------------------------------------------------------------- #

uygun = charts.uygun_grafikler(turler)
if not uygun:
    st.error(
        "Bu tabloyla çizilebilecek bir grafik bulunamadı. En az bir "
        "**sayısal** sütun gerekiyor; yukarıdaki türleri düzeltmeyi dene."
    )
    st.stop()

with st.sidebar:
    st.header("2 · Grafik")
    secenek_listesi = list(uygun)
    # Seçim, widget'ın kendi anahtarında tutulur. `index` değerini her
    # çalıştırmada seçime göre yeniden hesaplamak, widget kimliğini
    # değiştirip seçimi geri sıfırlar.
    if st.session_state.get("grafik_secimi") not in secenek_listesi:
        st.session_state["grafik_secimi"] = secenek_listesi[
            _varsayilan(secenek_listesi,
                        ["bar", "line", "scatter", "hist", "box", "heatmap"])
        ]
    grafik = st.selectbox(
        "Grafik türü",
        options=secenek_listesi,
        format_func=lambda k: uygun[k],
        key="grafik_secimi",
    )

eksen = charts.eksen_secenekleri(turler, grafik)
izinli = charts.secenekler(grafik)

YOK = "(yok)"


def _secim(etiket: str, adaylar: list[str], tercih: list[str],
           bos_secenek: bool = False, yardim: str | None = None
           ) -> str | None:
    """Bir sütun seçtirir; bos_secenek=True ise '(yok)' seçeneği eklenir."""
    if not adaylar:
        return None
    secenekler = ([YOK] + adaylar) if bos_secenek else adaylar
    varsayilan = _varsayilan(secenekler, tercih if not bos_secenek else [])
    secim = st.selectbox(etiket, options=secenekler, index=varsayilan,
                         help=yardim)
    return None if secim == YOK else secim


with st.sidebar:
    st.markdown("**Eksenler**")
    if grafik == "heatmap":
        varsayilan_sutunlar = [a for a in eksen["x"]][: min(8, len(eksen["x"]))]
        secilen_sutunlar = st.multiselect(
            "Korelasyonu hesaplanacak sayısal sütunlar",
            options=eksen["x"],
            default=varsayilan_sutunlar,
            help="En az iki sütun seç. Çok sütun seçersen etiketler sıkışır.",
        )
        x = y = hue = None
    elif grafik == "box":
        y = _secim(
            "y ekseni", eksen["y"],
            ["vize_notu", "adet", "ciro", "musteri_bin"],
        )
        x = _secim(
            "Gruplama sütunu (x)", eksen["x"],
            ["bolum", "sehir", "urun"],
            bos_secenek=True,
            yardim="Boş bırakırsan tek bir kutu çizilir.",
        )
        hue = None
        secilen_sutunlar = []
    else:
        x = _secim(
            "x ekseni", eksen["x"],
            ["ay", "sehir", "tarih", "date", "urun", "bolum"],
        )
        y = _secim(
            "y ekseni", eksen["y"],
            ["adet", "ciro", "musteri_bin", "vize_notu", "birim_fiyat"],
        )
        if eksen["hue"]:
            hue_secim = st.selectbox(
                "Renkle ayır (hue)",
                options=[YOK] + eksen["hue"],
                index=0,
                help="Grupları renkle ayırmak istersen bir sütun seç.",
            )
            hue = None if hue_secim == YOK else hue_secim
        else:
            hue = None
        secilen_sutunlar = []

    if "toplama" in izinli:
        toplama = st.selectbox(
            "Özetleme", options=list(charts.TOPLAMALAR),
            format_func=lambda k: charts.TOPLAMALAR[k],
            help="Her kategori için tek bir değer gerekir.",
        )
    if "sirala" in izinli:
        sirala = st.checkbox("Sırala", value=True)
    if "bins" in izinli:
        bins = st.slider("Aralık sayısı (bins)", 3, 100, 20, step=1)

with st.sidebar:
    st.markdown("**Görünüm**")
    renk = st.color_picker("Tek renk", "#4C72B0") if "renk" in izinli else "#4C72B0"
    palet = (
        st.selectbox("Renk paleti", charts.PALETLER)
        if "palet" in izinli else "Set2"
    )
    cmap = (
        st.selectbox("Renk haritası", charts.CMAPLER)
        if "cmap" in izinli else "RdBu_r"
    )
    marker = (
        st.selectbox("İşaretçi (marker)", charts.MARKERLAR)
        if "marker" in izinli else "o"
    )
    cizgi_kalinligi = (
        st.slider("Çizgi kalınlığı", 0.5, 6.0, 2.0, 0.5)
        if "cizgi_kalinligi" in izinli else 2.0
    )
    nokta_boyu = (
        st.slider("Nokta boyu", 5.0, 200.0, 45.0, 5.0)
        if "nokta_boyu" in izinli else 45.0
    )
    saydamlik = (
        st.slider("Saydamlık", 0.2, 1.0, 0.85, 0.05)
        if "saydamlik" in izinli else 0.85
    )
    izgara = st.checkbox("Izgara çizgileri", value=True) if "izgara" in izinli else True
    gosterge = st.checkbox("Gösterge (legend)", value=True) if "gosterge" in izinli else True
    kde = st.checkbox("Yoğunluk eğrisi (kde)", value=False) if "kde" in izinli else False
    annot = st.checkbox("Hücre değerlerini yaz", value=True) if "annot" in izinli else True

with st.sidebar.expander("Başlıklar ve boyut"):
    baslik = st.text_input("Grafik başlığı", "")
    x_etiketi = st.text_input("x ekseni etiketi", "")
    y_etiketi = st.text_input("y ekseni etiketi", "")
    genislik = st.slider("Genişlik (inç)", 4.0, 20.0, 8.0, 0.5)
    yukseklik = st.slider("Yükseklik (inç)", 2.5, 14.0, 4.5, 0.5)

with st.sidebar.expander("seaborn'a özel"):
    tema = st.selectbox(
        "Tema (sns.set_theme)", charts.TEMALAR,
        help="Bu ayar yalnızca seaborn sekmesini etkiler; pandas ve "
             "matplotlib varsayılan stille çizer.",
    )

ayarlar = charts.varsayilan_ayarlar()
ayarlar.update({
    "grafik": grafik,
    "x": x,
    "y": y,
    "hue": hue,
    "sutunlar": secilen_sutunlar,
    "toplama": toplama if "toplama" in izinli else "mean",
    "sirala": sirala if "sirala" in izinli else True,
    "bins": bins if "bins" in izinli else 20,
    "renk": renk,
    "palet": palet,
    "cmap": cmap,
    "marker": marker,
    "cizgi_kalinligi": cizgi_kalinligi,
    "nokta_boyu": nokta_boyu,
    "saydamlik": saydamlik,
    "izgara": izgara,
    "gosterge": gosterge,
    "baslik": baslik,
    "x_etiketi": x_etiketi,
    "y_etiketi": y_etiketi,
    "genislik": genislik,
    "yukseklik": yukseklik,
    "tema": tema,
    "kde": kde,
    "annot": annot,
})


# --------------------------------------------------------------------------- #
# 4. Grafik + kod
# --------------------------------------------------------------------------- #

rehber = kilavuz.REHBER[grafik]

st.subheader(f"3 · {charts.GRAFIKLER[grafik]}")

if hue and grafik in ("line", "scatter"):
    st.caption(
        f"Grupları **{hue}** sütunu renklendiriyor. Grup sayısı arttıkça "
        "renk paleti okunaksızlaşır; 6-7'den sonrası için vurgulama düşün."
    )

sol, sag = st.columns([2, 3])
with sol:
    st.markdown("**Ne zaman kullanılır?**")
    st.markdown(rehber["amac"])
    for madde in rehber["ne_zaman"]:
        st.markdown(f"- {madde}")
with sag:
    st.markdown("**Dikkat**")
    for madde in rehber["dikkat"]:
        st.markdown(f"- {madde}")

if grafik == "heatmap" and len(secilen_sutunlar) < 2:
    st.info("Isı haritası için en az iki sayısal sütun seç.")
    st.stop()

if grafik in ("scatter", "line") and x is not None and x == y:
    st.warning(
        f"x ve y eksenine aynı sütunu (**{x}**) seçtin. İki farklı sütun "
        "seçmen gerekiyor.",
        icon="⚠️",
    )
    st.stop()

sekmeler = st.tabs([charts.KUTUPHANELER[k] for k in charts.KUTUPHANELER])

for sekme, kutuphane in zip(sekmeler, charts.KUTUPHANELER):
    with sekme:
        a = dict(ayarlar)
        a["kutuphane"] = kutuphane
        kod = charts.kod_uret(a)

        try:
            tur, nesne = charts.calistir(df, kod)
        except charts.CizimHatasi as hata:
            st.error(
                "Bu ayarlarla grafik üretilemedi. Seçtiğin sütunlarda "
                "yeterli veri olmayabilir."
            )
            st.exception(hata)
            st.code(kod, language="python")
            continue

        if tur == "figure":
            _fig_goster(nesne)
            charts.kapat()
        else:
            st.caption(
                "pandas'ta hazır ısı haritası yok; aynı bilgi **renklendirilmiş "
                "tablo** olarak gösteriliyor."
            )
            _tablo_goster(nesne)

        st.markdown("**Python kodu**")
        st.code(kod, language="python")

        with st.expander("Kodu satır satır oku"):
            for parca, aciklama in rehber["kod"][kutuphane]:
                st.markdown(f"- `{parca}` — {aciklama}")

        if kutuphane == charts.PANDAS:
            st.caption(
                "pandas'ın `.plot()` arayüzü matplotlib'i arka planda kullanır; "
                "hızlı bakış için pratiktir, ince ayar için sınırlıdır."
            )
        elif kutuphane == charts.MATPLOTLIB:
            st.caption(
                "matplotlib'de her şey `ax` nesnesi üzerinden yapılır: "
                "`ax.set_title`, `ax.set_xlabel`, `ax.grid`…"
            )
        else:
            st.caption(
                "seaborn sütun adlarıyla çalışır (`x=`, `y=`, `hue=`); "
                "renk paleti `palette=` ile verilir."
            )

# --------------------------------------------------------------------------- #
# 5. Kod nasıl kullanılır
# --------------------------------------------------------------------------- #

with st.expander("Bu kodu defterimde nasıl çalıştırırım?"):
    st.markdown(
        """
        Kod, `df` adında bir tablonun hazır olduğunu varsayar. Kendi
        defterinde şu üç satırla aynı ortamı kurarsın:

        ```python
        import pandas as pd

        df = pd.read_csv("veri-dosyam.csv")   # Excel için: pd.read_excel(...)
        ```

        Sonra seçtiğin sekmedeki kodu yeni bir hücreye yapıştır ve çalıştır.
        Grafiği defterde görmek için kodun sonuna `plt.show()` ekle.

        Sütun adları Türkçe karakter içeriyorsa sorun yok; kod üretilirken
        adlar tırnak içine alınır.
        """
    )

st.divider()
st.caption(
    "Grafik Atölyesi · Veri Görselleştirme dersi yardımcı aracı · "
    "Grafik türleri ve parametreler derslerdeki kullanımla uyumludur."
)
