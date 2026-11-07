"""Dosya okuma: CSV ve Excel."""

from __future__ import annotations

import io

import pandas as pd

DESTEKLENEN = ["csv", "xlsx", "xls"]

# Türkçe Excel dosyaları çoğunlukla bu kodlamalarla gelir.
_KODLAMALAR = ["utf-8-sig", "utf-8", "cp1254", "iso-8859-9", "latin-1"]


class OkumaHatasi(Exception):
    """Kullanıcıya gösterilecek okuma hatası."""


def oku(icerik: bytes, dosya_adi: str) -> dict[str, pd.DataFrame]:
    """Dosyayı okur ve {sayfa_adı: DataFrame} döndürür.

    CSV dosyalarında tek bir "sayfa" olur; anahtarı dosya adıdır.
    """
    uzanti = dosya_adi.rsplit(".", 1)[-1].lower()

    if uzanti == "csv":
        return {"CSV": _csv_oku(icerik)}
    if uzanti in ("xlsx", "xls"):
        return _excel_oku(icerik, uzanti)

    raise OkumaHatasi(
        f"**.{uzanti}** desteklenmiyor. Desteklenen biçimler: "
        + ", ".join(f".{u}" for u in DESTEKLENEN)
    )


def _csv_oku(icerik: bytes) -> pd.DataFrame:
    son_hata: Exception | None = None
    for kodlama in _KODLAMALAR:
        try:
            # sep=None: virgül, noktalı virgül ve sekme otomatik seçilir.
            df = pd.read_csv(
                io.BytesIO(icerik), encoding=kodlama, sep=None, engine="python"
            )
        except Exception as hata:  # kodlama ya da ayırıcı uymadı
            son_hata = hata
            continue
        if df.shape[1] < 2:
            # Tek sütun çıktıysa ayırıcı yanlış seçilmiş olabilir.
            son_hata = OkumaHatasi(
                "Dosya tek sütun olarak okundu; ayırıcı (virgül/noktalı virgül) "
                "tanınamadı."
            )
            continue
        df.columns = [str(k).strip() for k in df.columns]
        return df

    raise OkumaHatasi(
        "CSV dosyası okunamadı. Dosyanın bozuk olmadığını ve ayırıcısının "
        f"virgül/noktalı virgül olduğunu kontrol et. (Son hata: {son_hata})"
    )


def _excel_oku(icerik: bytes, uzanti: str) -> dict[str, pd.DataFrame]:
    motor = "openpyxl" if uzanti == "xlsx" else "xlrd"
    try:
        sayfalar = pd.read_excel(
            io.BytesIO(icerik), sheet_name=None, engine=motor
        )
    except ImportError as hata:
        raise OkumaHatasi(
            f"Excel okumak için `{motor}` paketi gerekli. "
            f"Terminalden `pip install {motor}` çalıştır. ({hata})"
        ) from hata
    except Exception as hata:
        raise OkumaHatasi(f"Excel dosyası okunamadı: {hata}") from hata

    temiz: dict[str, pd.DataFrame] = {}
    for ad, df in sayfalar.items():
        df.columns = [str(k).strip() for k in df.columns]
        temiz[str(ad)] = df
    if not temiz:
        raise OkumaHatasi("Excel dosyasında okunabilir sayfa bulunamadı.")
    return temiz


def bos_satirlari_at(df: pd.DataFrame) -> pd.DataFrame:
    """Tamamen boş satır ve sütunları temizler."""
    df = df.dropna(how="all").dropna(axis=1, how="all")
    return df.reset_index(drop=True)
