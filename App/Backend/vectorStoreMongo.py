from embedGenerate import EmbedGenerate
from chunkGenerate import ChunkGenerate
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

class VectorStoreMongo():
    def __init__(self):
        self.mongo_client = MongoClient(os.getenv("MONGO_ADDRESS"), server_api=ServerApi('1'))
        self.db_access = self.mongo_client[os.getenv("MONGO_DB")]
        self.collection_access = self.db_access[os.getenv("MONGO_COLLECTION")]
        self.embedding = EmbedGenerate()
        self.chunking = ChunkGenerate()

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
