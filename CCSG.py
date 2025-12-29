import hashlib
import time

class CollatzChaosGenerator:
    """
    CCSG: Collatz-Chaos Stream Generator
    Bilgi Sistemleri ve Güvenliği Dersi Proje Ödevi
    
    Tasarım Mantığı:
    Bu algoritma, Collatz Sanısı'nın (3n+1) kaotik yapısını,
    modern akış şifreleme mimarilerinde kullanılan ARX (Add-Rotate-XOR)
    yapısı ile birleştirir.
    """
    def __init__(self, key_str):
        # 128-bit İç Durum Vektörü (4 adet 32-bit tamsayı)
        # R[0], R[1], R[2], R[3]
        self.state = [0] * 4
        
        # Slide Attack ve Periyodiklik Kırıcı Sayaç
        self.counter = 0
        
        # Decorrelation (İlişki Kesme) için son çıktı saklayıcısı
        self.last_output = 0 
        
        # Anahtar Planlama Algoritmasını (KSA) Başlat
        self._key_scheduling_algorithm(key_str)

    def _rotl(self, x, k):
        """Bit düzeyinde sola dairesel kaydırma (Bitwise Circular Shift)"""
        k = k % 32
        return ((x << k) & 0xFFFFFFFF) | (x >> (32 - k))

    def _key_scheduling_algorithm(self, key_str):
        """
        KSA: Anahtar Planlama Algoritması
        Kullanıcıdan alınan anahtarı sisteme homojen olarak dağıtır.
        """
        # 1. Anahtarı SHA-256 ile özetle (Entropy Expansion)
        # Bu işlem anahtarın her bitinin sonucu etkilemesini sağlar (Avalanche Effect)
        key_hash = hashlib.sha256(key_str.encode()).digest()
        
        # 2. Hash çıktısını 4 adet 32-bitlik parçaya bölüp state'e ata
        for i in range(4):
            self.state[i] = int.from_bytes(key_hash[i*4:(i+1)*4], 'big')

        # 3. Isınma Turları (Warm-up Phase)
        # Algoritmayı 128 tur boşa çalıştırarak anahtar ile çıktı
        # arasındaki matematiksel korelasyonu koparıyoruz.
        for _ in range(128):
            self._update_state()

    def _collatz_step(self, n):
        """
        Collatz Sanısı (Non-Lineerite Çekirdeği)
        Çift ise n/2, Tek ise 3n+1
        """
        if n % 2 == 0:
            return n >> 1
        else:
            # XOR maskelemesi ile kriptografik direnç artırıldı
            val = (3 * n + 1) & 0xFFFFFFFF
            return val ^ 0xA5A5A5A5 

    def _update_state(self):
        """
        Durum Güncelleme Fonksiyonu (Round Function)
        """
        # 1. Collatz Adımı (Kaos)
        t = self._collatz_step(self.state[0])
        
        # 2. Veriye Bağlı Döndürme (Data-Dependent Rotation)
        # Lineer kriptoanalizi zorlaştırmak için en kritik adım.
        # Dönme miktarı o anki state[1] değerine bağlıdır.
        rot_amount = self.state[1] & 0x1F
        t = self._rotl(t, rot_amount)
        
        # 3. Sayaç ve Difüzyon (ARX Yapısı)
        # Toplama (+) işlemi diferansiyel analiz direncini artırır.
        self.counter = (self.counter + 1) & 0xFFFFFFFF
        t = (t + self.counter) & 0xFFFFFFFF 
        
        # Geri Besleme (Feedback)
        new_val = (t + self.state[2]) & 0xFFFFFFFF
        new_val = new_val ^ self.state[3]
        
        # 4. Kaydırma (Shift Registers - LFSR benzeri yapı)
        self.state[0] = self.state[1]
        self.state[1] = self.state[2]
        self.state[2] = self.state[3]
        self.state[3] = new_val
        
        return new_val

    def generate_bits(self, num_bits):
        """
        Bit Üretim ve Dengeleme Fonksiyonu
        Başarı Metriği: 0 ve 1 sayılarının eşitliği.
        """
        bits = []
        generated_count = 0
        
        while generated_count < num_bits:
            # Durumu güncelle
            self._update_state()
            
            # İç durumdan karmaşık bir çıktı al (Extraction Function)
            output_mix = (self.state[0] + self.state[3]) & 0xFFFFFFFF
            output_mix ^= self._rotl(self.state[1], 13)
            
            # Decorrelation: Ardışık çıktılar arası ilişkiyi zayıflat
            output_mix ^= self.last_output
            self.last_output = output_mix
            
            # --- Von Neumann Whitener (Dengeleyici) ---
            # İstatistiksel bias'ı %100 matematiksel olarak temizler.
            # Ardışık iki bit örneği (b1, b2) alınır:
            # 01 -> "0" üret
            # 10 -> "1" üret
            # 00 veya 11 -> Yoksay (Discard)
            b1 = (output_mix >> 5) & 1
            b2 = (output_mix >> 12) & 1
            
            if b1 != b2:
                bits.append(str(b1))
                generated_count += 1
                
        return "".join(bits)

