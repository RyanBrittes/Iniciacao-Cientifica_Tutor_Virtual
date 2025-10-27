import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from instructions import Instructions
from ragGenerate import RagGenerate

load_dotenv()

class Menu():
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.client.chats.create
        self.chat = self.client.chats.create(model="gemma-3-27b-it", 
                                             config= types.GenerateContentConfig(
                                                 temperature=0.1,
                                                 #top_p=1,
                                                 #max_output_tokens=200,
                                                 #top_k=,
                                                 stop_sequences=[]))
        self.instructions = Instructions()
        self.recovery = RagGenerate()
        self.collection_name = "Chunk_Static_CH500_OV50"

    def post_message_norag(self, question):
        full_prompt = f"""
            {self.instructions.get_instructions("04")}
            {self.instructions.get_instructions("01")}
            Pergunta: {question}
            """
        return self.chat.send_message(full_prompt).text

    def post_message_rag(self, question):
        relevant_docs = self.recovery.compair_vector(question, self.collection_name)

        context_text = ""
        if 'documents' in relevant_docs and relevant_docs['documents']:
            for doc_list in relevant_docs['documents']:
                for doc in doc_list:
                    context_text += f"{doc}\n\n"

        full_prompt = f"""
            {self.instructions.get_instructions("04")}
            {self.instructions.get_instructions("01")}
            Responda com base nas seguintes informações:
            {context_text} 
            Se as informações não tiverem relação com a pergunta a seguir, desconsidere o uso delas.
            Pergunta: {question}
            """
        
        return self.chat.send_message(full_prompt).text
