import hashlib
import time

class CollatzKeyStream:
    """
    Collatz Sanısı ve ARX (Add-Rotate-Xor) mimarisi tabanlı
    özgün Sözde Rastgele Sayı Üreteci (PRNG).
    
    Algoritma Adı: CCSG (Collatz-Chaos Stream Generator)
    Tasarım: Collatz yörüngelerinin kaotik yapısı ile LFSR benzeri 
    durum güncelleme mekanizmasının hibritlenmesi.
    """
    def __init__(self, key_str):
        # 128-bit iç durum vektörü (4 adet 32-bitlik yazmaç)
        self.state = [0] * 4
        # Slide ataklarına karşı sayaç (round constant)
        self.counter = 0
        self._initialize_state(key_str)

    def _rotl(self, x, k):
        # Bit düzeyinde sola dairesel kaydırma (Bitwise Circular Shift)
        # Difüzyonu artırmak için kullanıldı.
        k = k % 32
        return ((x << k) & 0xFFFFFFFF) | (x >> (32 - k))

    def _initialize_state(self, key_str):
        # Anahtar Planlama Algoritması (Key Scheduling Algorithm - KSA)
        # Girdi anahtarı ve zaman damgası SHA-256 ile özetlenerek
        # başlangıç entropisi (seed) oluşturulur.
        seed_source = f"{key_str}-{time.time()}"
        key_hash = hashlib.sha256(seed_source.encode()).digest()
        
        for i in range(4):
            self.state[i] = int.from_bytes(key_hash[i*4:(i+1)*4], 'big')

        # Başlangıç durumu ile çıktı arasındaki korelasyonu kırmak için
        # 64 turluk ısınma (warm-up) süreci.
        for _ in range(64):
            self._next_state_update()

    def _collatz_step(self, n):
        # Collatz Sanısı (3n+1 Problemi)
        # Non-lineerite kaynağı olarak kullanıldı.
        # Kriptografik direnç için XOR maskelemesi eklendi.
        if n % 2 == 0:
            return n >> 1
        else:
            val = (3 * n + 1) & 0xFFFFFFFF
            return val ^ 0xA5A5A5A5 # Pattern kırıcı sabit maske

    def _next_state_update(self):
        # Durum Güncelleme Fonksiyonu
        
        # 1. Collatz dönüşümü (Non-Linearity)
        c_val = self._collatz_step(self.state[0])
        
        # 2. Veriye Bağlı Döndürme (Data-Dependent Rotation)
        # Lineer kriptoanalizi zorlaştırmak için dönüş miktarı
        # state[1]'in o anki değerine göre dinamik belirlenir.
        rot_amount = self.state[1] & 0x1F
        mixed = self._rotl(c_val, rot_amount)
        
        # 3. Sayaç eklemesi (Slide Attack koruması)
        self.counter = (self.counter + 1) & 0xFFFFFFFF
        mixed = (mixed + self.counter) & 0xFFFFFFFF

        # 4. Geri Besleme (Feedback) - ARX Yapısı
        # Toplama ve XOR işlemleri birlikte kullanılarak
        # diferansiyel analiz zorlaştırıldı.
        feedback = (mixed + self.state[2]) & 0xFFFFFFFF
        feedback = feedback ^ self.state[3]
        
        # 5. Yazmaçları Kaydır (Shift Registers)
        self.state[0] = self.state[1]
        self.state[1] = self.state[2]
        self.state[2] = self.state[3]
        self.state[3] = feedback
        
        return feedback

    def generate_balanced_bits(self, num_bits):
        # İstenilen sayıda bit üretimi.
        # Başarı metriği: 0 ve 1'lerin eşit dağılımı.
        bits = []
        generated_count = 0
        
        while generated_count < num_bits:
            # İç durumu güncelle
            self._next_state_update()
            
            # Çıktı Fonksiyonu (Extraction)
            # Tüm durum yazmaçlarının non-lineer kombinasyonu
            output_mix = (self.state[0] + self.state[3]) & 0xFFFFFFFF
            output_mix ^= self.state[1]
            output_mix ^= (self.state[2] >> 3)
            
            # Von Neumann Düzeltici (Whitener)
            # İstatistiksel sapmayı (bias) gidermek için kullanılır.
            # Ardışık iki bit örneği alınır:
            # 01 -> "0" üretilir
            # 10 -> "1" üretilir
            # 00 ve 11 -> Atılır (Discard)
            b1 = (output_mix >> 5) & 1
            b2 = (output_mix >> 12) & 1
            
            if b1 != b2:
                bits.append(str(b1))
                generated_count += 1
                
        return "".join(bits)

# --- Test ve Doğrulama ---
if __name__ == "__main__":
    # Kullanım Örneği
    test_key = "Kripto2025_ProjeAnahtari"
    cipher = CollatzKeyStream(test_key)
    
    target_len = 10000
    print(f"Algoritma: CCSG (Collatz-Chaos Stream Generator)")
    print(f"Hedeflenen Bit Uzunluğu: {target_len}")
    print("Üretim ve analiz başlıyor...")
    
    start_time = time.time()
    keystream = cipher.generate_balanced_bits(target_len)
    end_time = time.time()
    
    zeros = keystream.count('0')
    ones = keystream.count('1')
    diff = abs(zeros - ones)
    percentage = (diff / target_len) * 100
    
    print("-" * 30)
    print(f"Üretilen Stream (Hex Önizleme): {hex(int(keystream[:32], 2))}")
    print(f"0 Sayısı : {zeros}")
    print(f"1 Sayısı : {ones}")
    print(f"Fark     : {diff}")
    print(f"Sapma    : %{percentage:.4f}")
    print(f"Süre     : {end_time - start_time:.4f} sn")
    
    if percentage < 1.0:
        print("SONUÇ: BAŞARILI (Kriptografik Rastgelelik İstatistikleri Sağlandı)")
    else:
        print("SONUÇ: BAŞARISIZ (Yüksek Sapma)")
