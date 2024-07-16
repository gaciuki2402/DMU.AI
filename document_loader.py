from xml.dom.minidom import Document
from langchain_community.document_loaders import PyPDFLoader, UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

def load_documents():
    # current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    pdf_paths = [
        os.path.join(current_dir, 'C:/Users/delbr/DMU/DMU2.pdf'),
        os.path.join(current_dir, 'C:/Users/delbr/DMU/DMU1.pdf'),
        os.path.join(current_dir, 'C:/Users/delbr/DMU/DMU3.pdf') #C:\Users\delbr\DMU\DMU1.pdf
    ]
    #print(pdf_paths)

      # Load PDFs 
    all_data = []
    for pdf_path in pdf_paths:
        if os.path.exists(pdf_path):
            print(f"Loading PDF: {pdf_path}")
            try:
                loader = PyPDFLoader(pdf_path)
                all_data.extend(loader.load())
            except Exception as e:
                print(f"Error loading {pdf_path}: {str(e)}")
        else:
            print(f"Warning: PDF file not found: {pdf_path}")
    
    if not all_data:
        print("No PDF documents were loaded. Please check your PDF file locations.")
        
        # Fallback to a simple text document
        fallback_text = "This is a fallback document. No PDFs were successfully loaded."
        all_data = [Document(page_content=fallback_text, metadata={"source": "fallback"})]

        # Split text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.split_documents(all_data)

        print(f"Loaded {len(docs)} document chunks.")
        return docs
    return all_data
    
#load_documents()