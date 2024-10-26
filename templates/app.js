document.addEventListener("DOMContentLoaded", function () {
    function loadChats() {
        fetch('/getChats')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Ошибка сети');
                }
                return response.json();
            })
            .then(chats => {
                const chatList = document.getElementById('chat-list');
                chatList.innerHTML = '';

                chats.forEach(chat => {
                    const chatBlock = document.createElement('div');
                    chatBlock.className = 'p-4 border-b border-gray-700 flex justify-between cursor-pointer chat-item';
                    chatBlock.dataset.chatId = chat.chat_id;

                    chatBlock.innerHTML = `
                        <div>
                            <div class="flex items-center space-x-2">
                                <img alt="Profile" class="rounded-full" height="40" src="https://placehold.co/40x40/000/FFF" width="40">
                                <span>${chat.participant_name}</span>
                            </div>
                            <span class="text-gray-500 ml-12">${chat.last_message_text}</span>
                        </div>
                        <span class="text-gray-500">${formatDate(chat.last_message_time)}</span>
                    `;

                    chatBlock.addEventListener('click', function () {
                        openChat(chat.chat_id, chat.participant_name);
                    });

                    chatList.appendChild(chatBlock);
                });
            })
            .catch(error => {
                console.error('Ошибка при загрузке чатов:', error);
            });
    }

    function openChat(chatId, chatName) {
        fetch(`/chat/${chatId}`)
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка доступа к чату');
        }
        return response.json();
    })
    .then(data => {
        const chatWindow = document.getElementById('chat-window');
        chatWindow.classList.remove('hidden');

        chatWindow.innerHTML = `
            <div class="flex items-center justify-between p-4 border-b border-gray-700">
                <div class="flex items-center space-x-2">
                    <img alt="Profile" class="rounded-full" height="40" src="https://placehold.co/40x40/000/FFF" width="40" />
                    <span class="text-lg font-semibold">${chatName}</span>
                    <span class="text-gray-500 text-sm">${chatId}</span>
                </div>
            </div>
            <div class="flex-1 overflow-y-auto p-4" id="chat-messages">
                ${data.messages.length === 0 ? '' : ''}
            </div>
            <div class="p-4 border-t border-gray-700 flex items-center">
                <input type="text" placeholder="Type a message..." class="flex-1 bg-gray-700 text-white rounded-full px-4 py-2 focus:outline-none" id="message-input" />
                <button class="bg-blue-600 text-white rounded-full px-4 py-2 ml-2 hover:bg-blue-700" id="send-button">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        `;

        const chatMessagesContainer = document.getElementById('chat-messages');

        data.messages.forEach(message => {
            const messageElement = document.createElement('div');
            messageElement.className = message.sender_id === data.uid ? 'flex items-end justify-end mb-4' : 'flex items-start mb-4';
            messageElement.innerHTML = `
                <span class="${message.sender_id === data.uid ? 'bg-blue-600' : 'bg-gray-700'} text-white rounded-lg px-4 py-2">
                    ${message.text}
                    <span class="text-gray-500 text-xs ml-2">${formatDate(message.time)}</span>
                </span>
            `;
            chatMessagesContainer.appendChild(messageElement);
        });

        document.getElementById('send-button').addEventListener('click', () => {
            sendChatMessage();
        });

        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
        
        document.getElementById('message-input').addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                sendChatMessage();
            }
        });

        function sendChatMessage() {
            const messageInput = document.getElementById('message-input');
            const newMessage = messageInput.value.trim();
            if (newMessage) {
                sendMessage(chatId, newMessage);
                console.log('Новое сообщение:', newMessage);
                messageInput.value = '';
            }
        }
        
        function sendMessage(chatId, message) {
            if (socket && socket.readyState === WebSocket.OPEN) {
                const messageData = {
                    chat_id: chatId,
                    content: message,
                    
                };
                socket.send(JSON.stringify(messageData));
            }
        }
    })
    .catch(error => {
        console.error('Ошибка при открытии чата:', error);
    });
    }

    loadChats();
    connectWebSocket();
});

let socket;

function connectWebSocket() {

    socket = new WebSocket("/ws");

    socket.onopen = () => {
        console.log('Connected to WebSocket');
    };

    socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        displayMessage(message);
    };

    socket.onclose = () => {
        console.log('Disconnected from WebSocket');
    };

    socket.onerror = (error) => {
        console.error('WebSocket Error: ', error);
    };
}

function displayMessage(message) {
    const chatMessagesContainer = document.getElementById('chat-messages');

    const messageElement = document.createElement('div');
    messageElement.className = message.isMyMessage ? 'flex items-end justify-end mb-4' : 'flex items-start mb-4';
    messageElement.innerHTML = `
        <span class="${message.sender_id === message.isMyMessage ? 'bg-blue-600' : 'bg-gray-700'} text-white rounded-lg px-4 py-2">
            ${message.content}
            <span class="text-gray-500 text-xs ml-2">${formatDate(message.time)}</span>
        </span>
    `;
    chatMessagesContainer.appendChild(messageElement);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const day = String(date.getUTCDate()).padStart(2, '0');
    const month = String(date.getUTCMonth() + 1).padStart(2, '0');
    const year = date.getUTCFullYear();
    const hours = String(date.getUTCHours()).padStart(2, '0');
    const minutes = String(date.getUTCMinutes()).padStart(2, '0');
    return `${day}-${month}-${year} ${hours}:${minutes}`;
}