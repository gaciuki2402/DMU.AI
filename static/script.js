let currentConversationId = null;
let questionCounter = 0;

document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadChatHistory();
});

function initializeEventListeners() {
    document.getElementById('new-chat-btn').addEventListener('click', startNewChat);
    document.getElementById('send-button').addEventListener('click', sendMessage);
    document.getElementById('user-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    document.getElementById('user-input').addEventListener('input', autoResizeTextarea);
}

function autoResizeTextarea() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
}

async function loadChatHistory() {
    try {
        const response = await fetch('/chat_history');
        const data = await response.json();
        updateChatHistoryList(data.conversations);
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

function updateChatHistoryList(conversations) {
    const chatHistoryList = document.getElementById('chat-history-list');
    chatHistoryList.innerHTML = '';

    conversations.forEach(conversation => {
        const item = document.createElement('div');
        item.className = 'chat-history-item flex items-center justify-between p-2 border-b border-gray-300';
        item.dataset.conversationId = conversation.id;
        
        const title = document.createElement('span');
        title.textContent = conversation.title;
        
        const deleteButton = document.createElement('button');
        deleteButton.className = 'delete-chat-button text-red-500 hover:text-red-700';
        deleteButton.textContent = 'Delete';
        deleteButton.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent triggering the loadChat function
            if (confirm('Are you sure you want to delete this chat?')) {
                deleteChat(conversation.id);
            }
        });

        item.appendChild(title);
        item.appendChild(deleteButton);
        item.addEventListener('click', () => loadChat(conversation.id));
        chatHistoryList.appendChild(item);
    });
}

async function loadChat(conversationId) {
    currentConversationId = conversationId;
    try {
        const response = await fetch(`/conversation/${conversationId}`);
        const data = await response.json();
        clearChatContainer();
        data.messages.forEach(msg => {
            displayMessage(msg.content, msg.sender === 'Human' ? 'user' : 'bot', msg.interaction_id);
        });
        questionCounter = data.messages.filter(msg => msg.sender === 'Human').length;
    } catch (error) {
        console.error('Error loading chat:', error);
    }
}

function clearChatContainer() {
    const chatContainer = document.getElementById('chat-container');
    chatContainer.innerHTML = '';
}

async function startNewChat() {
    try {
        const response = await fetch('/conversation/new', { method: 'POST' });
        const data = await response.json();
        currentConversationId = data.conversation_id;
        clearChatContainer();
        loadChatHistory();
        questionCounter = 0;
    } catch (error) {
        console.error('Error creating new conversation:', error);
    }
}

async function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    if (message) {
        displayMessage(message, 'user');
        userInput.value = '';
        autoResizeTextarea.call(userInput);

        questionCounter++;

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: message,
                    format: 'default',
                    conversation_id: currentConversationId
                }),
            });
            const data = await response.json();
            if (data.answer) {
                displayMessage(data.answer, 'bot', data.interaction_id);
                checkQuestionLimit();
            } else {
                console.error('No answer in response');
                displayMessage('Sorry, I couldn\'t generate an answer.', 'bot');
            }
            currentConversationId = data.conversation_id;
            loadChatHistory();
        } catch (error) {
            console.error('Error:', error);
            displayMessage('Sorry, there was an error processing your request. Please try again.', 'bot');
        }
    }
}

function checkQuestionLimit() {
    if (questionCounter >= 7) {
        const message = "You've asked 7 questions in this conversation. Would you like to start a new chat for better context management?";
        displayMessage(message, 'bot');
        displayNewChatPrompt();
    }
}

function displayNewChatPrompt() {
    const chatContainer = document.getElementById('chat-container');
    const promptElement = document.createElement('div');
    promptElement.className = 'new-chat-prompt';
    promptElement.innerHTML = `
        <button onclick="startNewChat()" class="new-chat-button">
            Start New Chat
        </button>
    `;
    chatContainer.appendChild(promptElement);
}

async function deleteChat(conversationId) {
    try {
        const response = await fetch(`/conversation/${conversationId}`, { method: 'DELETE' });
        if (response.ok) {
            loadChatHistory();
            if (currentConversationId === conversationId) {
                clearChatContainer();
                currentConversationId = null;
                questionCounter = 0;
            }
        } else {
            console.error('Failed to delete conversation');
            alert('Failed to delete conversation');
        }
    } catch (error) {
        console.error('Error deleting conversation:', error);
        alert('Error deleting conversation');
    }
}

function displayMessage(message, sender, interactionId = null) {
    const chatContainer = document.getElementById('chat-container');
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);
    
    const icon = document.createElement('img');
    icon.src = sender === 'user' ? '/static/default-user-avatar.png' : '/static/dmu.jpeg';
    icon.alt = sender === 'user' ? 'User Avatar' : 'DMU Logo';
    icon.className = 'message-icon';
    
    const content = document.createElement('div');
    content.className = 'message-content';

    const formattedMessage = formatMessage(message);
    content.innerHTML = formattedMessage;

    if (sender === 'bot' && message.includes("You've asked 7 questions")) {
        content.classList.add('question-limit-prompt');
    }

    const timestamp = document.createElement('span');
    timestamp.className = 'timestamp';
    timestamp.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageElement.appendChild(icon);
    messageElement.appendChild(content);
    messageElement.appendChild(timestamp);

    if (sender === 'bot' && interactionId) {
        const feedbackButtons = createFeedbackButtons(interactionId);
        messageElement.appendChild(feedbackButtons);
    }
    
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function formatMessage(message) {
    // Convert numbered lists
    message = message.replace(/(\d+\.)\s(.*?)(?=(?:\n\d+\.|\n\n|$))/gs, '<li>$2</li>');
    
    // Convert bullet points
    message = message.replace(/•\s(.*?)(?=(?:\n•|\n\n|$))/gs, '<li>$1</li>');
    
    // Wrap lists in <ol> or <ul> tags
    message = message.replace(/<li>.*?(?=<li>|$)/gs, match => {
        return match.includes('1.') ? `<ol>${match}</ol>` : `<ul>${match}</ul>`;
    });
    
    // Convert bold text
    message = message.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    
    // Convert paragraphs
    message = message.replace(/(.+?)(\n\n|$)/g, '<p>$1</p>');
    
    return message;
}

function createFeedbackButtons(interactionId) {
    const feedbackButtons = document.createElement('div');
    feedbackButtons.classList.add('feedback-buttons');
    feedbackButtons.innerHTML = `
        <button onclick="submitFeedback(${interactionId}, 3)" class="feedback-button okay">Helpful</button>
        <button onclick="submitFeedback(${interactionId}, 5)" class="feedback-button good">Not Helpful</button>
    `;
    return feedbackButtons;
}

function submitFeedback(interactionId, rating) {
    fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interaction_id: interactionId, feedback: rating }),
    })
    .then(response => response.json())
    .then(data => console.log('Feedback submitted:', data))
    .catch(error => console.error('Error submitting feedback:', error));
}
