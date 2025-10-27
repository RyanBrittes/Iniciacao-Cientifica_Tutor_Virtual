from extractorPDF import ExtractorPDF

class ChunkGenerate():
    def __init__(self):
        self.extractor = ExtractorPDF()
        self.chunk_static_size = 500
        self.overlap_static_size = 50
        self.overlap_dinamic_size = 10

    def create_static_chunk(self):
        text = self.extractor.extract_pdf_to_text()
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_static_size, text_length)
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end >= text_length:
                break
                
            start += self.chunk_static_size - self.overlap_static_size
            
            if self.overlap_static_size >= self.chunk_static_size:
                start = end
        
        return chunks
    
    def create_dinamic_chunk(self):
        text = self.extractor.extract_pdf_to_text()
        chunks = []
        overlap = ""
        count = 0
        index_letter = 0
        index_start = 0
        index_overlap = 1

        while index_letter < len(text):
            if text[index_letter] == ".":
                chunk = text[index_start:index_letter + 1]
                index_start = index_letter + 2
                chunks.append(overlap + chunk)

                while count < self.overlap_dinamic_size:
                    if chunk[-index_overlap] in [" ", ","]:
                        count += 1
                    
                    if index_overlap == len(chunk):
                        break

                    index_overlap += 1

                overlap = chunk[-index_overlap + 1:]
                count = 1
                index_overlap = 0

            index_letter += 1

        return chunks

    def create_dinamic_chunk_no_overlap(self):
        text = self.extractor.extract_pdf_to_text()
        chunks = []
        initial_point = 0
        count = 0

        for i in text:
            if i == ".":
                chunk = text[initial_point:count + 1]
                initial_point = count + 1
                chunks.append(chunk)

            count += 1

        return chunks       
