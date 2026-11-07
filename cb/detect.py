"""Sütun türü tanıma.

Amaç: yüklenen tablodaki her sütunun "ne işe yaradığını" kabaca anlamak.
Kesin bir bilim değil; bir öneri üretip öğrencinin düzeltmesine izin veriyoruz.
"""

from __future__ import annotations

import re

import pandas as pd

SAYISAL = "Sayısal"
KATEGORIK = "Kategorik"
METIN = "Metin"
TARIH = "Tarih"

TURLER = [SAYISAL, KATEGORIK, METIN, TARIH]

# "id", "ogrenci_id", "sube_id" gibi adlar kimliktir; sayı gibi görünse de
# grafikte eksene konmaz.
_ID_ADI = re.compile(r"(^id$|_id$|^id_|^\u0131d$)", re.IGNORECASE)

# Tarih ayrıştırırken bu ayırıcılardan en az biri geçmeli; yoksa "2020" gibi
# sayılar da tarih sanılır.
_TARIH_ISARETI = re.compile(r"[-/:. ]")


def _tarih_orani(seri: pd.Series) -> float:
    """Metin sütununun ne kadarının tarihe çevrilebildiğini ölçer (0-1)."""
    temiz = seri.dropna()
    if temiz.empty:
        return 0.0
    if not (temiz.dtype == object or pd.api.types.is_string_dtype(temiz)):
        return 0.0

    ornek = temiz.astype(str).head(50)
    if not ornek.map(lambda x: bool(_TARIH_ISARETI.search(x))).any():
        return 0.0

    donusen = pd.to_datetime(ornek, errors="coerce", format="mixed")
    return float(donusen.notna().mean())


def _sayisal_gorunumlu_mu(seri: pd.Series) -> bool:
    """Metin olarak okunmuş ama sayı gibi görünen sütunları yakalar.

    Tipik durum: Türkçe Excel/CSV'de ondalık ayırıcı virgüldür ("12,5"), bu
    yüzden pandas sütunu metin okur. Kural sıkı tutulur: değerlerin
    neredeyse tamamı sayı olmalı. Böylece içine birkaç metin karışmış
    sütunlar (ör. 1-5 puanlamada bir "iyi") sayısal sayılmaz; öğrenci
    türü kendisi seçer.
    """
    temiz = seri.dropna()
    if temiz.empty:
        return False
    ornek = temiz.astype(str).str.strip().head(200)
    donusen = pd.to_numeric(ornek.str.replace(",", ".", regex=False),
                            errors="coerce")
    return float(donusen.notna().mean()) >= 0.99


def _kategorik_mi(seri: pd.Series) -> bool:
    """Az sayıda farklı değer taşıyan metin sütunları kategoriktir.

    Ölçüt: en çok 20 benzersiz değer ya da benzersiz değerlerin satır sayısına
    oranı %10'un altında. İkinci koşul, 500 satırlık bir tabloda 30 şehir gibi
    durumları da kategorik sayar.
    """
    adet = seri.nunique(dropna=True)
    satir = len(seri)
    if adet <= 1:
        return True
    if adet <= 20:
        return True
    return adet / max(satir, 1) <= 0.10


def onerilen_tur(seri: pd.Series, ad: str) -> str:
    """Bir sütun için tür önerisi döndürür."""
    if pd.api.types.is_datetime64_any_dtype(seri):
        return TARIH
    if pd.api.types.is_bool_dtype(seri):
        return KATEGORIK
    if pd.api.types.is_numeric_dtype(seri):
        # Kimlik sütunları sayısal görünse de anlamlı bir sayı değildir.
        return METIN if _ID_ADI.search(ad) else SAYISAL
    if pd.api.types.is_timedelta64_dtype(seri):
        return METIN

    if _tarih_orani(seri) >= 0.8:
        return TARIH
    if _ID_ADI.search(ad):
        return METIN
    if _sayisal_gorunumlu_mu(seri):
        return SAYISAL
    if _kategorik_mi(seri):
        return KATEGORIK
    return METIN


def tanima_tablosu(df: pd.DataFrame) -> pd.DataFrame:
    """Arayüzde gösterilecek tanıma özetini üretir."""
    satirlar = []
    for ad in df.columns:
        seri = df[ad]
        ornek = seri.dropna().astype(str).head(3).tolist()
        satirlar.append({
            "Sütun": ad,
            "pandas türü": str(seri.dtype),
            "Tür": onerilen_tur(seri, ad),
            "Benzersiz": int(seri.nunique(dropna=True)),
            "Eksik": int(seri.isna().sum()),
            "Örnek değerler": ", ".join(ornek),
        })
    return pd.DataFrame(satirlar)


def uygula(df: pd.DataFrame, turler: dict[str, str]) -> tuple[pd.DataFrame, list[str]]:
    """Seçilen türlere göre sütunları dönüştürür.

    Dönüş: (yeni tablo, kullanıcıya gösterilecek uyarı listesi)
    """
    yeni = df.copy()
    uyarilar: list[str] = []

    for ad, tur in turler.items():
        if ad not in yeni.columns:
            continue
        seri = yeni[ad]
        if tur == SAYISAL:
            if not pd.api.types.is_numeric_dtype(seri):
                yeni[ad] = pd.to_numeric(
                    seri.astype(str).str.replace(",", ".", regex=False),
                    errors="coerce",
                )
                kayip = int(yeni[ad].isna().sum() - seri.isna().sum())
                if kayip > 0:
                    uyarilar.append(
                        f"**{ad}**: {kayip} değer sayıya çevrilemedi, boş (NaN) yapıldı."
                    )
        elif tur == TARIH:
            if not pd.api.types.is_datetime64_any_dtype(seri):
                yeni[ad] = pd.to_datetime(seri, errors="coerce", format="mixed")
                kayip = int(yeni[ad].isna().sum() - seri.isna().sum())
                if kayip > 0:
                    uyarilar.append(
                        f"**{ad}**: {kayip} değer tarihe çevrilemedi, boş (NaN) yapıldı."
                    )
        elif tur in (KATEGORIK, METIN):
            if pd.api.types.is_datetime64_any_dtype(seri):
                yeni[ad] = seri.dt.strftime("%Y-%m-%d")
            else:
                yeni[ad] = seri.astype("string")

    return yeni, uyarilar


def sutunlar(df: pd.DataFrame, turler: dict[str, str], tur: str) -> list[str]:
    """Belirli bir türdeki sütun adlarını verir."""
    return [ad for ad in df.columns if turler.get(ad) == tur]
