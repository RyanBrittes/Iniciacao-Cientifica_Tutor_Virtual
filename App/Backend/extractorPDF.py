import fitz

class ExtractorPDF():
    def __init__(self):
        self.pdf_path = "files/Texto_Exemplo.pdf"
        self.pdf_file = fitz.open(self.pdf_path)
    
    def extract_pdf_to_text(self):
        text = ""

        for page in self.pdf_file:
            text += page.get_text("text")

            text = text.replace("\n", " ")
            text = " ".join(text.split())
            
        return text
    
    def extract_pdf_to_token(self):
        tokens = []
        initial_point = 0
        count = 0
        text = self.extract_pdf_to_text()

        for i in text:
            if i in [" ", "."]:
                token = text[initial_point:count + 1]
                initial_point = count + 1
                tokens.append(token)
            count += 1

        return tokens
    