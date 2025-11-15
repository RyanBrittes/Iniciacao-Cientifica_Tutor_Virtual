import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
import os
from dotenv import load_dotenv
from rag.embedGenerate import EmbedGenerate

load_dotenv()

class VectorSearch:
    def __init__(self):
        self.mongo_client = MongoClient(os.getenv("MONGO_ADDRESS"))
        self.db_access = self.mongo_client[os.getenv("MONGO_DB")]
        self.collection_access = self.db_access[os.getenv("MONGO_COLLECTION")]
        self.embedding = EmbedGenerate()

    def search(self, prompt):
        query = self.embedding.embed_query(prompt)

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "cosine-index",
                    "path": "embedding",
                    "queryVector": query,
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

        results = list(self.collection_access.aggregate(pipeline))
        
        return results[0]

if __name__ == "__main__":
    searcher = VectorSearch()
    prompt = input('Digite a frase para busca: ')
    results = searcher.search(prompt)

    print("\nInput →", prompt)
    print("\nResultados semelhantes:")

    print(f"\nInput -> {prompt}")
    print(f"\nDocumentos semelhantes:\n{results}")

