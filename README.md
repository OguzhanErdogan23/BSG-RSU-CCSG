CCSG: Collatz-Chaos Stream Generator

Bu depo, Bilgi Sistemleri ve Güvenliği dersi proje ödevi kapsamında geliştirilen sözde rastgele sayı üretecinin (PRNG) kaynak kodlarını ve teknik dokümantasyonunu içerir.

Geliştirilen CCSG algoritması, Collatz Sanısı (3n+1 Problemi) dinamiklerini temel alarak kaos tabanlı bir akış şifreleme (stream cipher) mimarisi sunar.

🛠 Algoritma Mimarisi

Algoritma, kriptografik güvenlik ve rastgelelik sağlamak amacıyla aşağıdaki teknik yapıları kullanır:

Kaotik Çekirdek: Collatz yörüngelerinin doğrusal olmayan (non-linear) yapısı, ana entropi kaynağı olarak kullanılmıştır.

ARX Yapısı: Diferansiyel analize direnç sağlamak için Addition-Rotation-XOR işlemleri entegre edilmiştir.

Veriye Bağlı Döndürme (Data-Dependent Rotation): Her turdaki bit kaydırma miktarı, iç durumdaki (internal state) başka bir değişkene bağlıdır.

Whitening İşlemi: Çıktı bitlerinin 0/1 dengesini (balance) sağlamak ve istatistiksel sapmayı önlemek için Von Neumann düzeltici algoritması uygulanmıştır.

🚀 Kurulum ve Kullanım

Proje Python 3 standart kütüphaneleri ile geliştirilmiştir, ek paket kurulumu gerektirmez.

# Algoritmayı çalıştırmak için:
python CCSG.py


📜 Sözde Kod (Pseudo-Code)

Algoritmanın çalışma mantığı ve akış diyagramının metin temsili aşağıdadır:

ALGORİTMA: Collatz-Chaos Stream Generator (CCSG)

BAŞLANGIÇ (SETUP):
    Girdi: Anahtar (Kullanıcı Girdisi)
    Durum Vektörü: S[0..3] (128-bit)
    
    1. Anahtar ve Zaman Damgası -> SHA-256 Hash
    2. Hash Değeri -> S[0..3] yazmaçlarına atanır
    3. Isınma Turları (Warm-up): 64 döngü çıktı üretmeden çalıştırılır

DURUM GÜNCELLEME (ROUND FUNCTION):
    Her bit üretimi için döngü:
    
    1. Collatz Adımı (Non-Linearity):
       Eğer S[0] Çift ise -> T = S[0] >> 1
       Eğer S[0] Tek ise  -> T = (3 * S[0] + 1) XOR MASK
    
    2. Karıştırma (Diffusion):
       Rotasyon = S[1] AND 0x1F
       T = ROL(T, Rotasyon)
       
    3. Geri Besleme (Feedback):
       T = (T + Sayaç) MOD 2^32
       Yeni_Deger = (T + S[2]) XOR S[3]
       
    4. Kaydırma (Shift):
       S[0] <- S[1], S[1] <- S[2], S[2] <- S[3], S[3] <- Yeni_Deger

ÇIKTI ÜRETİMİ (EXTRACTION):
    Von Neumann Whitening:
    - İç durumdan karmaşık bir bit bloğu oluştur.
    - Ardışık bit çiftlerini (b1, b2) karşılaştır.
    - b1 != b2 ise b1'i çıktı olarak al.
    - b1 == b2 ise atla (Discard).


🛡️ Kriptanaliz ve Güvenlik Notları

Periyodiklik: 128-bit iç durum uzayı ve kaotik Collatz fonksiyonu sayesinde kısa döngü periyotları engellenmiştir.

Lineer Analiz: Dönme miktarının (rotation amount) dinamik olarak değişmesi, lineer yaklaşımları geçersiz kılar.

İstatistiksel Dağılım: Whitening katmanı sayesinde çıktı dizisindeki 0 ve 1 yoğunluğu %50 oranına yakınsar (Bias < %1).
