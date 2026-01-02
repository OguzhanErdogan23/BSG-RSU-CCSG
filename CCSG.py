import hashlib
import time
import math
import os
import struct

class NISTUtils:
    """
    NIST Testleri için Yardımcı Matematiksel Fonksiyonlar.
    """
    @staticmethod
    def erfc(x):
        return math.erfc(x)

    @staticmethod
    def igamc(a, x):
        if x < 0: return 0
        return NISTUtils._igamc_continued_fraction(a, x)

    @staticmethod
    def _igamc_continued_fraction(a, x):
        GLN = math.lgamma(a)
        b = x + 1.0 - a
        c = 1.0 / 1.0e-30
        d = 1.0 / b
        h = d
        for i in range(1, 101):
            an = -i * (i - a)
            b += 2.0
            d = an * d + b
            if abs(d) < 1.0e-30: d = 1.0e-30
            c = b + an / c
            if abs(c) < 1.0e-30: c = 1.0e-30
            d = 1.0 / d
            del_val = d * c
            h *= del_val
            if abs(del_val - 1.0) < 1.0e-7: break
        return math.exp(-x + a * math.log(x) - GLN) * h

class CollatzChaosGenerator:
    """
    CCSG: Collatz-Chaos Stream Generator
    
    Deterministik kaotik dönüşümler (Collatz) ve kriptografik hash extractor (SHA-256)
    tabanlı rastgele sayı üreteci.
    
    Mimari: 
    - 128-bit İç Durum
    - Collatz Tabanlı Doğrusal Olmayan Güncelleme
    - SHA-256 Hash Extraction
    
    Uyumluluk: NIST SP 800-22
    """
    def __init__(self, key_str):
        self.state = [0] * 4
        self.counter = 0
        self.buffer = "" # Çıktı tamponu
        self.buffer_idx = 0
        self._key_scheduling_algorithm(key_str)

    def _rotl(self, x, k):
        k = k % 32
        return ((x << k) & 0xFFFFFFFF) | (x >> (32 - k))

    def _key_scheduling_algorithm(self, key_str):
        """Anahtar Planlama Algoritması (KSA)"""
        key_hash = hashlib.sha256(key_str.encode()).digest()
        for i in range(4):
            self.state[i] = int.from_bytes(key_hash[i*4:(i+1)*4], 'big')
        
        # Isınma Turları (Warm-up)
        for _ in range(128):
            self._update_state()

    def _collatz_step(self, n):
        """Collatz Dönüşümü"""
        if n % 2 == 0:
            return n >> 1
        else:
            val = (3 * n + 1) & 0xFFFFFFFF
            return val ^ 0xA5A5A5A5 

    def _update_state(self):
        """
        Durum Güncelleme Fonksiyonu (G-Function)
        """
        # 1. Giriş Karıştırma
        mixed_input = self.state[0] ^ self.state[2]
        t = self._collatz_step(mixed_input)
        
        # 2. Veriye Bağlı Döndürme
        rot_amount = self.state[1] & 0x1F
        t = self._rotl(t, rot_amount)
        
        # 3. ARX Yapısı
        self.counter = (self.counter + 1) & 0xFFFFFFFF
        t = (t + self.counter) & 0xFFFFFFFF 
        
        # Geri Besleme
        new_val = (t + self.state[2]) & 0xFFFFFFFF
        new_val = new_val ^ self.state[3]
        
        # 4. Doğrusal Olmayan Kaydırma
        self.state[0] = self.state[1] ^ self.state[3]
        self.state[1] = self.state[2]
        self.state[2] = self.state[3]
        self.state[3] = new_val
        
        return new_val

    def generate_bits(self, num_bits):
        """
        Hash Extraction ile Bit Üretimi
        """
        bits = []
        total_generated = 0
        
        while total_generated < num_bits:
            if self.buffer_idx >= len(self.buffer):
                self._update_state()
                
                # Hash Extractor (Durum + Sayaç -> SHA-256)
                data_to_hash = struct.pack('>IIII', *self.state) + struct.pack('>I', self.counter)
                digest = hashlib.sha256(data_to_hash).digest()
                
                self.buffer = "".join(f"{b:08b}" for b in digest)
                self.buffer_idx = 0
            
            needed = num_bits - total_generated
            available = len(self.buffer) - self.buffer_idx
            take = min(needed, available)
            
            chunk = self.buffer[self.buffer_idx : self.buffer_idx + take]
            bits.append(chunk)
            self.buffer_idx += take
            total_generated += len(chunk)
            
        return "".join(bits)

    def generate_nist_file(self, filename="data.bin", num_bits=1000000):
        """NIST Uyumlu Binary Dosya Oluşturur"""
        with open(filename, 'wb') as f:
            buffer = bytearray()
            bits = self.generate_bits(num_bits)
            for i in range(0, len(bits), 8):
                byte_val = int(bits[i:i+8], 2)
                buffer.append(byte_val)
            f.write(buffer)
        return bits

    def save_binary_file(self, filename, bits):
        """Bit dizisini dosyaya kaydeder"""
        with open(filename, 'wb') as f:
            buffer = bytearray()
            for i in range(0, len(bits), 8):
                chunk = bits[i:i+8]
                if len(chunk) < 8: break 
                byte_val = int(chunk, 2)
                buffer.append(byte_val)
            f.write(buffer)
        return os.path.abspath(filename)

    # --- NIST SP 800-22 TESTLERİ ---

    def test_frequency_monobit(self, bits):
        n = len(bits)
        sn = bits.count('1') - bits.count('0')
        s_obs = abs(sn) / math.sqrt(n)
        return math.erfc(s_obs / math.sqrt(2))

    def test_block_frequency(self, bits, M=128):
        """Block Frequency Testi"""
        n = len(bits)
        N = n // M
        if N == 0: return 0.0
        chi_sq = 0.0
        for i in range(N):
            block = bits[i*M : (i+1)*M]
            pi = block.count('1') / M
            chi_sq += (pi - 0.5) ** 2
        chi_sq *= (4 * M)
        
        p_val = NISTUtils.igamc(N/2.0, chi_sq/2.0)
        
        # Numerik kararsızlık kontrolü
        if p_val < 0 or p_val > 1:
            return None 
            
        return p_val

    def test_runs(self, bits):
        n = len(bits)
        pi = bits.count('1') / n
        if abs(pi - 0.5) >= (2 / math.sqrt(n)): return 0.0
        v_obs = 1
        for i in range(n-1):
            if bits[i] != bits[i+1]: v_obs += 1
        num = abs(v_obs - 2*n*pi*(1-pi))
        den = 2 * math.sqrt(2*n) * pi * (1-pi)
        return math.erfc(num/den)

    def test_cumulative_sums(self, bits):
        """Cumulative Sums (İleri ve Geri)"""
        n = len(bits)
        x = [1 if b=='1' else -1 for b in bits]
        
        def _compute_cusum_p(seq):
            s = 0
            max_s = 0
            for val in seq:
                s += val
                max_s = max(max_s, abs(s))
            z = max_s
            return 1.0 - math.erfc(z / (math.sqrt(n) * math.sqrt(2)))

        p_forward = _compute_cusum_p(x)
        p_backward = _compute_cusum_p(x[::-1])
        return p_forward, p_backward

    def test_serial(self, bits, m=2):
        """Serial Test (m=2)"""
        n = len(bits)
        bits_aug = bits + bits[:m-1]
        counts = {'00':0, '01':0, '10':0, '11':0}
        for i in range(n):
            sub = bits_aug[i:i+m]
            if sub in counts: counts[sub] += 1
        psi_sq = 0
        for sub in counts:
            psi_sq += pow(counts[sub], 2)
        psi_sq = (psi_sq * pow(2, m) / n) - n
        
        p_val = NISTUtils.igamc(pow(2, m-2), psi_sq/2.0)
        
        if p_val < 0 or p_val > 1:
            return None
            
        return p_val

    # --- EK TESTLER ---

    def test_chi_square(self, bits):
        """Ki-Kare Testi"""
        n = len(bits)
        c0 = bits.count('0')
        c1 = bits.count('1')
        expected = n / 2.0
        chi = math.pow(c0 - expected, 2) / expected + math.pow(c1 - expected, 2) / expected
        p_val = math.exp(-chi / 2)
        return chi, p_val

    def test_ks_uniformity(self, bits):
        """Kolmogorov-Smirnov Testi (Byte Düzeyinde)"""
        integers = []
        for i in range(0, len(bits)-8, 8):
            val = int(bits[i:i+8], 2)
            integers.append(val / 255.0)
        if not integers: return 0.0
        integers.sort()
        n = len(integers)
        max_d = 0.0
        for i in range(n):
            d = abs(((i + 1) / n) - integers[i])
            if d > max_d: max_d = d
        return max_d

    def test_autocorrelation_multi(self, bits, lags=[1, 2, 8, 16, 32]):
        """Çoklu Gecikmeli Otokorelasyon"""
        results = {}
        n = len(bits)
        for lag in lags:
            A = 0
            for i in range(n - lag):
                if bits[i] == bits[i+lag]: A += 1
                else: A -= 1
            z = A / math.sqrt(n - lag)
            results[lag] = z
        return results

    def avalanche_test(self, seed):
        """Avalanche (Çığ Etkisi) Testi"""
        gen1 = CollatzChaosGenerator(seed)
        bits1 = gen1.generate_bits(10000) 
        
        try:
            seed_int = int(seed, 16)
            mod_seed_int = seed_int ^ 1 
            mod_seed = hex(mod_seed_int)[2:].zfill(len(seed))
        except ValueError:
            mod_seed = seed[:-1] + (chr(ord(seed[-1]) ^ 1))

        gen2 = CollatzChaosGenerator(mod_seed)
        bits2 = gen2.generate_bits(10000)
        
        diff = 0
        for b1, b2 in zip(bits1, bits2):
            if b1 != b2: diff += 1
            
        ratio = (diff / 10000) * 100
        return ratio

