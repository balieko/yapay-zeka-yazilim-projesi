"""
resim_tarama.py — Cift ve benzer resim tespit scripti
Kullanim: python resim_tarama.py <klasorler...> [--rapor <dosya>]
"""
import os, sys, json, hashlib, math
from pathlib import Path

# Windows terminal bozuk karakterleri icin UTF-8 stdout
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from PIL import Image
    import imagehash
except ImportError:
    sys.exit("Gerekli paketler yüklenemedi: pillow, imagehash")

# ─────────────────────────────────────────────
DESTEKLENEN = {".jpg",".jpeg",".png",".gif",".bmp",".tiff",".webp",".heic",".heif"}
HASH_UZUNLUGU = 16          # perceptual hash boyutu (16x16 = 256 bit)
BENZER_ESIK = 0.08          # 0-256 bitlik farkta 8% altı = benzer kabul et
# ─────────────────────────────────────────────

def dosya_hash(yol: Path) -> str:
    """Dosya içeriğinin MD5 hash'i — tam eşleşme (birebir) için."""
    md5 = hashlib.md5()
    try:
        with open(yol, "rb") as f:
            for parca in iter(lambda: f.read(1 << 20), b""):
                md5.update(parca)
        return md5.hexdigest()
    except Exception:
        return ""

def goruntu_hash(yol: Path):
    """Görüntü algısal hash — benzer ama farklı boyut/kalite için."""
    try:
        img = Image.open(yol).convert("RGB")
        return imagehash.phash(img, hash_size=HASH_UZUNLUGU)
    except Exception:
        return None

def tarama(kokler: list) -> list:
    """Desteklenen resim dosyalarını topla."""
    dosyalar = []
    for kok in kokler:
        kok = Path(kok)
        if not kok.exists():
            print(f"[UYARI] Klasör bulunamadı: {kok}")
            continue
        for p in kok.rglob("*"):
            if p.is_file() and p.suffix.lower() in DESTEKLENEN:
                dosyalar.append(p)
    return sorted(set(dosyalar))

def grupla(dosyalar: list) -> tuple:
    """Birebir (MD5) ve benzer (pHash) grupları oluştur."""
    md5_gruplar = {}
    phash_list = []          # (dosya, phash) tuple listesi

    print("-> Dosyalar hashleniyor...")
    for i, d in enumerate(dosyalar, 1):
        h = dosya_hash(d)
        if h:
            md5_gruplar.setdefault(h, []).append(d)
        ph = goruntu_hash(d)
        if ph is not None:
            phash_list.append((d, ph))
        if i % 500 == 0:
            print(f"  {i}/{len(dosyalar)} işlendi...")

    def benzerlik(h1, h2):
        """Imagehash paketinin kendi fark fonksiyonu; 0-256 arasi ham bit farkini dondurur."""
        return (h1 - h2) / (HASH_UZUNLUGU * HASH_UZUNLUGU)  # 0-1 arasi normalize fark

    # Her resim için en küçük farkı bul
    benzer_eslesmeler = {}
    for i, (d1, h1) in enumerate(phash_list):
        for d2, h2 in phash_list[i+1:]:
            fark = benzerlik(h1, h2)
            if fark <= BENZER_ESIK and d1 != d2:
                benzer_eslesmeler.setdefault(d1, []).append((d2, fark))
                benzer_eslesmeler.setdefault(d2, []).append((d1, fark))
        if (i + 1) % 1000 == 0:
            print(f"  Benzerlik analizi: {i+1}/{len(phash_list)} tamamlandı...")

    # benzer_gruplar: dosya -> set(benzer diğer dosyalar)
    benzer_gruplar = {}
    for d, matches in benzer_eslesmeler.items():
        benzer_gruplar[d] = {m[0] for m in matches}

    return md5_gruplar, benzer_gruplar

