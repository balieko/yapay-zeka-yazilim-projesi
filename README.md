# Yapay Zeka Yazilim Projesi

Kisisel yapay zeka yazilim projeleri icin calisma depusu.

## Icerik

- `sarki-stream-plan/` - Sarki stream planlama araclari
  - `resim_tarama.py` - Resim tarama ve kopya tespiti
  - `duplicate_goruntuleyici.py` - Kopya resim goruntuleyici
- `duplikate_arsivi/` - Kopya resim arsivi
- `resim_duplicate_rapor_*.csv` - Kopya tarama raporlari
- `resim_duplicate_ozet_*.txt` - Tarama ozetleri

## Kullanim

Resim tarama:

```
python sarki-stream-plan/resim_tarama.py
```

Kopya goruntuleyici:

```
python sarki-stream-plan/duplicate_goruntuleyici.py
```

## Git Kullanimi

Degisiklikleri yuklemek icin:

```
git add .
git commit -m "Degisiklik aciklamasi"
git push
```

Guvenlik: Token, sifre gibi gizli bilgiler asla bu repoya eklenmez.