import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.wsgi import WSGIMiddleware
from flask import Flask, render_template, request, jsonify, send_from_directory
import logging
import os
import uuid
from typing import Optional, List
from pydantic import BaseModel
import asyncio
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from config import load_environment
from index_manager import load_or_create_index, update_index_with_interaction, get_relevant_context
from db_manager import (
    init_db, store_interaction, update_feedback,
    get_conversation_history, get_all_conversations,
    create_new_conversation, update_conversation_title, get_conversation, delete_conversation,
    get_feedback_statistics, get_low_rated_interactions, update_interaction_for_improvement,
    get_recent_positive_interactions
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app setup
flask_app = Flask(__name__, static_folder="static")

# FastAPI app setup
app = FastAPI()

# Load environment variables and initialize database
load_environment()
init_db()

# Load or create vector index
vectorstore = load_or_create_index()

# Initialize the language model
model = ChatOpenAI()

# Create the prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are DMU Assistant, an AI specifically designed for De Montfort University (DMU). Your role is to provide accurate and helpful information about DMU based solely on the given context. Adhere to these guidelines:

    1. Only answer questions using the provided context about DMU.
    2. Engage users in a respectful and customer-care oriented manner.
    3. Provide well-thought-out, accurate responses to questions about DMU.
    4. If the context doesn't contain the answer, politely admit not knowing.
    5. Do not mention or reference any sources of information.
    6. For lists or steps, use numerical formatting (1. 2. 3.) or letter formatting (a. b. c.) without any special characters. Please use new paragraphs for clarity when listing.
    7. Always maintain a professional, helpful, and friendly tone.
    8. Focus exclusively on DMU-related information; do not discuss other universities.
    9. If asked about personal opinions or experiences, clarify that you can only provide factual information about DMU based on the given context.

    Remember, your purpose is to assist with DMU-related queries using only the information provided in the context. Avoid using the statement about based on the context"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
    ("system", "Relevant DMU context: {context}")
])

# Create the chain
chain = prompt | model

# Wrap the chain with message history
chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: SQLChatMessageHistory(
        session_id=session_id, connection_string="sqlite:///chat_history.db"
    ),
    input_messages_key="question",
    history_messages_key="history",
)

# Pydantic models
class Question(BaseModel):
    question: str
    conversation_id: Optional[str] = None

class Feedback(BaseModel):
    interaction_id: int
    is_helpful: bool

class Message(BaseModel):
    sender: str
    content: str
    timestamp: str

class Conversation(BaseModel):
    id: str
    title: str
    messages: List[Message]

class ChatHistory(BaseModel):
    conversations: List[Conversation]

# Flask routes
@flask_app.route("/")
def index():
    return render_template("index.html")

@flask_app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)

# FastAPI routes
@app.post("/api/ask")
async def ask_question(question: Question, background_tasks: BackgroundTasks):
    logger.info(f"Received question: {question.question}")
    
    try:
        if not question.conversation_id:
            question.conversation_id = str(uuid.uuid4())
            create_new_conversation(question.conversation_id, question.question[:30])
            logger.info(f"Created new conversation with ID: {question.conversation_id}")
        else:
            conversation = get_conversation(question.conversation_id)
            if not conversation:
                create_new_conversation(question.conversation_id, question.question[:30])
                logger.info(f"Created new conversation with ID: {question.conversation_id}")

        relevant_context = get_relevant_context(question.question, question.conversation_id)
        
        positive_interactions = get_recent_positive_interactions(limit=5)
        for q, a in positive_interactions:
            relevant_context += f"\nQ: {q}\nA: {a}\n"
        
        logger.info(f"Retrieved relevant context: {relevant_context[:500]}...")

        config = {"configurable": {"session_id": question.conversation_id}}
        
        result = chain_with_history.invoke(
            {"question": question.question, "context": relevant_context},
            config=config
        )

        answer = result.content
        logger.info(f"Generated answer: {answer[:500]}...")

        interaction_id = store_interaction(question.conversation_id, question.question, answer, "default")
        update_conversation_title(question.conversation_id, question.question[:30])
        background_tasks.add_task(update_index_with_interaction, question.question, answer, question.conversation_id)

        return {
            "interaction_id": interaction_id,
            "conversation_id": question.conversation_id,
            "answer": answer,
        }
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while processing your question: {str(e)}")

@app.post("/api/feedback")
async def submit_feedback(feedback: Feedback):
    try:
        feedback_value = 1 if feedback.is_helpful else 0
        update_feedback(feedback.interaction_id, feedback_value)
        return {"message": "Feedback received"}
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while submitting feedback: {str(e)}")

@app.get("/api/chat_history")
async def get_chat_history_endpoint():
    conversations = get_all_conversations()
    return ChatHistory(conversations=[Conversation(id=id, title=title, messages=[]) for id, title in conversations])

@app.get("/api/conversation/{conversation_id}")
async def get_conversation_endpoint(conversation_id: str):
    history = get_conversation_history(conversation_id)
    messages = []
    for question, answer, timestamp in history:
        messages.append(Message(sender="Human", content=question, timestamp=str(timestamp)))
        messages.append(Message(sender="AI", content=answer, timestamp=str(timestamp)))
    return Conversation(id=conversation_id, title=f"Conversation {conversation_id[:8]}", messages=messages)

@app.post("/api/conversation/new")
async def create_new_conversation_endpoint():
    conversation_id = str(uuid.uuid4())
    title = f"New Conversation {conversation_id[:8]}"
    create_new_conversation(conversation_id, title)
    return {"conversation_id": conversation_id, "title": title}

@app.delete("/api/conversation/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: str):
    try:
        delete_conversation(conversation_id)
        return {"message": "Conversation deleted"}
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting the conversation: {str(e)}")

@app.get("/api")
async def root():
    return {"message": "API is running"}

async def periodic_feedback_analysis():
    while True:
        try:
            stats = get_feedback_statistics()
            if stats:
                positive_ratio, negative_ratio, avg_feedback = stats
                logger.info(f"Feedback stats: Positive: {positive_ratio:.2f}, Negative: {negative_ratio:.2f}, Average: {avg_feedback:.2f}")
                
                if negative_ratio > 0.3:  # If more than 30% feedback is negative
                    low_rated = get_low_rated_interactions()
                    for interaction_id, question, answer, feedback in low_rated:
                        improved_answer = await improve_answer(question, answer)
                        update_interaction_for_improvement(interaction_id, improved_answer)
                        logger.info(f"Improved answer for question: {question}")
            
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error(f"Error in periodic feedback analysis: {str(e)}")
            await asyncio.sleep(3600)  # Wait an hour before retrying

async def improve_answer(question, previous_answer):
    context = get_relevant_context(question)
    prompt = f"""
    The following question received a low rating:
    Question: {question}
    Previous Answer: {previous_answer}
    
    Please provide an improved answer based on the following context:
    {context}
    
    Improved Answer:
    """
    response = await model.agenerate([prompt])
    return response.generations[0][0].text

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_feedback_analysis())

# Mount Flask app
app.mount("/", WSGIMiddleware(flask_app))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)