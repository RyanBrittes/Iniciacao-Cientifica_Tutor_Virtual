#Exemplo de uso do nomic com processamento local de embeddings
from nomic import embed
from chunkGenerate import ChunkGenerate

#Classe que irá criar os embeddings dos textos e consultas
class EmbedGenerate:
    def __init__(self):
        self.chunks = ChunkGenerate()
        
    #Criador de embeddings, cria um dicionário com 4 chaves a partir de um documento dividido em blocos menores (chunks)
    def embed_text(self):
        output = embed.text(
            texts=self.chunks.create_dinamic_chunk(),
            model='nomic-embed-text-v1.5',
            task_type='search_document'
            #inference_mode='local',
            #device='cpu'
        )['embeddings']
        return output
    
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
    