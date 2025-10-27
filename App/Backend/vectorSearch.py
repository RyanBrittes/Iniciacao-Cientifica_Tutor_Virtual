from pymongo import MongoClient
import os
from dotenv import load_dotenv
from embedGenerate import EmbedGenerate

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGO_ADDRESS"))
db_access = mongo_client[os.getenv("MONGO_DB")]
collection_access = db_access[os.getenv("MONGO_COLLECTION")]
embedding = EmbedGenerate()

prompt = input('Digite a frase para busca: ')
query = embedding.embed_query(prompt)

collection_access.create_index(
    [('vector', 'vector')],
    name='vector-search-index',
    extra={'vectorIndexType': 'hnsw', 'vectorIndexParams': {'dim': 768, 'similarity': 'cosine'}}
)

search = db_access.command({
    'aggregate': 'vector-store',
    'pipeline': [
        {
            "$vectorSearch": {
                "queryVector": query,
                "path": "vector",
                "numCandidates": 15,
                "limit": 8,
                "index": "vector-search-index"
                }
        },
        {"$project": {"_id": 0, "texto": 1, "score": {"$meta": "vectorSearchScore"}}}
    ],
    'cursor': {}
})


print(f"\nInput -> {prompt}")
print(f"\nDocumentos semelhantes:\n{search}")