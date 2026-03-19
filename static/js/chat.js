// chat.js — Real-time chat via Socket.IO
// Only initializes on the editor page where STORY_ID is defined.

let socket = null;

document.addEventListener('DOMContentLoaded', () => {
    if (typeof STORY_ID === 'undefined') return;

    socket = io();

    socket.on('connect', () => {
        socket.emit('join_story', { story_id: STORY_ID });
    });

    socket.on('new_message', (msg) => {
        const panel = document.getElementById('chat-panel');
        const isOpen = panel && panel.classList.contains('active');
        appendMessage(msg, msg.username === (typeof CURRENT_USER !== 'undefined' ? CURRENT_USER : ''));
        if (isOpen) {
            scrollChatToBottom();
        } else if (msg.username !== CURRENT_USER) {
            // Show unread dot
            const dot = document.getElementById('chat-unread-dot');
            if (dot) dot.classList.add('visible');
        }
    });

    socket.on('system_message', (data) => {
        appendSystemMessage(data.content);
    });

    // Allow Enter key to send
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    scrollChatToBottom();

    // Floating chat toggle logic
    const chatToggleBtn = document.getElementById('chat-toggle-btn');
    const chatPanel = document.getElementById('chat-panel');
    if (chatToggleBtn && chatPanel) {
        chatToggleBtn.addEventListener('click', () => {
            chatPanel.classList.toggle('active');
            // Clear unread indicator when opening
            const dot = document.getElementById('chat-unread-dot');
            if (chatPanel.classList.contains('active')) {
                if (dot) dot.classList.remove('visible');
                scrollChatToBottom();
                const input = document.getElementById('chat-input');
                if (input) input.focus();
            }
        });
        
        // Close chat when clicking outside
        document.addEventListener('click', (e) => {
            if (chatPanel.classList.contains('active') && !chatPanel.contains(e.target) && !chatToggleBtn.contains(e.target)) {
                chatPanel.classList.remove('active');
            }
        });
    }
});

function sendMessage() {
    const input = document.getElementById('chat-input');
    const content = input.value.trim();
    if (!content || !socket) return;

    socket.emit('send_message', { story_id: STORY_ID, content });
    input.value = '';
}

function appendMessage(msg, isMine) {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    const div = document.createElement('div');
    div.className = `chat-message${isMine ? ' chat-mine' : ''}`;
    div.innerHTML = `
        <span class="msg-author">${escapeHtmlChat(msg.username)}</span>
        <p class="msg-text">${escapeHtmlChat(msg.content)}</p>
        <span class="msg-time">${msg.created_at}</span>
    `;
    container.appendChild(div);
}

function appendSystemMessage(text) {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'system-message';
    div.textContent = text;
    container.appendChild(div);
    scrollChatToBottom();
}

function scrollChatToBottom() {
    const container = document.getElementById('chat-messages');
    if (container) container.scrollTop = container.scrollHeight;
}

function escapeHtmlChat(str) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
}
