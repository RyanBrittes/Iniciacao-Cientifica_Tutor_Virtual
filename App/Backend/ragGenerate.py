from vectorStore import VectorStore
from embedGenerate import EmbedGenerate

#Classe utilizada para juntar as funcionalidades do RAG e pronta para ser chamada
class RagGenerate():
    def __init__(self):
        self.vector_store = VectorStore()
        self.embed = EmbedGenerate()
    
    #Método que mescla o armazenamento vetorial e o embedder
    def compair_vector(self, question: str, collection_name):
        query = self.embed.embed_query(question)
        
        return self.vector_store.collection_query(query, collection_name)
    