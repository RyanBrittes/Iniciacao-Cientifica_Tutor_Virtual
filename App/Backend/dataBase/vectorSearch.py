from pymongo import MongoClient
import os
from dotenv import load_dotenv
from App.Backend.rag.embedGenerate import EmbedGenerate

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGO_ADDRESS"))
db_access = mongo_client[os.getenv("MONGO_DB")]
collection_access = db_access[os.getenv("MONGO_COLLECTION")]
embedding = EmbedGenerate()

prompt = input('Digite a frase para busca: ')
query = embedding.embed_query(prompt)

pipeline = [
    {
        "$vectorSearch": {
            "index": "vector_index",          
            "path": "objplusembbeding",              
            "queryVector" : query,
            "numCandidates": 100,
            "limit": 5
        }
    },
    {
        "$project": {
            "_id": 0,
            "text": 1,
            "score": {"$meta": "vectorSearchScore"}
        }
    }
]

results = list(collection_access.aggregate(pipeline))

print("\nInput →", prompt)
print("\nResultados semelhantes:")

print(f"\nInput -> {prompt}")
print(f"\nDocumentos semelhantes:\n{results}")