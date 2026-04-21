if (window.lucide) window.lucide.createIcons();

const modelSelect = document.getElementById('modelSelect');
const creativityRange = document.getElementById('creativityRange');
const responseDepth = document.getElementById('responseDepth');
const chatHistory = document.getElementById('chatHistory');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const clearChatBtn = document.getElementById('clearChat');
const themeToggle = document.getElementById('themeToggle');
const currentModelName = document.getElementById('currentModelName');

// Session Identification
let sessionId = localStorage.getItem('gourmet_session_id') || 'session-' + Date.now();
localStorage.setItem('gourmet_session_id', sessionId);

let chatUIHistory = JSON.parse(localStorage.getItem('gourmet_chat_history_ui')) || [];

modelSelect.addEventListener('change', () => {
    currentModelName.textContent = modelSelect.options[modelSelect.selectedIndex].text.split(' (')[0];
});

// Theme Logic
function updateThemeUI() {
    const isLight = document.body.classList.contains('light-theme');
    themeToggle.innerHTML = `<i data-lucide="${isLight ? 'moon' : 'sun'}"></i>`;
    if (window.lucide) window.lucide.createIcons();
}

if (localStorage.getItem('gourmet_theme') === 'light') {
    document.body.classList.add('light-theme');
}
updateThemeUI();

themeToggle.addEventListener('click', (e) => {
    e.preventDefault();
    document.body.classList.toggle('light-theme');
    localStorage.setItem('gourmet_theme', document.body.classList.contains('light-theme') ? 'light' : 'dark');
    updateThemeUI();
});

// Clear Session
clearChatBtn.addEventListener('click', async () => {
    await fetch('/api/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId })
    });
    chatUIHistory = [];
    localStorage.removeItem('gourmet_chat_history_ui');
    renderInitialState();
});

function renderInitialState() {
    chatHistory.innerHTML = `
        <div class="message-wrapper assistant">
            <div class="message">
                <strong>Bonjour!</strong> I am your Executive Chef Assistant, now backed by a <strong>LangChain Server</strong>. Tell me what's in your pantry!
            </div>
        </div>
    `;
}

function loadHistoryUI() {
    if (chatUIHistory.length > 0) {
        chatHistory.innerHTML = '';
        chatUIHistory.forEach(msg => addMessage(msg.content, msg.role));
    } else {
        renderInitialState();
    }
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    userInput.value = '';
    
    const thinkingId = 'thinking-' + Date.now();
    addMessage('<i>Chef is consulting the secret archives...</i>', 'assistant', thinkingId);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                input: text,
                sessionId: sessionId,
                config: {
                    model: modelSelect.value,
                    temperature: parseFloat(creativityRange.value),
                    depth: responseDepth.value
                }
            })
        });

        const data = await response.json();
        const thinkingElement = document.getElementById(thinkingId);
        if (thinkingElement) thinkingElement.parentElement.remove();

        if (data.error) {
            addMessage(`Chef Error: ${data.error}`, 'assistant');
        } else {
            addMessage(data.reply, 'assistant');
            
            chatUIHistory.push({ role: 'user', content: text }, { role: 'assistant', content: data.reply });
            if (chatUIHistory.length > 30) chatUIHistory.splice(0, 2);
            localStorage.setItem('gourmet_chat_history_ui', JSON.stringify(chatUIHistory));
        }
    } catch (error) {
        const thinkingElement = document.getElementById(thinkingId);
        if (thinkingElement) thinkingElement.parentElement.remove();
        addMessage(`Network Error: ${error.message}. Is the server running?`, 'assistant');
    }
}

function addMessage(text, role, id = null) {
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper ${role}`;
    
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message';
    if (id) msgDiv.id = id;
    
    const formattedText = text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    msgDiv.innerHTML = formattedText;
    wrapper.appendChild(msgDiv);
    chatHistory.appendChild(wrapper);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });

loadHistoryUI();
userInput.focus();
