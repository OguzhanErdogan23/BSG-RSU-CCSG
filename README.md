CCSG: Collatz-Chaos Stream Generator

Bu depo, Bilgi Sistemleri ve Güvenliği dersi proje ödevi kapsamında geliştirilen sözde rastgele sayı üretecinin (PRNG) kaynak kodlarını ve teknik dokümantasyonunu içerir.

Geliştirilen CCSG algoritması, Collatz Sanısı (3n+1 Problemi) dinamiklerini temel alarak kaos tabanlı bir akış şifreleme (stream cipher) mimarisi sunar.

🛠 Algoritma Mimarisi

Algoritma, kriptografik güvenlik ve rastgelelik sağlamak amacıyla aşağıdaki teknik yapıları kullanır:

Anahtar Planlama (KSA): SHA-256 ve ısınma turları ile anahtar iç duruma homojen olarak dağıtılır.

Kaotik Çekirdek: Collatz yörüngelerinin doğrusal olmayan (non-linear) yapısı entropi kaynağıdır.

Veriye Bağlı Döndürme (Data-Dependent Rotation): Lineer analizi zorlaştırmak için bit kaydırma miktarı değişkendir.

Whitening (Dengeleme): Von Neumann algoritması ile çıktı bitlerinde %50-%50 (0 ve 1) dengesi sağlanır.

🚀 Kurulum ve Kullanım

Proje Python 3 ile geliştirilmiştir.

python CCSG.py


Program çalıştığında sizden bir Anahtar (Seed) ve Üretilecek Bit Sayısı isteyecektir.

📜 Sözde Kod (Pseudo-Code)

Algoritmanın teknik akışı aşağıdadır:

ALGORİTMA: Collatz-Chaos Stream Generator (CCSG)

1. ANAHTAR PLANLAMA (KSA):
   Girdi: Kullanıcı Anahtarı (K)
   - Anahtarın SHA-256 özetini al.
   - Özeti 4 parçaya bölüp Durum Vektörüne (S[0..3]) ata.
   - 128 tur boyunca çıktı üretmeden durumu karıştır (Warm-up).

2. DURUM GÜNCELLEME (ROUND FUNCTION):
   Her adımda:
   A. Collatz İşlemi:
      - S[0] Çift ise: T = S[0] >> 1
      - S[0] Tek ise:  T = (3 * S[0] + 1) XOR 0xA5A5A5A5
   
   B. Karıştırma (Diffusion):
      - Rotasyon Miktarı = S[1] AND 0x1F
      - T = SolaDöndür(T, Rotasyon Miktarı)
      - T = T + Sayaç (Mod 2^32)
   
   C. Geri Besleme (Feedback):
      - Yeni_Deger = (T + S[2]) XOR S[3]
   
   D. Kaydırma (Shift):
      - S[0] <- S[1], S[1] <- S[2], S[2] <- S[3], S[3] <- Yeni_Deger

3. ÇIKTI ÜRETİMİ (EXTRACTION & WHITENING):
   - Karışık değer hesapla: Out = (S[0] + S[3]) XOR Döndür(S[1])
   - Von Neumann Dengeleyici:
     - Ardışık iki bit (b1, b2) al.
     - b1 != b2 ise b1'i kaydet.
     - b1 == b2 ise atla.


🛡️ Güvenlik Analizi Notları

Kullanıcı Girdisi: Algoritma deterministik çalışır; aynı anahtar her zaman aynı sayı dizisini üretir.

İstatistiksel Denge: Whitening katmanı sayesinde çıktıdaki 0 ve 1 yoğunluğu %50 oranına yakınsar (Bias < %1).

Saldırı Direnci: Veriye bağlı döndürme ve Collatz kaosu, matematiksel modellemeyi (Lineer Analiz) ve periyodiklik tespitini zorlaştırır.
