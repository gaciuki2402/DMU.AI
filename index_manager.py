from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from document_loader import load_documents
from database_manager import get_conversation_history
import logging
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
print(f"Key: {openai_api_key}")
if not openai_api_key:
    raise ValueError(
        "Please set the OPENAI_API_KEY environment variable in the .env file."
    )

embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
vectorstore = None

# embeddings = OpenAIEmbeddings()
# vectorstore = None  # Initialize the global variable


def create_new_index():
    global vectorstore
    try:
        docs = load_documents()
        if not docs:
            logger.warning("No documents loaded. Using fallback document.")
            docs = [
                Document(
                    page_content="Fallback document content.",
                    metadata={"source": "fallback"},
                )
            ]
        else:
            logger.info(f"Loaded {len(docs)} documents.")
            for doc in docs:
                logger.info(
                    f"Document content (first 100 chars): {doc.page_content[:100]}..."
                )

        logger.info("Creating embeddings...")
        vectorstore = FAISS.from_documents(docs, embeddings)
        logger.info(f"Created vectorstore with {len(docs)} documents.")

        return vectorstore
    except Exception as e:
        logger.error(f"Error creating new index: {e}")
        return None


def load_or_create_index(force_update=False):
    global vectorstore
    if vectorstore is not None and not force_update:
        logger.info("Using existing index.")
        return vectorstore
    else:
        logger.info("Creating new index.")
        return create_new_index()


def update_index_with_interaction(question, answer, conversation_id):
    global vectorstore
    if vectorstore is None:
        vectorstore = create_new_index()

    conversation_history = get_conversation_history(conversation_id)
    recent_history = conversation_history[-6:]  # Get last 6 interactions
    history_str = "\n".join([f"Q: {q}\nA: {a}" for q, a, _ in recent_history])

    new_doc = Document(
        page_content=f"Conversation ID: {conversation_id}\nRecent History:\n{history_str}\nQ: {question}\nA: {answer}",
        metadata={"source": "user_interaction", "conversation_id": conversation_id},
    )
    vectorstore.add_documents([new_doc])
    logger.info(
        f"Added new interaction to the index for conversation {conversation_id}"
    )


def get_relevant_context(question, conversation_id):
    logger.info(f"Getting relevant context for question: {question}")
    conversation_history = get_conversation_history(conversation_id)

    # Use only the last 6 interactions to keep context relevant
    recent_history = conversation_history[-6:]
    history_str = "\n".join([f"Human: {q}\nAI: {a}" for q, a, _ in recent_history])

    if vectorstore:
        search_query = f"{question}\n\nRecent context: {history_str}"
        relevant_docs = vectorstore.similarity_search(search_query, k=3)
        logger.info(f"Retrieved {len(relevant_docs)} documents:")
        context_parts = []
        for i, doc in enumerate(relevant_docs):
            logger.info(
                f"Document {i+1} content (first 200 chars): {doc.page_content[:200]}..."
            )
            context_parts.append(f"Document {i+1}:\n{doc.page_content}")

        context = "\n\n".join(context_parts)

        return f"Relevant context:\n{context}\n\nRecent history:\n{history_str}"
    else:
        logger.warning(
            "Vectorstore is not initialized. Returning only conversation history."
        )
        return f"I don't have specific information about this topic. Recent conversation:\n{history_str}"


# Initialize the vectorstore
vectorstore = load_or_create_index()


def refresh_index():
    global vectorstore
    logger.info("Refreshing index with latest documents...")
    vectorstore = create_new_index()
    logger.info("Index refreshed.")


# You might want to call this function periodically or on-demand
# refresh_index()
