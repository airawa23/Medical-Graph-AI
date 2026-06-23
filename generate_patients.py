from neo4j import GraphDatabase
from faker import Faker
import random


# KONFIGURASI KONEKSI NEO4J

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password123"  # <-- Ganti password Neo4j Anda

fake = Faker('id_ID') # Menggunakan nama khas Indonesia

def generate_synthetic_patients():
    print("🔌 Menyambungkan ke Neo4j...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    
    with driver.session() as session:
        # 1. Ambil semua penyakit dan gejalanya dari database
        print("📖 Mengambil data penyakit dan gejala...")
        query_get_diseases = """
        MATCH (d:Disease)-[:HAS_SYMPTOM]->(s:Symptom)
        RETURN d.name AS disease, collect(s.name) AS symptoms
        """
        result = session.run(query_get_diseases)
        
        disease_data = []
        for record in result:
            disease_data.append({
                "disease": record["disease"],
                "symptoms": record["symptoms"]
            })
            
        print(f"✅ Berhasil mengambil {len(disease_data)} penyakit untuk simulasi.")
        
        # Buat 50 Pasien Sintetik
        TOTAL_PATIENTS = 50
        print(f"🧬 Mulai membuat {TOTAL_PATIENTS} profil pasien...")
        
        for i in range(TOTAL_PATIENTS):
            patient_id = f"P-{str(i+1).zfill(3)}"
            patient_name = fake.name()
            patient_age = random.randint(25, 80)
            
            # Pilih penyakit secara acak untuk pasien ini
            random_disease = random.choice(disease_data)
            disease_name = random_disease["disease"]
            
            # Ambil beberapa gejala dari penyakit tersebut (tidak selalu semua gejala muncul di tiap pasien)
            all_symptoms = random_disease["symptoms"]
            num_symptoms_to_exhibit = random.randint(1, len(all_symptoms))
            exhibited_symptoms = random.sample(all_symptoms, num_symptoms_to_exhibit)
            
            # Masukkan data pasien ke Neo4j
            query_insert_patient = """
            // Buat Node Patient
            MERGE (p:Patient {id: $patient_id})
            SET p.name = $patient_name, p.age = $patient_age
            
            // Hubungkan ke Penyakit
            WITH p
            MATCH (d:Disease {name: $disease_name})
            MERGE (p)-[:DIAGNOSED_WITH]->(d)
            
            // Hubungkan ke Gejala yang dialami
            WITH p
            UNWIND $exhibited_symptoms AS symptom_name
            MATCH (s:Symptom {name: symptom_name})
            MERGE (p)-[:EXHIBITS]->(s)
            """
            
            session.run(query_insert_patient, {
                "patient_id": patient_id,
                "patient_name": patient_name,
                "patient_age": patient_age,
                "disease_name": disease_name,
                "exhibited_symptoms": exhibited_symptoms
            })
            
            print(f"   👤 Dibuat: {patient_name} (Umur: {patient_age}) -> Didiagnosis: {disease_name}")
            
    driver.close()
    print("🎉 Selesai! Semua pasien berhasil dimasukkan ke dalam graf.")

if __name__ == "__main__":
    generate_synthetic_patients()