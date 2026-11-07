# 📊 Grafik Atölyesi

Veri Görselleştirme dersinin yardımcı aracı. Bir CSV ya da Excel dosyası
yüklediğinde:

1. dosyayı okuyup her sütunun türünü tahmin eder (sayısal, kategorik, metin,
   tarih),
2. o tabloyla çizilebilecek grafikleri listeler,
3. aynı grafiği **pandas**, **matplotlib** ve **seaborn** ile ayrı ayrı çizer,
4. her grafiğin **Python kodunu** gösterir ve satır satır açıklar,
5. başlık, renk, palet, işaretçi, saydamlık gibi özellikleri değiştirmene izin
   verir; kod anında buna göre yenilenir.

Amaç, "hazır grafik" vermek değil: ekranda gördüğün grafiği üreten kodu
okuyup kendi defterine taşıyabilmen.

Dersin kendisi ayrı bir depoda:
[Data-Visualisation](https://github.com/abdullatifkaban/Data-Visualisation)

## Kurulum

```bash
git clone https://github.com/abdullatifkaban/Chart-Builder.git
cd Chart-Builder
pip install -r requirements.txt
```

## Çalıştırma

```bash
streamlit run app.py
```

Tarayıcıda `http://localhost:8501` açılır. Sol panelden bir dosya yükle ya da
depodaki `Data/` klasöründen bir örnek seç.

## Neler var

| Grafik | Ne için | Üç kütüphanede |
|---|---|---|
| Çizgi | Zaman içinde değişim, trend | ✔ |
| Çubuk | Kategoriler arası büyüklük | ✔ |
| Dağılım | İki sayısal değişken arası ilişki | ✔ |
| Histogram | Tek değişkenin dağılımı | ✔ |
| Kutu | Grupları dağılım açısından karşılaştırma | ✔ |
| Isı haritası | Sayısal değişkenlerin korelasyonu | ✔ |

Her grafiğin yanında "ne zaman kullanılır" ve "dikkat" notları vardır; bunlar
ders içeriğindeki ilkelerle aynıdır (kesik eksen, aşırı renk, kalabalık grafik,
korelasyon ≠ nedensellik gibi).

Özelleştirilebilen parametreler: başlık, x/y eksen etiketi, tek renk, renk
paleti, renk haritası, işaretçi (marker), çizgi kalınlığı, nokta boyu,
saydamlık, ızgara, gösterge, sıralama, özetleme (ortalama/toplam/medyan/satır
sayısı), bins, yoğunluk eğrisi (kde), seaborn teması ve şekil boyutu.
Seçenekler grafik türüne göre otomatik filtrelenir.

## Sütun türü tanıma nasıl çalışıyor?

Tahmin üç sinyale dayanır:

- **pandas türü:** sayı, metin, tarih.
- **Benzersiz değer oranı:** bir metin sütununda az sayıda farklı değer varsa
  (en çok 20 ya da satırların %10'undan azı) **kategorik** sayılır.
- **Ad deseni:** `id`, `ogrenci_id` gibi adlar sayı gibi görünse de **metin**
  kabul edilir; eksene konmaz.
- **Sayı görünümlü metin:** Türkçe ondalık virgülü (`12,5`) taşıyan sütunlar
  sayısal tanınır.

Türler yanlış tahmin edilirse tablodaki **Tür** sütunundan değiştirilebilir.
Grafik seçenekleri anında buna göre güncellenir.

## Klasör yapısı

```text
Chart-Builder/
├── app.py            Streamlit arayüzü
├── requirements.txt
├── README.md
├── LICENSE
├── Data/             derslerdeki dört örnek veri seti
└── cb/
    ├── loader.py     CSV/Excel okuma
    ├── detect.py     sütun türü tanıma ve dönüştürme
    ├── charts.py     grafik kodu üretimi ve çalıştırma
    └── kilavuz.py    grafik başına öğretim notları
```

`charts.py` şu sırayla çalışır: **önce kodu üretir, sonra kodu çalıştırıp
grafiği çizer.** Böylece ekranda gördüğün grafik ile kopyaladığın kod birebir
aynı işi yapar.

## Yayınlama

Streamlit Community Cloud'da yayınlamak için:

1. Bu depoyu GitHub hesabına bağla.
2. Giriş dosyası olarak `app.py` seç.
3. Bağımlılıklar kökteki `requirements.txt` dosyasından kurulur.

Uygulama kendi bilgisayarında çalıştığında veri hiçbir yere gönderilmez.
Streamlit Community Cloud gibi bir sunucuda yayınlanırsa yüklediğin dosya
sunucuya gider; uygulama onu diske yazmaz, yalnız oturum boyunca bellekte
tutar.

## Sınırlar

- Isı haritasında pandas'ın hazır bir çizimi yoktur; pandas sekmesi aynı
  bilgiyi **renklendirilmiş tablo** (Styler) olarak verir. Gerçek ısı haritası
  için matplotlib veya seaborn sekmesini kullan.
- Kutu grafiğinde pandas, otomatik bir üst başlık ekler; üretilen kod bunu
  `fig.suptitle('')` ile temizler.
- Serbest metin sütunları (ad, not, açıklama) eksen olarak sunulmaz; bunlar
  grafik için uygun değildir.
- `.xls` (eski Excel) okumak için `xlrd` gerekir; `requirements.txt` içinde
  yok. Gerekirse `pip install xlrd`.

## Lisans

MIT — ayrıntı için [LICENSE](LICENSE).
