from neo4j import GraphDatabase
from openai import OpenAI
import json

# ==========================================
# KONFIGURASI KONEKSI NEO4J & OPENROUTER
# ==========================================
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password123"  # <-- Ganti password Neo4j Anda

OPENROUTER_API_KEY = "API_KEY_OPENROUTER_ANDA_DISINI"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Gunakan model yang pintar coding untuk Text-to-Cypher
MODEL_NAME = "openai/gpt-oss-20b:free"

# ==========================================
# DEFINISI SCHEMA GRAF (PENTING UNTUK LLM)
# ==========================================
GRAPH_SCHEMA = """
Node Labels & Properties:
- Patient {id: STRING, name: STRING, age: INTEGER}
- Disease {name: STRING}
- Symptom {name: STRING}
- Drug {name: STRING}

Relationships:
- (:Patient)-[:DIAGNOSED_WITH]->(:Disease)
- (:Patient)-[:EXHIBITS]->(:Symptom)
- (:Disease)-[:HAS_SYMPTOM]->(:Symptom)
- (:Disease)-[:TREATED_WITH]->(:Drug)
- (:Disease)-[:SIMILAR_TO]->(:Disease)
"""

# ==========================================
# FUNGSI 1: TEXT-TO-CYPHER
# ==========================================
def translate_to_cypher(user_query):
    prompt = f"""
    Kamu adalah ahli database Neo4j. Berdasarkan schema graph berikut:
    {GRAPH_SCHEMA}
    
    Terjemahkan pertanyaan user ini menjadi query Cypher yang valid: "{user_query}"
    
    ATURAN SANGAT KETAT:
    1. Output HANYA berupa query Cypher, tanpa penjelasan, tanpa format markdown (jangan gunakan ```cypher).
    2. Gunakan klausa RETURN untuk mengembalikan data yang diminta.
    3. Selalu batasi hasil dengan LIMIT 10 agar tidak terlalu berat.
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    
    cypher_query = response.choices[0].message.content.strip()
    
    # Bersihkan markdown jika AI membandel
    if cypher_query.startswith("```cypher"):
        cypher_query = cypher_query[9:-3].strip()
    elif cypher_query.startswith("```"):
        cypher_query = cypher_query[3:-3].strip()
        
    return cypher_query

# ==========================================
# FUNGSI 2: EXECUTE CYPHER KE NEO4J
# ==========================================
def execute_cypher(driver, cypher_query):
    try:
        with driver.session() as session:
            result = session.run(cypher_query)
            # Konversi hasil ke dalam list of dictionaries
            records = [record.data() for record in result]
            return records
    except Exception as e:
        return str(e)

# ==========================================
# FUNGSI 3: GRAPH RAG (GENERATE FINAL ANSWER)
# ==========================================
def generate_final_answer(user_query, db_results):
    prompt = f"""
    Kamu adalah asisten medis AI yang ramah. 
    User bertanya: "{user_query}"
    
    Sistem database graf mengembalikan data berikut: {json.dumps(db_results)}
    
    Tugasmu: Jawab pertanyaan user menggunakan bahasa Indonesia yang natural dan mudah dibaca HANYA berdasarkan data database tersebut. 
    Jika data kosong ([]), katakan bahwa kamu tidak menemukan informasinya di database pasien/medis.
    """
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content.strip()

# ==========================================
# MAIN LOOP: INTERFACE CHATBOT
# ==========================================
def chat_interface():
    print("\n" + "="*50)
    print("🏥 SELAMAT DATANG DI MEDICAL GRAPH RAG AI 🏥")
    print("Ketik 'exit' untuk keluar.")
    print("="*50)
    
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    
    while True:
        user_query = input("\n🧑 Anda: ")
        if user_query.lower() in ['exit', 'quit', 'keluar']:
            break
            
        print("   ⏳ [Text-to-Cypher] Sedang menerjemahkan pertanyaan...")
        cypher_query = translate_to_cypher(user_query)
        print(f"   💻 [Cypher Generated]: {cypher_query}")
        
        print("   🔍 [Retrieval] Sedang mencari di database Neo4j...")
        db_results = execute_cypher(driver, cypher_query)
        
        print("   🤖 [RAG] Sedang merangkai jawaban akhir...")
        final_answer = generate_final_answer(user_query, db_results)
        
        print(f"\n🩺 AI Assistant:\n{final_answer}")
        print("-" * 50)

    driver.close()
    print("Terima kasih telah menggunakan Medical Graph RAG AI!")

if __name__ == "__main__":
    chat_interface()