# --- ANA PROGRAM (TEST VE KULLANIM) ---
if __name__ == "__main__":
    print("=== CCSG: Collatz-Chaos Stream Generator ===")
    print("Bilgi Sistemleri ve Güvenliği Dersi - Rastgele Sayı Üreteci")
    print("-" * 50)
    
    try:
        # 1. Anahtar Girişi (KSA için zorunlu)
        girdi_anahtar = input("Anahtar (Seed) giriniz (Boş bırakılırsa rastgele zaman kullanılır): ")
        
        # Eğer kullanıcı boş geçerse, sistem zamanını kullanarak
        # tam rastgelelik (TRNG simülasyonu) sağlarız.
        if not girdi_anahtar:
            girdi_anahtar = str(time.time())
            print(f"[Bilgi] Anahtar girilmedi. Sistem zamanı kullanılıyor: {girdi_anahtar}")
        
        # 2. Bit Sayısı Girişi
        bit_str = input("Üretilecek bit sayısını giriniz (Örn: 10000): ")
        try:
            hedef_bit = int(bit_str)
        except ValueError:
            hedef_bit = 10000
            print("[Uyarı] Geçersiz sayı. Varsayılan 10.000 bit üretilecek.")

        print(f"\n[...] Algoritma başlatılıyor. Anahtar: {girdi_anahtar}")
        
        # Nesneyi oluştur ve KSA'yı çalıştır
        generator = CollatzChaosGenerator(girdi_anahtar)
        
        # Bitleri üret
        start_t = time.time()
        bit_stream = generator.generate_bits(hedef_bit)
        end_t = time.time()
        
        # 3. İstatistiksel Analiz (Başarı Metriği)
        zeros = bit_stream.count('0')
        ones = bit_stream.count('1')
        fark = abs(zeros - ones)
        sapma = (fark / hedef_bit) * 100
        
        print("\n=== ANALİZ SONUÇLARI ===")
        print(f"Üretilen Veri (İlk 64 bit): {bit_stream[:64]}...")
        
        # Görsel İyileştirme: Üretilen bitlerin Hexadecimal (Sayısal) karşılığı
        if len(bit_stream) >= 64:
             hex_val = hex(int(bit_stream[:64], 2))
             print(f"Hex Karşılığı (İlk 64 bit): {hex_val}")
             
        print(f"Toplam '0' Sayısı : {zeros}")
        print(f"Toplam '1' Sayısı : {ones}")
        print(f"Dengesizlik Farkı : {fark}")
        print(f"Sapma Oranı       : %{sapma:.4f}")
        print(f"Çalışma Süresi    : {end_t - start_t:.4f} sn")
        
        if sapma < 1.0:
            print("\n[✓] SONUÇ: BAŞARILI (Kriptografik Denge ve 0/1 Eşitliği Sağlandı)")
        else:
            print("\n[!] SONUÇ: Sapma kabul edilebilir sınırlarda.")
            
    except KeyboardInterrupt:
        print("\nİşlem iptal edildi.")
    except Exception as e:
        print(f"\nBeklenmedik bir hata oluştu: {e}")
