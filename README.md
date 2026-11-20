# 📊 Grafik Atölyesi

Bir CSV ya da Excel dosyası yükleyip grafiği **adım adım kurmaya** yarayan
bağımsız bir araç. Dosyayı yüklediğinde:

1. dosyayı okuyup her sütunun türünü tahmin eder (sayısal, kategorik, metin,
   tarih) ve her türü ayrı sekmede özetler,
2. o tabloyla çizilebilecek grafikleri listeler,
3. grafiği **pandas**, **matplotlib** veya **seaborn** ile çizer,
4. Python kodunu **adım adım büyüterek** yazar: her özellik koda yeni bir satır
   ekler,
5. seçtiğin sütunlarla grafiğin fiilen ne gösterdiğini veriden hesaplayıp
   yorumlar.

Amaç, "hazır grafik" vermek değil: ekranda gördüğün grafiği üreten kodu
adım adım okuyup kendi defterine taşıyabilmen.

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

## Nasıl kullanılır?

Uygulama yukarıdan aşağıya şu bölümlerden oluşur.

### Veriyi tanı

Dosya okunduğunda her sütun bir türe ayrılır ve dört sekmede özetlenir:

| Sekme | Gösterdiklerin |
|---|---|
| Sayısal | dolu/eksik, benzersiz, ortalama, medyan, std, min, maks |
| Kategorik | benzersiz, eksik, en sık değer ve sıklığı |
| Metin | benzersiz, ortalama uzunluk, örnek değerler |
| Tarih | en erken ve en geç tarih |

Tahmin yanlışsa **Sütun türlerini düzelt** bölümünden değiştir. İstatistikler
ve grafik seçenekleri anında güncellenir.

### Kütüphane ve grafik türü

Sol panelde sırayla:

1. **Kütüphane:** pandas, matplotlib veya seaborn. Kod, seçtiğin kütüphanenin
   sözdizimiyle yazılır.
2. **Grafik türü:** verinle çizilebilen türler listelenir. Seçilen kütüphanede
   olmayan türler listede görünmez.
3. **Eksenler:** x, y ve isteğe bağlı renkle ayırma (hue). x için seçtiğin
   sütun y listesinde çıkmaz.

### Özellikleri tek tek aç

Sol panelin **Özellikler** bölümünde her seçenek bir onay kutusudur. Hiçbirini
işaretlemezsen kod tek satır kalır:

```python
df.plot(x='ay', y='adet', kind='line')
```

Başlık açtığında iki satır olur, sonra x/y etiketi, renk, işaretçi, ızgara,
şekil boyutu… Kod ve önizleme aynı anda yenilenir:

```python
df.plot(x='ay', y='adet', kind='line', marker='o', color='#4C72B0')

plt.title('Aylık satış')
plt.xlabel('Ay')
plt.ylabel('Adet')
```

Seçenekler grafik türüne göre filtrelenir; örneğin `bins` yalnızca histogramda,
`cmap` yalnızca ısı haritasında görünür.

### Kodu oku

**Kodu adım adım yaz** başlığı altında beş bölüm vardır:

1. **Sabit giriş satırları** — kütüphane importları ve veriyi okuma. Dosya adı
   yüklediğin dosyadan gelir; Excel yüklediysen okuma satırı kendiliğinden
   `pd.read_excel(...)` olur.
2. **Grafik kodu** — yalnızca grafiği üreten, adım adım büyüyen satırlar.
3. **Grafik önizleme** — kodun canlı çıktısı.
4. **Tam kod (kopyalamaya hazır)** — giriş + grafik kodu tek blokta; indirme
   düğmesi de burada.
5. **Öğretim alanı** — aşağıdaki dört katman.

### Öğretim alanı

1. **Bu grafik ne için kullanılır?** — seçtiğin sütunlarla kurulan amaç
   cümlesi ve grafik türünün uygun olduğu durumlar.
2. **Seçtiğin sütunlarla bu grafik ne gösteriyor?** — yüklenen veriden
   hesaplanan yorum. Örneğin:
   - "`ay` boyunca `adet` ortalaması 385 → 349; genel eğilim azalıyor."
   - "En yüksek ortalama İstanbul (461), en düşük İzmir (289). Fark yaklaşık
     %59.7."
   - "`birim_fiyat` ile `adet` arasındaki korelasyon r = 0.46 (orta, pozitif)."

   Sütun ya da ayar değişince bu cümleler yenilenir.
3. **Nasıl okunur? / Dikkat** — grafiği yorumlama ilkeleri ve tuzaklar (kesik
   eksen, korelasyon ≠ nedensellik, bins seçimi, az gözlemde keman vb.).
4. **Koddaki komutlar** — o kodda geçen komutların tek satırlık açıklamaları,
   temelden ayrıntıya sıralı.

