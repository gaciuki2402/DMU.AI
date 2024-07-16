from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from document_loader import load_documents

embeddings = OpenAIEmbeddings()
vectorstore = None  # Initialize the global variable

def create_new_index():
    global vectorstore
    try:
        docs = load_documents()
        if not docs:
            print("No documents loaded. Using fallback document.")
            docs = [Document(page_content="Fallback document content.", metadata={"source": "fallback"})]
        
        print("Creating embeddings...")
        embeddings_list = embeddings.embed_documents([doc.page_content for doc in docs])
        
        if not embeddings_list:
            raise ValueError("No embeddings created. Check your OpenAI API key and network connection.")
        
        print(f"Created {len(embeddings_list)} embeddings.")
        
        vectorstore = FAISS.from_documents(docs, embeddings)
        return vectorstore
    except Exception as e:
        print(f"Error creating new index: {e}")
        return None

def load_or_create_index(force_update=False):
    global vectorstore
    if vectorstore is not None and not force_update:
        print("Using existing index.")
        return vectorstore
    else:
        return create_new_index()

def update_index_with_interaction(question, answer):
    global vectorstore
    if vectorstore is None:
        vectorstore = create_new_index()
    
    new_doc = Document(page_content=f"Q: {question}\nA: {answer}", metadata={"source": "user_interaction"})
    vectorstore.add_documents([new_doc])
    print(f"Added new interaction to the index.")

def get_relevant_context(question, conversation_history):
    # Convert conversation history to a string if it's not already
    if isinstance(conversation_history, list):
        history_str = "\n".join([f"Human: {q}\nAI: {a}" for q, a in conversation_history])
    else:
        history_str = conversation_history

    search_query = f"{history_str}\nHuman: {question}"

    # Get relevant documents from vectorstore
    if vectorstore:
        relevant_docs = vectorstore.similarity_search(search_query, k=3)
        context = "\n".join([doc.page_content for doc in relevant_docs])
        return f"{history_str}\n\nRelevant context:\n{context}"
    
    return history_str

# Initialize the vectorstore
vectorstore = load_or_create_index()