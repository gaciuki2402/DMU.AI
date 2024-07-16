import logging
import os
import uuid
from typing import Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from config import load_environment
from index_manager import load_or_create_index, update_index_with_interaction, get_relevant_context
from qa_chain import get_qa_chain
from database_manager import (init_db, store_interaction, update_feedback, 
                              get_conversation_history, get_all_conversations, 
                              create_new_conversation, update_conversation_title)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Load environment variables and initialize database
load_environment()
init_db()

# Load or create vector index
vectorstore = load_or_create_index()

# Pydantic models
class Question(BaseModel):
    question: str
    format: str = "default"
    conversation_id: Optional[str] = None

class Feedback(BaseModel):
    interaction_id: int
    feedback: int

class Message(BaseModel):
    sender: str
    content: str
    interaction_id: Optional[int] = None
    timestamp: str

class Conversation(BaseModel):
    id: str
    title: str
    messages: List[Message]

class ChatHistory(BaseModel):
    conversations: List[Conversation]

# API routes
@app.post("/ask")
async def ask_question(question: Question, background_tasks: BackgroundTasks):
    logger.info(f"Received question: {question.question}")
    qa_chain = get_qa_chain(vectorstore)
    if qa_chain is None:
        raise HTTPException(status_code=500, detail="QA system is not initialized")
    
    if not question.conversation_id:
        question.conversation_id = str(uuid.uuid4())
    
    # Retrieve conversation history
    conversation_history = get_conversation_history(question.conversation_id)
    
    # Prepare the context with conversation history
    context = "Previous conversation:\n"
    for prev_question, prev_answer, _ in conversation_history:
        context += f"Human: {prev_question}\nAI: {prev_answer}\n"
    context += f"\nHuman: {question.question}\n"
    
    # Get relevant context from the vector store
    relevant_context = get_relevant_context(context, question.conversation_id)
    
    system_instructions = {
        "default": "Answer normally.",
        "summary": "Provide a brief summary.",
        "simplified": "Provide a detailed answer using simplified words."
    }
    format_instructions = system_instructions.get(question.format, "Answer normally.")
    
    complete_question = (
        f"{context}\n"
        f"System Instructions: You are DMU Assistant, a DMU AI assistant meant to only answer from context. "
        f"Please engage the user in a customer care manner, responding to their questions with respect and well-thought-out answers. "
        f"If you don't know the answer, admit not knowing and suggest another question that the user may ask based on what you know. "
        f"Do not mention sources or where you got the information from in any way. "
        f"Use the provided context to inform your response. "
        f"{format_instructions}\n"
        f"Relevant context: {relevant_context}"
    )

    result = qa_chain({"query": complete_question})
    if not result or 'result' not in result:
        raise HTTPException(status_code=500, detail="Failed to generate an answer")

    answer = result['result']

    interaction_id = store_interaction(question.conversation_id, question.question, answer, question.format)
    
    # Update conversation title
    update_conversation_title(question.conversation_id, question.question[:30])

    background_tasks.add_task(update_index_with_interaction, question.question, answer)

    logger.info(f"Generated answer: {answer[:100]}...")
    return {
        "interaction_id": interaction_id,
        "conversation_id": question.conversation_id,
        "answer": answer,
        "sources": result.get('source_documents', [])
    }

@app.post("/feedback")
async def submit_feedback(feedback: Feedback):
    update_feedback(feedback.interaction_id, feedback.feedback)
    return {"message": "Feedback received"}

@app.get("/chat_history")
async def get_chat_history_endpoint():
    conversations = get_all_conversations()
    return ChatHistory(conversations=[Conversation(id=id, title=title, messages=[]) for id, title in conversations])

@app.get("/conversation/{conversation_id}")
async def get_conversation_endpoint(conversation_id: str):
    history = get_conversation_history(conversation_id)
    messages = []
    for question, answer, timestamp in history:
        messages.append(Message(sender="Human", content=question, timestamp=str(timestamp)))
        messages.append(Message(sender="AI", content=answer, timestamp=str(timestamp)))
    return Conversation(id=conversation_id, title=f"Conversation {conversation_id[:8]}", messages=messages)

@app.post("/conversation/new")
async def create_new_conversation():
    conversation_id = str(uuid.uuid4())
    title = f"New Conversation {conversation_id[:8]}"
    create_new_conversation(conversation_id, title)
    return {"conversation_id": conversation_id, "title": title}

@app.get("/")
async def root():
    return {"message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8050)