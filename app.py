Kalo pake yg ini tadi aman

import io
import os
import json
import time
import pandas as pd
import streamlit as st
from google import genai
from PIL import Image

# Konfigurasi Halaman agar Lebar dan Elegan
st.set_page_config(
    page_title="Smart Receipt to Excel Scanner",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling CSS agar Tampilan Sangat Profesional & Modern
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar Navigasi & Info
with st.sidebar:
    st.image("https://img.icons8.com/color/96/receipt.png", width=70)
    st.markdown("### 🛠️ Pengaturan Sistem")
    st.markdown("Aplikasi pintar untuk mengekstrak data struk belanjaan langsung ke format Excel secara otomatis.")
    st.markdown("---")
    st.info("💡 **Tips:** Pastikan foto struk terlihat jelas dan terang agar AI dapat membaca angka dengan akurat.")

# Header Utama
st.markdown('<p class="main-header">🧾 Smart Receipt to Excel Converter</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Unggah foto struk belanjaan Anda, AI akan mengekstrak Nama Barang, Harga Beli, Harga Jual, dan Stok secara instan.</p>', unsafe_allow_html=True)

# Mengambil API Key secara aman dari Streamlit Secrets atau Input Sidebar
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.markdown("### 🔑 Kunci Akses API")
    api_key = st.text_input("Masukkan Google Gemini API Key Anda:", type="password", help="Masukkan API key dari Google AI Studio")

# Layout Utama menggunakan Kolom
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📂 1. Unggah Foto Struk")
    uploaded_files = st.file_uploader(
        "Pilih atau seret file foto struk di sini:",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.success(f"Berhasil memuat {len(uploaded_files)} foto struk!")
        with st.expander("👁️ Lihat Pratinjau Foto Struk", expanded=True):
            for idx, uploaded_file in enumerate(uploaded_files):
                image = Image.open(uploaded_file)
                st.image(image, caption=f"Struk #{idx+1} ({uploaded_file.name})", use_container_width=True)

with col2:
    st.markdown("### ⚙️ 2. Proses & Unduh Hasil")
    
    if uploaded_files and api_key:
        if st.button("🚀 Mulai Ekstrak Data Struk Sekarang", type="primary", use_container_width=True):
            with st.spinner("⏳ Sedang memindai teks struk dan merapikan data menggunakan AI..."):
                try:
                    client = genai.Client(api_key=api_key)
                    all_extracted_data = []

                    for uploaded_file in uploaded_files:
                        image = Image.open(uploaded_file)
                        
                        prompt = """
                        Analisis gambar struk belanja ini secara teliti.
                        Ekstrak semua item produk/menu yang dibeli atau tertera di dalam struk.
                        Untuk setiap item, tentukan:
                        1. Nama barang/menu (nama_barang)
                        2. Harga beli satuan/total per baris (harga_beli) -> masukkan nilai angka murni saja tanpa titik/koma/Rp.
                        3. Harga jual (kosongkan atau isi null)
                        4. Stok / Kuantitas (stok) -> angka kuantitas yang dibeli di struk.
                        
                        Keluarkan hasilnya HANYA dalam format JSON berupa list of dictionary dengan keys:
                        "nama_barang", "harga_beli", "harga_jual", "stok".
                        Jangan tambahkan teks pembuka atau penutup, pastikan format JSON valid.
                        """

                        response = None
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                response = client.models.generate_content(
                                    model="gemini-3.8-flash",
                                    contents=[image, prompt]
                                )
                                break
                            except Exception as err:
                                if "503" in str(err) and attempt < max_retries - 1:
                                    time.sleep(3)
                                    continue
                                else:
                                    raise err

                        clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
                        items = json.loads(clean_text)
                        all_extracted_data.extend(items)

                    df = pd.DataFrame(all_extracted_data)
                    
                    if "harga_jual" not in df.columns:
                        df["harga_jual"] = ""
                    
                    expected_cols = ["nama_barang", "harga_beli", "harga_jual", "stok"]
                    for col in expected_cols:
                        if col not in df.columns:
                            df[col] = ""

                    st.session_state['df_result'] = df
                    st.success("🎉 Pemindaian struk berhasil diselesaikan!")

                except Exception as ec:
                    st.error(f"Terjadi kesalahan saat memproses data: {ec}")
    elif not uploaded_files:
        st.info("👈 Silakan unggah foto struk terlebih dahulu di sebelah kiri.")
    elif not api_key:
        st.warning("⚠️ Masukkan API Key terlebih dahulu.")

# Bagian Tabel Preview & Tombol Download di Bawah
if 'df_result' in st.session_state and not st.session_state['df_result'].empty:
    st.markdown("---")
    st.markdown("### 📊 Pratinjau Tabel Data Hasil Ekstraksi")
    
    # Membuat tabel preview dengan nomor urut mulai dari 1 dan menyembunyikan index 0
    df_display = st.session_state['df_result'].copy()
    df_display.insert(0, 'No', range(1, len(df_display) + 1))
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Buat file Excel dalam memori (tanpa kolom 'No' tambahan agar file Excel bersih)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        st.session_state['df_result'].to_excel(writer, index=False, sheet_name="Data Struk")
    excel_data = output.getvalue()

    col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
    with col_dl2:
        st.download_button(
            label="📥 Unduh Format Excel (.xlsx) Profesional",
            data=excel_data,
            file_name="Hasil_Scan_Struk_Profesional.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
