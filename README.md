# 🏥 Graph AI Medical Assistant: Disease-Symptom Knowledge Graph

Proyek ini adalah implementasi Sistem Tanya Jawab Medis (RAG) dan Analitik Graf menggunakan **Neo4j**, **Graph Data Science (GDS)**, dan **LLM via OpenRouter API**. Graf ini memetakan hubungan antara Penyakit, Gejala, Obat, dan Pasien, serta memungkinkan pengguna berinteraksi dengan data medis menggunakan bahasa natural.

## 🏗️ Arsitektur Sistem
Sistem ini dibangun dengan arsitektur pipa data (*data pipeline*) berikut:
1. **Core Data Ingestion:** Membaca data `main.csv` (134 penyakit, 408 gejala) dan memasukkannya ke Neo4j sebagai node `Disease` dan `Symptom`.
2. **LLM Graph Builder (Enrichment):** Menggunakan LLM (OpenRouter/Llama 3) untuk mengekstrak informasi obat berdasarkan nama penyakit, lalu membuat node `Drug` dan relasi `TREATED_WITH`.
3. **Synthetic Data Generation:** Menggunakan library `Faker` untuk membuat data `Patient` fiktif yang dihubungkan dengan penyakit (`DIAGNOSED_WITH`) dan gejalanya (`EXHIBITS`).
4. **Graph Machine Learning (GDS):** Menjalankan algoritma *Jaccard Node Similarity* untuk menemukan tingkat kemiripan antar-penyakit berdasarkan gejalanya, dan menyimpannya sebagai relasi `SIMILAR_TO`.
5. **Text-to-Cypher & RAG:** LLM menerjemahkan input bahasa natural pengguna menjadi query Cypher, mengekstrak konteks dari graf, dan menghasilkan jawaban medis yang akurat (Graph-Augmented Retrieval).

## ⚙️ Persyaratan (Prerequisites)
* Neo4j Desktop (Versi 5.x) dengan plugin **Graph Data Science (GDS)** diinstal dan diaktifkan.
* Python 3.8+
* API Key dari OpenRouter (untuk akses LLM).

## 🚀 Cara Instalasi dan Konfigurasi
1. Clone repositori ini.
2. Buat *virtual environment* dan instal library yang dibutuhkan:
   ```bash
   pip install neo4j pandas faker openai
    ```
3. Buka file skrip Python (`ingest_core.py`, `enrich_drug.py`, dll) dan ubah variabel kredensial berikut sesuai dengan instance Neo4j lokal Anda:
    ```python
       URI = "bolt://localhost:7687"
       USER = "neo4j"
       PASSWORD = "password_neo4j_anda"
       OPENROUTER_API_KEY = "api_key_openrouter_anda"
    ```

## 🏃 Cara Menjalankan (Pipeline Execution)
Jalankan skrip secara berurutan di terminal:
1. `python ingest_core.py` (Memasukkan data CSV ke graf).
2. `python enrich_drug.py` (Menjalankan LLM Graph Builder untuk data obat).
3. `python generate_patients.py` (Membuat data pasien dummy).
4. (Opsional) Jalankan *syntax* GDS di Neo4j Browser untuk analitik.
5. `python rag_chatbot.py` (Menjalankan antarmuka Text-to-Cypher / AI RAG).

## 🧠 Penjelasan Logika Cypher & Pipeline AI
* **Logika Cypher:** Kami menggunakan klausa `MERGE` alih-alih `CREATE` untuk memastikan operasi bersifat *idempotent* (mencegah duplikasi data jika skrip dijalankan ulang). Untuk Graph Analytics, kami menggunakan `gds.nodeSimilarity.write` untuk menghitung skor kemiripan fitur secara *in-memory* dan langsung memproyeksikannya kembali ke database sebagai garis (relasi) baru bernama `SIMILAR_TO`.
* **Pipeline AI:** 1. **Prompt Engineering for JSON:** AI dipaksa bertindak sebagai ekstraktor data (*Graph Builder*) dengan output wajib JSON murni agar mudah di-*parsing* oleh Python menjadi Node di Neo4j.
  2. **Fallback Mechanism:** Pipeline AI dilengkapi dengan `try-except` dan `time.sleep()` untuk menangani *Rate Limit* dari API gratis OpenRouter.