document.addEventListener("DOMContentLoaded", function () {
    document.getElementById('settings-icon').addEventListener('click', () => {
        const submenu = document.getElementById('submenu');
        submenu.classList.toggle('hidden');
    });

    document.getElementById('new-chat-button').addEventListener('click', openModal);
    document.getElementById('close-modal').addEventListener('click', closeModal);
    document.getElementById('search-input').addEventListener('input', filterUsers);

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
                let activeChatBlock = null;

                chats.forEach(chat => {
                    const chatBlock = document.createElement('div');
                    chatBlock.className = 'p-4 border-b border-gray-700 flex justify-between cursor-pointer chat-item';
                    chatBlock.dataset.chatId = chat.chat_id;
                    const lastMessageText = chat.last_message_text || '';
                    const lastMessageTime = chat.last_message_time ? formatDate(chat.last_message_time) : '';
                    chatBlock.innerHTML = `
                        <div>
                            <div class="flex items-center space-x-2">
                                <img alt="Profile" class="rounded-full" height="40" src="https://placehold.co/40x40/000/FFF" width="40">
                                <span>${chat.participant_name}</span>
                            </div>
                            <span class="text-gray-500 ml-12">${lastMessageText}</span>
                        </div>
                        <span class="text-gray-500">${lastMessageTime}</span>
                    `;

                    chatBlock.addEventListener('click', function () {
                        if (activeChatBlock) {
                            activeChatBlock.classList.remove('bg-purple-600');
                            activeChatBlock.querySelectorAll('span').forEach(span => span.classList.replace('text-white-500', 'text-gray-500'));
                        }
    

                        chatBlock.classList.add('bg-purple-600');
                        chatBlock.querySelectorAll('span').forEach(span => span.classList.replace('text-gray-500', 'text-white-500'));
                        activeChatBlock = chatBlock;
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
            <div class="flex items-center justify-between p-4 border-b border-gray-700 bg-gray-800">
                <div class="flex items-center space-x-2">
                    <img alt="Profile" class="rounded-full" height="40" src="https://placehold.co/40x40/000/FFF" width="40" />
                    <span class="text-lg font-semibold">${chatName}</span>
                    <span class=" ${data.isOnline ? 'text-green-500' : 'text-red-500'}  text-sm">${data.isOnline ? 'Online' : 'Offline'}</span>
                </div>
            </div>
            <div class="flex-1 overflow-y-auto p-4" id="chat-messages">
                ${data.messages.length === 0 ? '' : ''}
            </div>
            <div class="p-4 border-t border-gray-700 flex items-center">
                <input type="text" placeholder="Type a message..." class="flex-1 bg-gray-700 text-white rounded-full px-4 py-2 focus:outline-none" id="message-input" />
                <button class="bg-purple-600 text-white rounded-full px-4 py-2 ml-2 hover:bg-purple-700" id="send-button">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        `;

        const chatMessagesContainer = document.getElementById('chat-messages');

        data.messages.forEach(message => {
            const messageElement = document.createElement('div');
            messageElement.className = message.sender_id === data.uid ? 'flex items-end justify-end mb-4' : 'flex items-start mb-4';
            messageElement.innerHTML = `
                <span class="${message.sender_id === data.uid ? 'bg-purple-600' : 'bg-gray-700'} text-white rounded-lg px-4 py-2">
                    ${message.text}
                    <span class="${message.sender_id === data.uid ? 'text-white-500' : 'text-gray-500'} text-xs ml-2">${formatDate(message.time)}</span>
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
        <span class="${message.isMyMessage ? 'bg-purple-600' : 'bg-gray-700'} text-white rounded-lg px-4 py-2">
            ${message.content}
            <span class="${message.isMyMessage ? 'text-white-500' : 'text-gray-500'} text-xs ml-2">${formatDate(message.time)}</span>
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


function openModal() {
    const modal = document.getElementById('user-modal');
    modal.classList.remove('hidden');
    fetchUsers();
}

async function fetchUsers() {
    try {
        const response = await fetch(`/getUsers`);
        const users = await response.json();
        console.log(users);
        const userList = document.getElementById('user-list');
        userList.innerHTML = '';

        users.forEach(user => {
            const userItem = document.createElement('div');
            userItem.classList.add('flex', 'items-center', 'justify-between', 'p-2', 'text-white');
            userItem.innerHTML = `
                <img src="" alt="${user.nickname}" class="w-8 h-8 rounded-full mr-2">
                <span>${user.nickname}</span>
                <button class="bg-purple-600 text-white rounded-full w-8 h-8 flex items-center justify-center">
                    <i class="fas fa-plus"></i>
                </button>
            `;
            const addButton = userItem.querySelector('button');
            addButton.addEventListener('click', () => {
                addChat(user.id);
            });
            userList.appendChild(userItem);
        });

    } catch (error) {
        console.error('Ошибка при получении пользователей:', error);
    }
}

function filterUsers() {
    const searchTerm = this.value.toLowerCase();
    const userItems = document.querySelectorAll('#user-list > div');

    userItems.forEach(item => {
        const nickname = item.querySelector('span').textContent.toLowerCase();
        
        item.style.display = nickname.includes(searchTerm) ? 'flex' : 'none';
    });
}


function closeModal() {
    const modal = document.getElementById('user-modal');
    modal.classList.add('hidden');
}

async function addChat(userId) {
    try {
        const response = await fetch('/addChat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: userId })
        });

        if (response.ok) {
            console.log('Чат успешно добавлен!');
            closeModal();
        } else {
            console.error('Ошибка при добавлении чата:', response.statusText);
        }
    } catch (error) {
        console.error('Ошибка при добавлении чата:', error);
    }
}


