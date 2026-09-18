"""
duplicate_goruntuleyici.py
CSV raporunu okuyup resimleri gorsel olarak listeler;
secilenleri silinecekler listesine ekler.
Calistir: streamlit run duplicate_goruntuleyici.py
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from PIL import Image
import shutil, os, sys

CSV_YOLU = Path(r"C:\Users\EKO\Desktop\yapay zeka yazilim projesi\resim_duplicate_rapor_20260910-162545.csv")

@st.cache_data
def yukle_csv(yol):
    df = pd.read_csv(yol, encoding="utf-8")
    return df

@st.cache_data
def resim_kucuk(yol, boyut=(200, 200)):
    try:
        img = Image.open(yol)
        img.thumbnail(boyut)
        return img
    except Exception:
        return None

st.set_page_config(page_title="Duplicate Resim Duzenleyici", layout="wide")
st.title("Duplicate / Benzer Resim Duzenleyici")
st.markdown("CSV raporundaki resimleri goruntule, silmek istediklerini sec, sonra tek seferde arsivle.")

if not CSV_YOLU.exists():
    st.error(f"CSV dosyasi bulunamadi: {CSV_YOLU}")
    st.stop()

df = yukle_csv(CSV_YOLU)

if "secilecekler" not in st.session_state:
    st.session_state.secilecekler = set()

if "arsivlenmis" not in st.session_state:
    st.session_state.arsivlenmis = False

# Filtreler
sec_tipi = st.sidebar.radio("Tur filtresi", ["Hepsi", "Sadece birebir", "Sadece benzer"])
if sec_tipi == "Sadece birebir":
    df = df[df["tip"] == "birebir"]
elif sec_tipi == "Sadece benzer":
    df = df[df["tip"] == "benzer"]

# Sayfa basina resim
sayfa_basi = st.sidebar.number_input("Sayfa basina resim", min_value=10, max_value=100, value=30, step=5)

# Arsiv klasoru
arsiv_klasoru = Path(r"C:\Users\EKO\Desktop\yapay zeka yazilim projesi\duplikate_arsivi")
arsiv_klasoru.mkdir(exist_ok=True)

# Sayfalama
toplam = len(df)
sayfa_sayisi = max(1, (toplam // sayfa_basi) + 1)
sayfa_no = st.sidebar.number_input("Sayfa numarasi", min_value=1, max_value=sayfa_sayisi, value=1)

baslangic = (sayfa_no - 1) * sayfa_basi
bitis = min(toplam, baslangic + sayfa_basi)
sayfa_df = df.iloc[baslangic:bitis]

# Ana gorunum
col1, col2 = st.columns([1, 4])
with col1:
    st.markdown(f"**{toplam}** kayit gosteriliyor")
    st.markdown(f"**Secilen:** {len(st.session_state.secilecekler)}")
    if st.button("Secimi temizle"):
        st.session_state.secilecekler.clear()
with col2:
    st.markdown("**Nasil kullanilir:** Gormek istedigin resi tikla, silmek icin checkbox isaretle. Sonra 'Secilenleri Arsive Tasi' ile tek seferde arsivle.")

for idx, row in sayfa_df.iterrows():
    dosya_yolu = Path(row["dosya_yolu"])
    tip = row["tip"]
    boyut = row["boyut_kb"]
    tarih = row["son_degisiklik"]

    cols = st.columns([1, 5, 1, 1, 1])
    with cols[0]:
        img = resim_kucuk(str(dosya_yolu))
        if img:
            st.image(img, use_container_width=True)
        else:
            st.write("Resim okunamadi")
    with cols[1]:
        st.markdown(f"**Yol:** `{dosya_yolu}`")
        st.markdown(f"**Tip:** `{tip}` | **Boyut:** `{boyut} KB` | **Degisiklik:** `{tarih}`")
    with cols[2]:
        sec = st.checkbox("Sil", key=f"chk_{idx}", value=str(dosya_yolu) in st.session_state.secilecekler)
        if sec:
            st.session_state.secilecekler.add(str(dosya_yolu))
        else:
            st.session_state.secilecekler.discard(str(dosya_yolu))
    with cols[3]:
        if st.button("Ac", key=f"ac_{idx}", help="Dosyayi gorsel gorunumde ac"):
            try:
                os.startfile(str(dosya_yolu))
            except Exception as e:
                st.error(f"Acilamadi: {e}")

# Arsivle butonu
st.markdown("---")
if st.button(f"Secilen ({len(st.session_state.secilecekler)}) resmi arsive tasiyacak", disabled=len(st.session_state.secilecekler) == 0):
    hedef_klasor = arsiv_klasoru / f"secilim_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
    hedef_klasor.mkdir(exist_ok=True)
    tasindi = []
    for yol_str in st.session_state.secilecekler:
        yol = Path(yol_str)
        if yol.exists():
            hedef = hedef_klasor / yol.name
            try:
                shutil.move(str(yol), str(hedef))
                tasindi.append(yol.name)
            except Exception as e:
                st.error(f"{yol.name} tasiyamadi: {e}")
    st.success(f"{len(tasindi)} resim tasindi: {hedef_klasor}")
    st.session_state.secilecekler.clear()

st.markdown("---")
st.caption("Not: Bu liste sadece goruntuleme ve silme onayi icindir; hicbir dosyayi otomatik olarak silmez.")