def raporu_olustur(md5_gruplar, benzer_gruplar, kokler, toplam_resim):
    """CSV ve metin raporu üret."""
    import csv, datetime
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    rapor_dosyasi = Path.cwd() / f"resim_duplicate_rapor_{ts}.csv"
    ozet_dosyasi = Path.cwd() / f"resim_duplicate_ozet_{ts}.txt"

    satirlar = [["tip","grup_id","dosya_yolu","boyut_kb","son_degisiklik"]]
    ozet_birebir = 0
    ozet_benzer = 0

    for gid, (hsh, dosyalar) in enumerate(md5_gruplar.items(), 1):
        if len(dosyalar) < 2:
            continue
        for d in dosyalar:
            st = d.stat()
            satirlar.append(["birebir", gid, str(d), f"{st.st_size/1024:.1f}",
                             datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")])
            ozet_birebir += len(dosyalar) - 1

    # Benzer grupları MD5'ten farklı olanlar için ayrı grup
    seen = set()
    gben = len([g for g in md5_gruplar.values() if len(g) >= 2])
    benzer_grup_id = gben + 1
    for ana_dosya, benzerler in benzer_gruplar.items():
        for b in benzerler:
            if b == ana_dosya or (str(b) == str(ana_dosya)):
                continue
            satirlar.append(["benzer", benzer_grup_id, str(b), f"{b.stat().st_size/1024:.1f}",
                             datetime.datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M")])
            ozet_benzer += 1
        benzer_grup_id += 1

    # CSV kaydet
    with open(rapor_dosyasi, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(satirlar)

    # Özet metin
    with open(ozet_dosyasi, "w", encoding="utf-8") as f:
        f.write(f"Tarama tarihi: {ts}\n")
        f.write(f"Taranan kökler: {', '.join(str(k) for k in kokler)}\n")
        f.write(f"Toplam resim dosyasi: {toplam_resim}\n")
        f.write(f"── Birebir duplicate grupları: {gben}\n")
        f.write(f"── Bu gruplardaki fazladan dosya: {ozet_birebir}\n")
        f.write(f"── Benzer resim çiftleri (görsel): {ozet_benzer // 2}\n")
        f.write(f"── Rapor dosyası: {rapor_dosyasi.name}\n")

    return rapor_dosyasi, ozet_dosyasi, ozet_birebir, ozet_benzer // 2

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Çift/benzer resim tespit")
    ap.add_argument("dirs", nargs="*", default=[
        str(Path.home() / "Pictures"),
        str(Path.home() / "Desktop"),
        str(Path.home() / "Downloads"),
    ], help="Taranacak klasörler (varsayılan: Resimler + Masaüstü + İndirilenler)")
    ap.add_argument("--tum", action="store_true", help="Tüm kullanıcı klasörünü tara (yavaş)")
    ap.add_argument("--rapor", help="Çıktı özet dosyası yolu (varsayılan: çalışma dizini)")
    ap.add_argument("--esik", type=float, default=BENZER_ESIK, help="Benzerlik eşiği 0-1 arası, düşük = daha sıkı")
    args = ap.parse_args()

    # Eşik ve gruplar
    globals()["BENZER_ESIK"] = args.esik

    kokler = []
    if args.tum:
        kokler = [str(Path.home())]
    else:
        for d in args.dirs:
            if d:
                kokler.append(os.path.expandvars(d))

    print(f"Tarama başlıyor: {kokler}")
    dosyalar = tarama(kokler)
    if not dosyalar:
        print("Hiç resim dosyası bulunamadı.")
        return

    md5_gruplar, benzer_gruplar = grupla(dosyalar)
    rapor, ozet, birebir_fazla, benzer_sayisi = raporu_olustur(md5_gruplar, benzer_gruplar, kokler, len(dosyalar))

    print()
    print("=" * 55)
    print(f"Tarama tamamlandi.")
    print(f"  Ozet dosyasi  : {ozet}")
    print(f"  CSV raporu    : {rapor}")
    print(f"  --------------------------------------")
    print(f"  Birebir (tam eslesme) -> {birebir_fazla} fazla dosya")
    print(f"  Benzer (gorsel eslesme) -> {benzer_sayisi} cift")
    print(f"  --------------------------------------")
    print("Oneri: Tasima/ silme icin onay verdikten sonra su secenekler hazir olacak:")
    print("  1) En eski dosyayi sakla, digerlerini tasi ('duplikate_' klasorune)")
    print("  2) En buyuk dosyayi sakla, digerlerini tasi")
    print("  3) Sadece goruntule (hicbir dosyaya dokunma)")
    print("=" * 55)

if __name__ == "__main__":
    main()
