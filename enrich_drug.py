from neo4j import GraphDatabase
from openai import OpenAI
import json
import time


# KONFIGURASI KONEKSI NEO4J

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password123"  # <-- Ganti password Neo4j Anda 


# KONFIGURASI OPENROUTER

OPENROUTER_API_KEY = "API_KEY_OPENROUTER_ANDA_DISINI"

# Inisialisasi client OpenAI dengan Base URL OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ganti model ini sesuai keinginan
MODEL_NAME = "openai/gpt-oss-20b:free" 


# FUNGSI LLM GRAPH BUILDER (TIER 3 & 4)

def ask_llm_for_drugs(disease_name):
    prompt = f"""
    Kamu adalah dokter ahli farmasi. Berikan 2 nama obat medis/generik utama untuk mengobati penyakit '{disease_name}'. 
    Berikan output HANYA dalam bentuk JSON array of strings. Tanpa teks tambahan, tanpa format markdown.
    Contoh output yang benar: ["Metformin", "Insulin"]
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ],
            # Opsional: Jika model mendukung JSON mode di OpenRouter, ini akan membantu
            # response_format={"type": "json_object"} 
        )
        
        teks_jawaban = response.choices[0].message.content.strip()
        
        # Membersihkan markdown ```json jika AI membandel
        if teks_jawaban.startswith("```json"):
            teks_jawaban = teks_jawaban[7:-3].strip()
        elif teks_jawaban.startswith("```"):
            teks_jawaban = teks_jawaban[3:-3].strip()
            
        # Mengubah teks JSON menjadi List Python
        drugs = json.loads(teks_jawaban)
        print(f"   🤖 LLM merekomendasikan: {drugs}")
        return drugs
        
    except Exception as e:
        print(f"   ⚠️ Gagal mendapat jawaban LLM untuk {disease_name}. Error: {e}")
        return ["Standard Medical Care"] # Fallback jika API gagal


# PROSES ENRICHMENT GRAF KE NEO4J

def run_enrichment():
    print("🔌 Menyambungkan ke Neo4j...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    
    with driver.session() as session:
        print("📖 Mengambil daftar penyakit dari database...")
        # Mengambil node Disease yang sudah ada di database
        result = session.run("MATCH (d:Disease) RETURN d.name AS disease_name")
        diseases = [record["disease_name"] for record in result]
        
        print(f"✅ Ditemukan {len(diseases)} penyakit. Memulai AI Graph Builder via OpenRouter...")
        
        count = 0
        # Kita batasi 20 penyakit dulu untuk testing agar tidak memakan waktu lama
        for disease in diseases[:20]:
            print(f"\n🔍 Mencari obat untuk: {disease}")
            
            # Panggil OpenRouter API
            drugs = ask_llm_for_drugs(disease)
            
            # Masukkan ke Neo4j (Membuat relasi TREATED_WITH ke node Drug)
            for drug in drugs:
                query = """
                MATCH (d:Disease {name: $disease_name})
                MERGE (dr:Drug {name: $drug_name})
                MERGE (d)-[:TREATED_WITH]->(dr)
                """
                session.run(query, disease_name=disease, drug_name=drug)
                count += 1
            
            # Jeda n detik agar tidak terkena rate limit (terutama untuk model gratis)
            time.sleep(6)
                
    driver.close()
    print(f"\n🎉 Selesai! Berhasil menambahkan {count} relasi obat (TREATED_WITH) dari AI ke dalam graf.")

# Eksekusi skrip
if __name__ == "__main__":
    run_enrichment()