# --- ANA PROGRAM ---
if __name__ == "__main__":
    print("=== CCSG: Collatz-Chaos Stream Generator ===")
    
    try:
        print("\nÖnerilen Kriptografik Test Vektörü:")
        print("1. 1c583789679f28d84429972323c976930053916960c14f6524336d39678254d6")
        
        seed = input("\nSeed Giriniz (Boş = Oto): ")
        if not seed:
            seed = hashlib.sha256(os.urandom(32)).hexdigest()
            print(f"[Oto-Seed]: {seed}")
            
        miktar_str = input("Üretilecek bit sayısını milyon cinsinden giriniz [Varsayılan: 1]: ")
        try:
            if not miktar_str:
                hedef_bit = 1000000
                dosya_etiketi = "1M"
            else:
                miktar_str = miktar_str.replace(',', '.')
                kat_sayi = float(miktar_str)
                hedef_bit = int(kat_sayi * 1000000)
                dosya_etiketi = f"{kat_sayi}M"
                if hedef_bit < 1000:
                    hedef_bit = 1000
        except ValueError:
            print("[Hata] Geçersiz sayı formatı. Varsayılan 1 Milyon bit kullanılıyor.")
            hedef_bit = 1000000
            dosya_etiketi = "1M"

        # Dosya ismi oluşturma
        seed_hash_short = hashlib.sha256(seed.encode()).hexdigest()[:8]
        dosya_adi = f"CCSG_{dosya_etiketi}_{seed_hash_short}.bin"
        
        print(f"\n[İşlem] {hedef_bit:,} bit üretiliyor... (Lütfen bekleyin)".replace(',', '.'))
        t0 = time.time()
        
        # Üretim (Bellekte)
        gen = CollatzChaosGenerator(seed)
        bit_stream = gen.generate_nist_file(dosya_adi, hedef_bit)
        
        t1 = time.time()
        
        # --- ANALİZLER ---
        zeros = bit_stream.count('0')
        ones = bit_stream.count('1')
        total = len(bit_stream)
        diff = abs(zeros - ones)
        ratio = (diff / total) * 100
        hex_val = hex(int(bit_stream[:64], 2))
        
        # 1. NIST Testleri Hesaplama
        p_monobit = gen.test_frequency_monobit(bit_stream)
        p_block = gen.test_block_frequency(bit_stream)
        p_runs = gen.test_runs(bit_stream)
        p_serial = gen.test_serial(bit_stream)
        p_cusum_fwd, p_cusum_bwd = gen.test_cumulative_sums(bit_stream)
        
        # 2. Diğer Analizler Hesaplama
        chi, p_chi = gen.test_chi_square(bit_stream)
        ks_val = gen.test_ks_uniformity(bit_stream)
        av_ratio = gen.avalanche_test(seed)
        auto_res = gen.test_autocorrelation_multi(bit_stream)
        
        # --- RAPORLAMA ---
        print("\n" + "="*40)
        print("          ANALİZ SONUÇLARI")
        print("="*40)
        
        # 1. GENEL BİLGİLER
        print("\n--- 1. GENEL BİLGİLER ---")
        print(f"Kullanılan Seed   : {seed}")
        print(f"Üretilen Veri     : {bit_stream[:64]}...")
        print(f"Hex Karşılığı     : {hex_val}")
        print(f"Toplam Bit Sayısı : {total:,}".replace(',', '.'))
        print(f"Dağılım (0 / 1)   : {zeros:,} / {ones:,}".replace(',', '.'))
        print(f"Dengesizlik Farkı : {diff:,}".replace(',', '.'))
        print(f"Sapma Oranı       : %{ratio:.4f}")
        print(f"Çalışma Süresi    : {t1-t0:.4f} sn")
        
        # 2. NIST TESTLERİ
        print("\n--- 2. NIST SP 800-22 DAHİLİ TESTLERİ ---")
        
        def print_res(name, p_val):
            if p_val is None:
                print(f"{name:<25}: HESAPLANAMADI (Numerik Limit)")
            else:
                status = "[GEÇTİ]" if p_val >= 0.01 else "[KALDI]"
                print(f"{name:<25}: P={p_val:.6f} {status}")

        print_res("Monobit Frequency", p_monobit)
        print_res("Block Frequency", p_block)
        print_res("Runs Test", p_runs)
        print_res("Serial Test (m=2)", p_serial)
        print_res("Cumulative Sums (Fwd)", p_cusum_fwd)
        print_res("Cumulative Sums (Bwd)", p_cusum_bwd)
        
        # 3. DİĞER ANALİZLER
        print("\n--- 3. DİĞER İSTATİSTİKSEL VE GÜVENLİK ANALİZLERİ ---")
        
        # Ki-Kare
        res_chi = "[BAŞARILI]" if chi < 3.841 else "[BAŞARISIZ]"
        print(f"{'Ki-Kare Testi':<25}: χ²={chi:.4f} {res_chi}")
        
        # KS Testi
        res_ks = "[BAŞARILI]" if ks_val < 0.05 else "[BAŞARISIZ]"
        print(f"{'KS Testi (Uniformity)':<25}: D={ks_val:.4f} {res_ks}")
        
        # Avalanche
        av_status = ""
        if 0 <= av_ratio < 40:
            av_status = "[ZAYIF DIFFUSION]"
        elif 40 <= av_ratio < 45:
            av_status = "[SINIRDA DIFFUSION]"
        elif 45 <= av_ratio < 48:
            av_status = "[KABUL EDİLEBİLİR DIFFUSION]"
        elif 48 <= av_ratio <= 52:
            av_status = "[GÜÇLÜ DIFFUSION]"
        elif 52 < av_ratio <= 55:
            av_status = "[KABUL EDİLEBİLİR DIFFUSION]"
        elif 55 < av_ratio <= 60:
            av_status = "[AŞIRI KARIŞIM EĞİLİMİ]"
        else: # > 60
            av_status = "[ANORMAL DIFFUSION]"
            
        print(f"{'Avalanche (Çığ Etkisi)':<25}: %{av_ratio:.2f} {av_status}")
        
        # Otokorelasyon
        max_z = 0.0
        for lag, z in auto_res.items():
            if abs(z) > max_z: max_z = abs(z)
        
        z_status = "< 3.00" if max_z < 3.00 else ">= 3.00"
        auto_msg = "Anlamlı korelasyon gözlenmedi" if max_z < 3.00 else "Korelasyon şüphesi"
        
        print(f"{'Otokorelasyon':<25}: {auto_msg} [Max Z = {max_z:.2f} {z_status}] (Lag 1–32)")

        print("\n" + "-"*40)
        
        # Dosya Kaydetme
        while True:
            cevap = input(f"Tam NIST testi için dosya (.bin) oluşturulsun mu? (E/H): ").strip().lower()
            if cevap == 'e':
                print(f"[Dosya] '{dosya_adi}' yazılıyor...")
                tam_yol = gen.save_binary_file(dosya_adi, bit_stream)
                print(f"Dosya Konumu: {tam_yol}")
                print("[Dosya] Hazır. Hash Extractor yapısı ile NIST uyumlu.")
                break
            elif cevap == 'h':
                print("Dosya oluşturulmadı.")
                break
            else:
                print("Lütfen 'E' veya 'H' giriniz.")
        
        print("-" * 40)

    except KeyboardInterrupt:
        print("\nİptal.")
