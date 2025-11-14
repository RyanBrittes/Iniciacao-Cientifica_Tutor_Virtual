import os
import logging
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

    def insert_several(self):
            chunk_collection = self.chunking.create_dinamic_chunk()
            embed_collection = self.embedding.embed_text()

            obj = [
                {
                    'text': chunk_collection[i],
                    'embedding': embed_collection[i]
                }
                for i in range(len(chunk_collection))
            ]


            try:
                self.collection_access.insert_many(obj)
                logging.info("inserido no banco com sucesso")
            except Exception as e:
                logging.error(f"erro ao inserir no banco: {e}")


    def ping(self):
        self.mongo_client.admin.command('ping')
        print("Entrou!")
