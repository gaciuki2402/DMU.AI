from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from config import load_environment
from index_manager import load_or_create_index, update_index_with_interaction, get_relevant_context
from qa_chain import get_qa_chain
import logging
import openai
import os
from database_manager import init_db, store_interaction, update_feedback, get_conversation_history
import uuid
from pydantic import ValidationError
from typing import Optional
from langchain.memory import ConversationBufferMemory


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

load_environment()
init_db()
vectorstore = load_or_create_index()
print("global access")

# load openai api key from env
openai.api_key =os.getenv("OPENAI_API_KEY")


class Question(BaseModel):
    question: str
    format: str = "default"   #options: "default", "summary", "simplified"
    conversation_id: Optional[str] = None

class Feedback(BaseModel):
    interaction_id: int
    feedback: int

def summarize_content(content):
    response = openai.Completion.create(
        engine="davinci-codex",
        prompt = f"Summarize the following content: {content}",
        max_tokens=150
    )
    return response.choices[0].text.strip()

def simplify_content(content):
    response = openai.Completion.create(
        engine="davinci-codex",
        prompt=f"Simplify the following content: {content}",
        max_token=300
    )
    return response.choices[0].text.strip()

conversation_memory = {}

@app.post("/ask")
async def ask_question(question: Question, background_tasks: BackgroundTasks):
    logger.info(f"Received question data: {question.dict()}")
    logger.info(f"Received question: {question.question}")
    logger.info(f"Receeived format: {question.format}")
    logger.info(f"Received conversation_id: question.conversation_id")
    
    qa_chain = get_qa_chain(vectorstore)
    if qa_chain is None:
        raise HTTPException(status_code=500, detail="QA system is not initialized")
    
    if not question.conversation_id:
        question.conversation_id = str(uuid.uuid4())
    

    # initialize or retrieve conversation memory
    if question.conversation_id not in conversation_memory:
        conversation_memory[question.conversation_id] = ConversationBufferMemory(return_messages=True)
    memory = conversation_memory[question.conversation_id]
    memory.chat_memory.add_user_message(question.question)
    # get conversation history
    conversation_history = memory.chat_memory.messages
        
    relevant_context = get_relevant_context(question.question, question.conversation_id)
        
    # adding instructions based on format
    system_instructions = {
        "default": "Answer normally.",
        "summary": "Provide a brief summary.",
        "simplified": "Priovide a detailed answer using simplified words."
    }
    format_instructions = system_instructions.get(question.format, "Answer normally.")

    # combine user question with system instructions
    complete_question = (
        f"Conversation history: \n{'\n'.join([f'{msg.type}: {msg.content}' for msg in conversation_history])}\n\n"
        f"Question: {question.question}\n\n"
        f"Current question: {question.question}\n\n"
        f"System Instructions: You are DMU Assistant, a DMU AI assistant meant to only answer from context. "
        f"Please engage the user in a customer care manner, responding to their questions with respect and well-thought-out answers. "
        f"If you don't know the answer, admit not knowing and suggest another question that the user may ask based on what you know. "
        f"Do not mention sources or where you got the information from in any way. "
        f"Use the provided context to inform your response."
        f"{format_instructions}\n"
        f"Relevant context: {relevant_context}"
    )
    result = qa_chain({"question": complete_question})
    if not result or 'answer' not in result:
        raise HTTPException(status_code=500, detail="Failed to generate an answer")

    answer = result['answer']

    if question.format == "summary":
        answer = summarize_content(answer)
    elif question.format == "simplified":
        answer = simplify_content(answer)

    # add the response to memory
    memory.chat_memory.add_ai_message(answer)
    
    interaction_id = store_interaction(question.conversation_id, question.question, answer, question.format)

    # Update the index with the new interaction
    background_tasks.add_task(update_index_with_interaction, question.question, answer)

    logger.info(f"Generated answer: {result['answer'][:100]}...")  # Log first 100 chars of answer
    return {
        "interaction_id": interaction_id,
        "conversation_id": question.conversation_id,
        "answer": result['answer'],
        "sources": result.get('sources', [])
}
@app.post("/feedback")
async def submit_feedback(feedback: Feedback):
    update_feedback(feedback.interaction_id, feedback.feedback)
    return {"message": "Feedback received"}

@app.get("/")
async def root():
    return {"message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8050)

