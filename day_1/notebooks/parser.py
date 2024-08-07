"""General Parser."""
import os

import docx
from PyPDF2 import PdfReader


class PDFParser:
    def __init__(self):
        pass

    def parse(self, file_path: str) -> str:
        content = ""
        pdf_reader = PdfReader(file_path)
        for page in pdf_reader.pages:
            content += page.extract_text()
        return content

class TextParser:
    def __init__(self):
        pass

    def parse(self, file_path: str) -> str:
        """Parse content out of Text File."""
        content: str = ""
        with open(file_path, "r+", encoding="utf8") as f:
            content: str = f.read()
        return content
    
# TODO docx parser
class DocxParser:
    def __init__(self,):
        pass
    def parse(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        paragraphs = []
        for paragraph in doc.paragraphs:
            paragraphs.append(paragraph.text)
        content = "\n".join(paragraphs)
        return content

class FileParser:
    def __init__(self):
        pass

    def parse(self, file_path: str) -> str:
        path_list = os.path.split(file_path)
        file_name = path_list[-1]
        extension = file_name[file_name.rfind(".")+1:].lower()
        if extension == "pdf":
            parser = PDFParser()
        elif extension == "txt":
            parser = TextParser()
        elif extension == "docx":
            parser = DocxParser()
        else:
            raise Exception(f"No Parser for type {extension}")
        
        content = parser.parse(file_path)
        return content, file_name
