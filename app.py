import io
import os
import json
import pandas as pd
import streamlit as st
from google import genai
from PIL import Image

st.set_page_config(page_title="Aplikasi Scan Struk ke Excel", page_icon="🧾", layout="centered")

st.title("🧾 Aplikasi Scan Struk ke Excel")
st.markdown("Unggah foto struk belanjaan Anda, dan AI akan otomatis mengekstrak data ke dalam format Excel: **Nama Barang, Harga Beli, Harga Jual, dan Stok**.")

# Mengambil API Key secara aman dari Streamlit Secrets atau Input Manual
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    api_key = st.text_input("Masukkan Google Gemini API Key Anda:", type="password")

uploaded_files = st.file_uploader("Pilih atau seret foto struk di sini (bisa lebih dari 1 foto):", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files and api_key:
    if st.button("🚀 Proses Semua Struk"):
        with st.spinner("Sedang memindai struk dan merapikan data menggunakan AI..."):
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
                    2. Harga beli (harga_beli)
                    3. Harga jual (harga_jual)
                    4. Stok / Kuantitas (stok)
                    
                    Keluarkan hasilnya HANYA dalam format JSON berupa list of dictionary dengan keys:
                    "nama_barang", "harga_beli", "harga_jual", "stok".
                    Jangan tambahkan teks pembuka atau penutup, pastikan format JSON valid.
                    """

                    # Menggunakan model gemini-2.5-flash atau gemini-2.5-flash-lite yang stabil
                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=[image, prompt]
                    )

                    clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
                    items = json.loads(clean_text)
                    all_extracted_data.extend(items)

                df = pd.DataFrame(all_extracted_data)
                
                expected_cols = ["nama_barang", "harga_beli", "harga_jual", "stok"]
                for col in expected_cols:
                    if col not in df.columns:
                        df[col] = ""

                st.success("✅ Berhasil memindai semua struk!")
                st.subheader("Preview Data Gabungan:")
                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Data Gabungan")
                excel_data = output.getvalue()

                st.download_button(
                    label="📥 Unduh File Excel (.xlsx)",
                    data=excel_data,
                    file_name="Hasil_Scan_Struk_Gabungan.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as ec:
                st.error(f"Terjadi kesalahan saat memproses data: {ec}")
                
