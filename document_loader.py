from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import logging

logger = logging.getLogger(__name__)

def load_documents():
    # current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    pdf_paths = ['upload/DMUDataSet2.pdf']

    # Load PDFs 
    all_data = []
    for pdf_path in pdf_paths:
        if os.path.exists(pdf_path):
            logger.info(f"Loading PDF: {pdf_path}")
            try:
                loader = PyPDFLoader(pdf_path)
                all_data.extend(loader.load())
            except Exception as e:
                logger.error(f"Error loading {pdf_path}: {str(e)}")
        else:
            logger.warning(f"Warning: PDF file not found: {pdf_path}")
    
    if not all_data:
        logger.warning("No PDF documents were loaded. Please check your PDF file locations.")
        
        # Fallback to a simple text document
        fallback_text = "This is a fallback document. No PDFs were successfully loaded."
        all_data = [Document(page_content=fallback_text, metadata={"source": "fallback"})]

    # Split text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    docs = text_splitter.split_documents(all_data)

    logger.info(f"Loaded {len(docs)} document chunks.")
    return docs

# Uncomment the following line if you want to test the function directly
# load_documents()
