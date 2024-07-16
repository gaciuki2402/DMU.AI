from langchain.chains import RetrievalQA
from langchain_openai import OpenAI

def get_qa_chain(vectorstore):
    llm = OpenAI(temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        return_source_documents=True
    )
    return qa_chain
