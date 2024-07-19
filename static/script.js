let currentConversationId = null;

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

function loadChatHistory() {
    fetch('/chat_history')
        .then(response => response.json())
        .then(data => {
            updateChatHistoryList(data.conversations);
            if (data.conversations.length > 0) {
                loadChat(data.conversations[0].id);
            }
        })
        .catch(error => console.error('Error loading chat history:', error));
}

function updateChatHistoryList(conversations) {
    const chatHistoryList = document.getElementById('chat-history-list');
    chatHistoryList.innerHTML = '';
    conversations.forEach(conv => {
        const li = document.createElement('li');
        li.className = 'chat-history-item p-2 hover:bg-gray-700 cursor-pointer';
        li.textContent = conv.title || 'New chat';
        li.onclick = () => loadChat(conv.id);
        if (conv.id === currentConversationId) {
            li.classList.add('bg-gray-700');
        }
        chatHistoryList.appendChild(li);
    });
}

function loadChat(conversationId) {
    currentConversationId = conversationId;
    fetch(`/conversation/${conversationId}`)
        .then(response => response.json())
        .then(data => {
            clearChatContainer();
            data.messages.forEach(msg => {
                displayMessage(msg.content, msg.sender === 'Human' ? 'user' : 'bot', msg.interaction_id);
            });
            updateChatHistoryList(data.conversations);
        })
        .catch(error => console.error('Error loading chat:', error));
}

function clearChatContainer() {
    document.getElementById('chat-container').innerHTML = '';
}

function startNewChat() {
    fetch('/conversation/new', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            currentConversationId = data.conversation_id;
            clearChatContainer();
            loadChatHistory();
        })
        .catch(error => console.error('Error creating new conversation:', error));
}

function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    if (message) {
        displayMessage(message, 'user');
        userInput.value = '';
        autoResizeTextarea.call(userInput);

        fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: message,
                format: 'default',
                conversation_id: currentConversationId
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.answer) {
                displayMessage(data.answer, 'bot', data.interaction_id);
            } else {
                console.error('No answer in response');
                displayMessage('Sorry, I couldn\'t generate an answer.', 'bot');
            }
            currentConversationId = data.conversation_id;
            loadChatHistory();
        })
        .catch(error => {
            console.error('Error:', error);
            displayMessage('Sorry, there was an error processing your request. Please try again.', 'bot');
        });
    }
}

function displayMessage(message, sender, interactionId = null) {
    const chatContainer = document.getElementById('chat-container');
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
    
    const icon = document.createElement('img');
    icon.src = sender === 'user' ? '/static/default-user-avatar.png' : '/static/dmu.jpeg';
    icon.alt = sender === 'user' ? 'User Avatar' : 'DMU Logo';
    icon.className = 'message-icon';
    
    const content = document.createElement('p');
    content.textContent = message;
    
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

function createFeedbackButtons(interactionId) {
    const feedbackButtons = document.createElement('div');
    feedbackButtons.classList.add('feedback-buttons', 'mt-2');
    feedbackButtons.innerHTML = `
        <button onclick="submitFeedback(${interactionId}, 1)" class="feedback-button bg-red-500 text-white">Poor</button>
        <button onclick="submitFeedback(${interactionId}, 3)" class="feedback-button bg-yellow-500 text-white">Okay</button>
        <button onclick="submitFeedback(${interactionId}, 5)" class="feedback-button bg-green-500 text-white">Good</button>
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