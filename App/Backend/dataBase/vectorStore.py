import os
import logging
from torch import embedding
from App.Backend.rag.embedGenerate import EmbedGenerate
from App.Backend.rag.chunkGenerate import ChunkGenerate
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

class VectorStoreMongo():
    def __init__(self):
        self.mongo_client = MongoClient(os.getenv("MONGO_ADDRESS"), server_api=ServerApi('1'))
        self.db_access = self.mongo_client[os.getenv("MONGO_DB")]
        self.collection_access = self.db_access[os.getenv("MONGO_COLLECTION")]
        self.embedding = EmbedGenerate()
        self.chunking = ChunkGenerate()

    def create_obj(doc_name: str, chunk_id: int, text: str, embedding: list[float]) -> dict:
        return {
            "doc_name": doc_name,
            "chunk_id": chunk_id,
            "text": text,
            "embedding": embedding
        }
    
    def insert_objs(collection, data: dict) -> str | None:
    #verifica se o objeto da colecao e valido
        if collection is None:
            logging.error("Collection unavailable for insertion.")
            return None
        try:
            res = collection.insert_several(data, ordered=False)
            return [str(_id) for _id in res.inserted_ids]
        except Exception as e:
            logging.error(f"Error inserting many objects: {e}")
            return None


    def insert_single(self):
        chunk_collection = self.chunking.create_dinamic_chunk()
        embed_collection = self.embedding.embed_text()

        for i in range(len(chunk_collection)):
            new_object = {
                '_id': i,
                'vector': embed_collection[i],
                'chunk': chunk_collection[i]
            }

            self.collection_access.insert_one(new_object)

    def insert_several(self):
        chunk_collection = self.chunking.create_dinamic_chunk()
        embed_collection = self.embedding.embed_text()

        self.collection_access.insert_many(
            {'_id': i, 'vector': embed_collection[i], 'chunk': chunk_collection[i]} for i in range(len(chunk_collection))
            )

    def ping(self):
        self.mongo_client.admin.command('ping')
        print("Entrou!")
