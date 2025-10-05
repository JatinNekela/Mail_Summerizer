const fetchBtn = document.getElementById('fetch-btn');
const emailListDiv = document.getElementById('email-list');
const emailLoader = document.getElementById('email-loader');
const modelSelect = document.getElementById('model-select');
const chatContainer = document.getElementById('chat-container');

const BACKEND_URL = 'http://localhost:5000';
let currentEmailId = null;
let conversationHistory = [];

// --- Event Listener for Fetching Emails ---
fetchBtn.addEventListener('click', async () => {
    emailListDiv.innerHTML = '';
    emailLoader.style.display = 'block';

    try {
        const response = await fetch(`${BACKEND_URL}/api/summarize-emails`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: modelSelect.value })
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const emails = await response.json();

        if (emails.error) throw new Error(emails.error);

        emails.forEach(email => {
            const emailCard = document.createElement('div');
            emailCard.className = 'email-card';
            emailCard.dataset.emailId = email.id;
            emailCard.dataset.emailSubject = email.subject || 'No Subject';

            emailCard.innerHTML = `
                <h3>${email.subject || 'No Subject'}</h3>
                <p><strong>From:</strong> ${email.from || 'Unknown Sender'}</p>
                <p class="summary">${email.summary || 'No summary available.'}</p>
            `;
            emailCard.addEventListener('click', () => {
                handleEmailSelect(email.id, email.subject || 'No Subject');
                // Highlight active email
                document.querySelectorAll('.email-card').forEach(c => c.classList.remove('active'));
                emailCard.classList.add('active');
            });
            emailListDiv.appendChild(emailCard);
        });

    } catch (error) {
        emailListDiv.innerHTML = `<p style="color: red; padding: 20px;"><strong>Error:</strong> ${error.message}</p>`;
    } finally {
        emailLoader.style.display = 'none';
    }
});

// --- Functions for Chat Interface ---
function handleEmailSelect(emailId, emailSubject) {
    currentEmailId = emailId;
    conversationHistory = [];
    
    chatContainer.innerHTML = `
        <div class="header">
            <h1>Chat: ${emailSubject}</h1>
        </div>
        <div class="chat-window" id="chat-window"></div>
        <div class="loader" id="chat-loader"></div>
        <div class="input-area">
            <input type="text" id="message-input" placeholder="Ask a question..." autocomplete="off">
            <button id="send-btn">Send</button>
        </div>
    `;

    const sendBtn = document.getElementById('send-btn');
    const messageInput = document.getElementById('message-input');

    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
}

async function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const userMessage = messageInput.value.trim();
    if (!userMessage || !currentEmailId) return;

    appendMessage(userMessage, 'user');
    messageInput.value = '';
    document.getElementById('chat-loader').style.display = 'block';

    try {
        const response = await fetch(`${BACKEND_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email_id: currentEmailId,
                question: userMessage,
                history: conversationHistory,
                model: modelSelect.value
            }),
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);
        
        const data = await response.json();
        appendMessage(data.answer, 'ai');

        conversationHistory.push({ "role": "user", "content": userMessage });
        conversationHistory.push({ "role": "assistant", "content": data.answer });

    } catch (error) {
        appendMessage(`Error: ${error.message}`, 'ai', true);
    } finally {
        document.getElementById('chat-loader').style.display = 'none';
    }
}

function appendMessage(text, sender, isError = false) {
    const chatWindow = document.getElementById('chat-window');
    if(!chatWindow) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender === 'user' ? 'user-msg' : 'ai-msg'}`;
    if (isError) messageDiv.style.color = 'red';
    
    messageDiv.textContent = text;
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

