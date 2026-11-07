"""Grafik türleri için kısa öğretim notları.

Arayüzde "Bu grafik ne zaman kullanılır?" ve "Kodu nasıl okurum?" bölümlerini
doldurur. Metinler ders içeriğindeki terminolojiyle uyumludur.
"""

from __future__ import annotations

REHBER = {
    "line": {
        "amac": "Bir değerin **sıralı bir eksen** boyunca (genellikle zaman) "
                "nasıl değiştiğini gösterir.",
        "ne_zaman": [
            "x ekseni tarih ya da sıralı bir kategori (ay, gün, yıl) ise",
            "Soru \"trend nasıl?\", \"artıyor mu, azalıyor mu?\" ise",
            "Aynı eksende birkaç seriyi karşılaştırmak istiyorsan (hue)",
        ],
        "dikkat": [
            "Sırasız kategorilerde (şehir, ürün) çizgi yanıltıcıdır; "
            "aralarında olmayan bir süreklilik ima eder.",
            "Çok sayıda seri çizgiyi okunmaz yapar; 5-6'dan sonrası için "
            "vurgulama ya da küçük çoklu panel düşün.",
            "Kesik y ekseni küçük farkları dev gibi gösterir (1. ders).",
        ],
        "kod": {
            "pandas": [
                ("sort_values", "Çizginin soldan sağa doğru sıralı çizilmesi "
                                "için veriyi x'e göre sıralar."),
                ("set_index / pivot_table", "x'i indekse alır; pandas indeksi "
                                            "x eksenine yazar."),
                (".plot(marker=...)", "marker her veri noktasına işaret koyar; "
                                      "linewidth çizgi kalınlığıdır."),
            ],
            "matplotlib": [
                ("ax.plot(...)", "x listesi ve y listesi alır; iki seri "
                                 "çizeceksen ikinci bir ax.plot eklenir."),
                ("renkler = plt.get_cmap(...)", "Kategorik grupları renk "
                                                "haritasından sırayla renklendirir."),
                ("ax.legend()", "label verilen serilerin göstergesini çizer."),
            ],
            "seaborn": [
                ("sns.lineplot(...)", "x, y ve hue'yu sütun adıyla alır; "
                                      "veriyi elle hazırlaman gerekmez."),
                ("errorbar=None", "Her x için güven aralığı bandını kapatır; "
                                  "öğretimde grafiği sadeleştirir."),
                ("hue=", "Aynı grafikte grupları renkle ayırır ve göstergesi "
                         "kendiliğinden gelir."),
            ],
        },
    },
    "bar": {
        "amac": "**Kategoriler arasındaki büyüklüğü** karşılaştırır. "
                "Gözün en iyi yaptığı iş uzunluk karşılaştırmasıdır.",
        "ne_zaman": [
            "x ekseni kategorik (şehir, ürün, bölüm) ise",
            "Soru \"hangisi daha büyük?\", \"sıralama nedir?\" ise",
            "Her kategori için tek bir özet değer varsa (ortalama, toplam)",
        ],
        "dikkat": [
            "Çubuk ekseni **sıfırdan** başlamalıdır; kesik eksen farkı "
            "abartır.",
            "Kategori sayısı 15-20'yi geçerse yatay çubuk ya da ilk N "
            "kategori daha okunur olur.",
            "Hiçbir zaman 3B çubuk kullanma; derinlik algısı değeri çarpıtır.",
        ],
        "kod": {
            "pandas": [
                ("groupby(...)[...].agg(...)", "Her kategori için tek bir "
                                               "özet değer hesaplar."),
                ("sort_values(ascending=False)", "Çubukları büyükten küçüğe "
                                                 "sıralar; okumayı kolaylaştırır."),
                ("kind='bar'", "pandas'a çubuk grafiği çizmesini söyler."),
            ],
            "matplotlib": [
                ("ax.bar(x, y)", "Kategori adlarını ve yükseklikleri ayrı "
                                 "listeler olarak alır."),
                ("edgecolor='white'", "Çubuklar arasına ince beyaz ayırıcı "
                                      "koyar."),
                ("tick_params(rotation=45)", "Uzun kategori adlarının "
                                             "üst üste binmesini önler."),
            ],
            "seaborn": [
                ("sns.barplot(x, y)", "x'e kategori, y'ye değer verilir. "
                                      "Özetleme yapılmış veriyle çalışırız."),
                ("alpha=", "Saydamlık; arka plandaki ızgarayı hafifçe "
                           "gösterir."),
            ],
        },
    },
    "scatter": {
        "amac": "İki sayısal değişken arasındaki **ilişkiyi** gösterir. "
                "Her nokta bir gözlemdir (bir satır).",
        "ne_zaman": [
            "Elimizde iki sayısal sütun varsa",
            "Soru \"x arttıkça y değişiyor mu?\" ise",
            "Aykırı değerleri ve kümeleri gözle bulmak istiyorsan",
        ],
        "dikkat": [
            "Nokta sayısı çoksa üst üste binme (overplotting) olur; saydamlık "
            "ya da daha küçük nokta kullan.",
            "İlişki **nedensellik demek değildir**.",
            "Nokta boyutunu üçüncü bir değişkene bağlarsan alan algısı "
            "doğrusal değildir (1. ders).",
        ],
        "kod": {
            "pandas": [
                ("df.plot.scatter(x=, y=)", "İki sütunu doğrudan alır; "
                                            "`s` nokta boyutudur."),
                ("grup.plot.scatter(...) in loop", "hue için her grubu ayrı "
                                                  "çağırıp label veririz."),
            ],
            "matplotlib": [
                ("ax.scatter(x, y)", "Nokta grafiğinin temel komutu."),
                ("s=", "Nokta alanı; 45 makul bir başlangıçtır."),
                ("alpha=", "Saydamlık; kalabalık veride üst üste binen "
                           "noktaları görünür kılar."),
            ],
            "seaborn": [
                ("sns.scatterplot(...)", "hue ile renk, style ile işaret "
                                         "biçimi verebilirsin."),
                ("palette=", "Kategorilerin renk paletini seçer."),
            ],
        },
    },
    "hist": {
        "amac": "Tek bir sayısal değişkenin **dağılımını** gösterir: hangi "
                "aralıklarda yığılma var, dağılım simetrik mi?",
        "ne_zaman": [
            "Tek sayısal sütunun genel şeklini merak ediyorsan",
            "Soru \"değerler nerede toplanıyor?\" ise",
            "Veri temizliğinde aykırı değeri ilk gözle bulmak için (6. ders)",
        ],
        "dikkat": [
            "**Bin sayısı** sonucu değiştirir: az bin kaba, çok bin gürültülü. "
            "Birkaç değeri dene.",
            "Histogram çubukları arasında boşluk yoktur; her çubuk bir "
            "*aralığı* temsil eder (kategori değil).",
            "Eksik değerler (NaN) histograma girmez; eksik sayısını ayrıca "
            "kontrol et.",
        ],
        "kod": {
            "pandas": [
                ("df[x].plot(kind='hist')", "Tek sütunu seçip histogram "
                                            "çizer."),
                ("bins=", "Aralık sayısı; grafiğin görünümünü belirler."),
            ],
            "matplotlib": [
                ("ax.hist(...)", "Değerleri alır ve aralıklara böler."),
                ("edgecolor='white'", "Komşu çubukları birbirinden ayırır."),
            ],
            "seaborn": [
                ("sns.histplot(...)", "histogram + isteğe bağlı yoğunluk "
                                      "eğrisi (kde)."),
                ("kde=True", "Dağılımın yumuşatılmış eğrisini ekler."),
            ],
        },
    },
    "box": {
        "amac": "Bir sayısal değişkenin dağılımını **özetler**: medyan, "
                "çeyrekler ve aykırı değerler.",
        "ne_zaman": [
            "Grupları dağılım açısından karşılaştıracaksan (şube, bölüm)",
            "Soru \"hangi grup daha değişken?\" ise",
            "Aykırı değerleri işaretlemek istiyorsan",
        ],
        "dikkat": [
            "Kutu medyanı ve çeyrekleri gösterir; ortalama görünmez.",
            "Göz, kutu yüksekliklerini çubuk uzunlukları kadar iyi "
            "karşılaştıramaz.",
            "Grup başına gözlem çok azsa (5-10) kutu yanıltıcı olur.",
        ],
        "kod": {
            "pandas": [
                ("df.boxplot(column=, by=)", "Grup bazında kutu çizer; "
                                             "`by` gruplama sütunudur."),
                ("fig.suptitle('')", "pandas otomatik bir üst başlık ekler; "
                                     "onu temizleriz."),
            ],
            "matplotlib": [
                ("ax.boxplot(veri)", "Grup başına değer listesi alır."),
                ("patch_artist=True", "Kutuların içini renklendirmeyi "
                                      "mümkün kılar."),
                ("tick_labels=", "Grupların eksen etiketleri (matplotlib "
                                 "3.9+)."),
            ],
            "seaborn": [
                ("sns.boxplot(data, x, y)", "Uzun formatta veriyle gruplu "
                                            "kutu çizer."),
                ("saturation=", "Kutu renginin doygunluğu."),
            ],
        },
    },
    "heatmap": {
        "amac": "Sayısal değişkenler arasındaki **korelasyon matrisini** "
                "renkle okur. Desen avlamak için hızlı bir genel bakıştır.",
        "ne_zaman": [
            "Çok sayıda sayısal sütunun birbiriyle ilişkisi merak ediliyorsa",
            "EDA'nın ilk adımı olarak hangi değişkenlere odaklanacağını "
            "arıyorsan (10. ders)",
        ],
        "dikkat": [
            "Korelasyon **nedensellik değildir**; sadece birlikte değişimi "
            "gösterir.",
            "Matris simetriktir; yarısı tekrardır.",
            "Sütun sayısı çoksa etiketler okunmaz; en ilgili değişkenleri "
            "seç.",
            "pandas'ta hazır ısı haritası yoktur; orada tablo renklendirme "
            "(Styler) gösterilir.",
        ],
        "kod": {
            "pandas": [
                ("df[sayisal].corr()", "Seçilen sütunların korelasyon "
                                       "matrisini hesaplar."),
                (".style.background_gradient", "Tabloyu renk skalasıyla "
                                               "boyar (figür değil, tablo)."),
            ],
            "matplotlib": [
                ("ax.imshow(korelasyon)", "Matrisi renkli bir görüntü olarak "
                                          "çizer."),
                ("vmin=-1, vmax=1", "Renk skalasını -1..+1 aralığına sabitler; "
                                    "farklı matrisler karşılaştırılabilir olur."),
                ("ax.text(...)", "Hücrelerin üstüne sayısal değer yazar."),
            ],
            "seaborn": [
                ("sns.heatmap(...)", "annot=True hücre değerlerini yazar."),
                ("fmt='.2f'", "Ondalık biçim; 2 hane yeterli."),
                ("linewidths=", "Hücreler arasına ince ayırıcı koyar."),
            ],
        },
    },
}
