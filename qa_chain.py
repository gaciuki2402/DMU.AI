from langchain_openai import OpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.memory import ConversationBufferMemory

llm = OpenAI(temperature=0, max_tokens=500)

def get_qa_chain(vectorstore):
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages = True
    )
    return RetrievalQAWithSourcesChain.from_llm(
        llm = llm,
        retriever = vectorstore.as_retriever(),
        memory=memory,
        return_source_documents = True,
        verbose=True
    )