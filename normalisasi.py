import pandas as pd
from neo4j import GraphDatabase


# KONFIGURASI KONEKSI NEO4J

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password123"  # <-- Ganti password Neo4j Anda

CSV_FILE_PATH = "Diseases and Symptoms Database.csv" 

def execute_query(driver, query, parameters=None):
    with driver.session() as session:
        session.run(query, parameters)

print("📖 Membaca file dataset...")
# Baca normal, tidak perlu index_col=0 lagi
df = pd.read_csv(CSV_FILE_PATH)

# Identifikasi nama kolom secara persis
col_disease = 'label'
col_frequency = [c for c in df.columns if 'frequency' in str(c).lower()][0]

# Kolom gejala adalah semua kolom selain 'label' dan 'frequency'
symptom_columns = [col for col in df.columns if col not in [col_disease, col_frequency]]

print("\n🔍 --- DIAGNOSIS STRUKTUR DATA BARU ---")
print(f"Kolom Penyakit : '{col_disease}'")
print(f"Kolom Frekuensi: '{col_frequency}'")
print(f"Total Gejala   : {len(symptom_columns)} kolom")
print("---------------------------------------\n")

# Inisialisasi Driver Neo4j
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

print("Membersihkan database lama (menghapus node angka tadi)...")
with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")

print("Membuat constraints...")
execute_query(driver, "CREATE CONSTRAINT unique_disease IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE")
execute_query(driver, "CREATE CONSTRAINT unique_symptom IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE")

print("Memulai proses pengisian graf ke Neo4j...")

for idx, row in df.iterrows():
    disease_raw = str(row[col_disease]).strip()
    
    # Lewati jika baris kosong
    if pd.isna(disease_raw) or disease_raw == "" or "nan" in disease_raw.lower():
        continue
        
    occurrence = row[col_frequency] if pd.notna(row[col_frequency]) else 0
    
    # Ekstraksi nama: format "UMLS:C0011570_depression mental^UMLS..."
    # Kita ambil string pertama sebelum tanda '^', lalu ambil teks setelah '_'
    first_disease_part = disease_raw.split('^')[0]
    disease_name = first_disease_part.split('_')[-1] if '_' in first_disease_part else first_disease_part
    disease_code = first_disease_part.split('_')[0] if '_' in first_disease_part else "Unknown"
    
    # Buat Node Disease
    query_disease = """
    MERGE (d:Disease {name: $name})
    SET d.umls_code = $code, d.total_occurrence = $occurrence
    """
    execute_query(driver, query_disease, {
        "name": disease_name, 
        "code": disease_code, 
        "occurrence": int(occurrence)
    })
    
    # 2. Hubungkan dengan kolom Gejala
    for col in symptom_columns:
        val = row[col]
        
        if pd.notna(val) and str(val).strip() in ['1', '1.0']:
            symptom_str = str(col).strip()
            symptom_name = symptom_str.split('_')[-1] if '_' in symptom_str else symptom_str
            symptom_code = symptom_str.split('_')[0] if '_' in symptom_str else "Unknown"
            
            query_relation = """
            MERGE (s:Symptom {name: $symptom_name})
            SET s.umls_code = $symptom_code
            WITH s
            MATCH (d:Disease {name: $disease_name})
            MERGE (d)-[:HAS_SYMPTOM]->(s)
            """
            execute_query(driver, query_relation, {
                "symptom_name": symptom_name, 
                "symptom_code": symptom_code, 
                "disease_name": disease_name
            })

print("✅ Selesai! Core Graph sudah rapi.")
driver.close()