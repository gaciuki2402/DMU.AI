let currentConversationId = null;
let conversations = [];

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded and parsed');
    initializeEventListeners();
    loadInitialChatHistory();
});

function initializeEventListeners() {
    const sendButton = document.getElementById('send-button');
    const userInput = document.getElementById('user-input');
    const newChatButton = document.getElementById('new-chat-btn');

    if (sendButton) {
        sendButton.addEventListener('click', handleSendMessage);
    } else {
        console.error('Send button not found');
    }

    if (userInput) {
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleSendMessage();
            }
        });
    } else {
        console.error('User input field not found');
    }

    if (newChatButton) {
        newChatButton.addEventListener('click', startNewChat);
    } else {
        console.error('New chat button not found');
    }
}

function handleSendMessage() {
    console.log('Send message triggered');
    const userInput = document.getElementById('user-input');
    const formatSelect = document.getElementById('format-select');
    const message = userInput.value.trim();
    const format = formatSelect.value;

    if (message) {
        if (!currentConversationId) {
            startNewChat().then(() => sendMessageToServer(message, format));
        } else {
            sendMessageToServer(message, format);
        }
        userInput.value = '';
    }
}

function sendMessageToServer(message, format) {
    displayMessage(message, 'user');
    fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            question: message, 
            format: format,
            conversation_id: currentConversationId 
        }),
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        displayMessage(data.answer, 'bot', data.interaction_id);
        updateConversationPreview(currentConversationId, message);
    })
    .catch(error => {
        console.error('Error:', error);
        displayMessage('Sorry, there was an error processing your request. Please try again.', 'bot');
    });
}

function startNewChat() {
    return fetch('/conversation/new', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            currentConversationId = data.conversation_id;
            conversations.unshift({ id: data.conversation_id, title: data.title });
            updateChatHistoryList();
            clearChatContainer();
        })
        .catch(error => console.error('Error creating new conversation:', error));
}

function loadInitialChatHistory() {
    fetch('/chat_history')
        .then(response => response.json())
        .then(data => {
            conversations = data.conversations;
            updateChatHistoryList();
            if (conversations.length === 0) {
                startNewChat();
            } else {
                loadChat(conversations[0].id);
            }
        })
        .catch(error => console.error('Error loading chat history:', error));
}

function updateChatHistoryList() {
    const chatHistoryList = document.getElementById('chat-history-list');
    if (!chatHistoryList) {
        console.error('Chat history list element not found');
        return;
    }
    chatHistoryList.innerHTML = '';
    conversations.forEach(conv => {
        const li = document.createElement('li');
        li.className = 'chat-history-item';
        li.textContent = conv.title;
        li.onclick = () => loadChat(conv.id);
        if (conv.id === currentConversationId) {
            li.classList.add('active');
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
                displayMessage(msg.content, msg.sender, msg.interaction_id);
            });
            updateChatHistoryList();
        })
        .catch(error => console.error('Error loading chat:', error));
}

function clearChatContainer() {
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
        chatContainer.innerHTML = '';
    } else {
        console.error('Chat container not found');
    }
}

function displayMessage(message, sender, interactionId = null) {
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) {
        console.error('Chat container not found');
        return;
    }
    const messageElement = document.createElement('div');
    messageElement.classList.add('p-4', 'rounded-lg', 'max-w-3xl', 'mx-auto', 'mb-4');
    
    if (sender === 'user' || sender === 'Human') {
        messageElement.classList.add('bg-gray-100');
        messageElement.innerText = message;
    } else {
        messageElement.classList.add('bg-white', 'border', 'border-gray-200');
        messageElement.innerText = message;
        if (interactionId) {
            const feedbackButtons = createFeedbackButtons(interactionId);
            messageElement.appendChild(feedbackButtons);
        }
    }
    
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function createFeedbackButtons(interactionId) {
    const feedbackButtons = document.createElement('div');
    feedbackButtons.classList.add('mt-2');
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

function updateConversationPreview(conversationId, message) {
    const index = conversations.findIndex(conv => conv.id === conversationId);
    if (index !== -1) {
        conversations[index].title = message.substring(0, 30) + (message.length > 30 ? '...' : '');
        conversations.unshift(conversations.splice(index, 1)[0]);
        updateChatHistoryList();
    }
}