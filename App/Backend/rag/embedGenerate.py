import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nomic import embed
from rag.chunkGenerate import ChunkGenerate

class EmbedGenerate:
    def __init__(self):
        self.chunks = ChunkGenerate()
        
    #Criador de embeddings, cria um dicionário com 4 chaves a partir de um documento dividido em blocos menores (chunks)
    def embed_text(self):
        chunks = self.chunks.create_static_chunk_token()

        output = embed.text(
            texts=chunks,
            model='nomic-embed-text-v1.5',
            task_type='search_document'
            #inference_mode='local',
            #device='cpu'
        )['embeddings']
        return [output, chunks]
    
    #Este código está implementado utilizando a API do Nomic, caso deseje processar localmente,
    #Apague os hastags de inference_mode e device
    def embed_query(self, query: str):
        output = embed.text(
            texts=[query],
            model='nomic-embed-text-v1.5',
            task_type='search_document'
            #inference_mode='local',
            #device='cpu'
        )['embeddings']
        return output
    
    def embed_openai(self):
        return self
    