## Desteklenen grafikler

| Grafik | pandas | matplotlib | seaborn |
|---|---|---|---|
| Çizgi | ✔ | ✔ | ✔ |
| Basamak | ✔ | ✔ | ✔ |
| Alan | ✔ | ✔ | – |
| Çubuk (dikey/yatay) | ✔ | ✔ | ✔ |
| Yığılmış çubuk | ✔ | ✔ | – |
| Pasta | ✔ | ✔ | – |
| Dağılım | ✔ | ✔ | ✔ |
| Histogram | ✔ | ✔ | ✔ |
| Kutu | ✔ | ✔ | ✔ |
| Keman | – | ✔ | ✔ |
| Isı haritası | ✔ (Styler) | ✔ | ✔ |

Ortak özellikler (başlık, eksen etiketleri, tek renk, saydamlık, palet, ızgara,
45° etiket, gösterge, şekil boyutu, seaborn teması) dışında türe özel
seçenekler de vardır: çizgi biçimi ve basamak konumu, alan yığma, yatay çubuk ve
değer etiketleri, yığını %100'e normalize etme, pasta yüzdesi/başlangıç
açısı/patlama/gölge, histogramda bins/kde/kümülatif/yoğunluk, kutuda ortalama ve
aykırı değer denetimi, kemanda iç gösterim ve kesme, ısı haritasında üst üçgen
maskesi, hücre çizgileri ve renk çubuğu.

## Sütun türü tanıma nasıl çalışıyor?

Tahmin dört sinyale dayanır:

- **pandas türü:** sayı, metin, tarih.
- **Benzersiz değer oranı:** bir metin sütununda az sayıda farklı değer varsa
  (en çok 20 ya da satırların %10'undan azı) **kategorik** sayılır.
- **Ad deseni:** `id`, `ogrenci_id` gibi adlar sayı gibi görünse de **metin**
  kabul edilir; eksene konmaz.
- **Sayı görünümlü metin:** Türkçe ondalık virgülü (`12,5`) taşıyan sütunlar
  sayısal tanınır.

Türler yanlış tahmin edilirse tablodaki **Tür** sütunundan değiştirilebilir;
grafik seçenekleri anında buna göre güncellenir.

## Örnek veriler

`Data/` klasöründe dört veri seti var:

| Dosya | İçerik |
|---|---|
| `kahve-satis.csv` | ay, şehir, ürün, adet, birim fiyat |
| `anket-verisi.csv` | eksik ve tutarsız değerler içeren anket verisi |
| `ogrenci-aliskanliklari.csv` | öğrenci alışkanlıkları ve vize notu |
| `korona-vaka.csv` | ülke bazında günlük vaka sayıları (geniş format) |

## Klasör yapısı

```text
Chart-Builder/
├── app.py            Streamlit arayüzü
├── requirements.txt
├── README.md
├── LICENSE
├── Data/             dört örnek veri seti
└── cb/
    ├── loader.py       CSV/Excel okuma
    ├── detect.py       sütun türü tanıma ve dönüştürme
    └── grafik_kodu.py  kod üretimi, çalıştırma ve yorumlar
```

`grafik_kodu.py` kodu iki amaçla üretir: **göstermek** (kopyalanabilir tam kod) ve
**çalıştırmak** (önizleme). Ekranda gördüğün grafik ile kopyaladığın kod aynı
kaynaktan geldiği için birebir aynı işi yapar.

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

- Isı haritasında pandas'ın hazır bir çizimi yoktur; pandas seçildiğinde aynı
  bilgi **renklendirilmiş tablo** (Styler) olarak verilir. Gerçek ısı haritası
  için matplotlib veya seaborn seç.
- Kutu grafiğinde pandas otomatik bir üst başlık ekler; üretilen kod bunu
  `plt.suptitle('')` ile temizler.
- Serbest metin sütunları (ad, not, açıklama) eksen olarak sunulmaz; grafik
  için uygun değildir.
- Seaborn'da pasta, alan ve yığılmış çubuk yoktur; pandas'ta keman grafiği
  yoktur. Bu türler ilgili kütüphane seçildiğinde listede görünmez.
- Yığılmış çubuk için ikinci bir kategorik sütun (hue) gerekir.
- `.xls` (eski Excel) okumak için `xlrd` gerekir; `requirements.txt` içinde
  yok. Gerekirse `pip install xlrd`.

## İlgili kaynak

Veri görselleştirmeyi bir bütün olarak ele alan ayrı bir ders deposu var. Bu
araç ondan bağımsız çalışır; konuyla ilgini çekerse oraya da bakabilirsin:

[Veri Görselleştirme](https://github.com/abdullatifkaban/Data-Visualisation)

## Lisans

MIT — ayrıntı için [LICENSE](LICENSE).
