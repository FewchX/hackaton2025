document.addEventListener('DOMContentLoaded', () => {
    const N8N_WEBHOOK_URL = window.N8N_WEBHOOK_URL || 'https://yevheniibilozor.app.n8n.cloud/webhook/anka-wake-word';

    const chatHistory = document.getElementById('chat-history');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const toggleBtn = document.getElementById('toggle-btn');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    let isVoiceRunning = false;
    let typingIndicatorElement = null;

    // Connect to SSE for voice events
    const eventSource = new EventSource('/events');

    eventSource.onopen = function () {
        console.log('SSE connection opened');
    };

    eventSource.onerror = function (error) {
        console.error('SSE connection error:', error);
    };

    eventSource.onmessage = function (event) {
        if (event.data === ': keepalive') return;

        try {
            const data = JSON.parse(event.data);
            handleVoiceEvent(data);
        } catch (e) {
            console.error('Failed to parse event data:', e);
        }
    };

    function handleVoiceEvent(data) {
        switch (data.type) {
            case 'connected':
                console.log('Voice stream connected');
                break;

            case 'log':
                console.log(`[${data.level}] ${data.message}`);
                if (data.level === 'success' && data.message.includes('Wake word detected')) {
                    displayMessage('Wake word detected...', 'system');
                }
                break;

            case 'status':
                updateStatus(data.status);
                break;

            case 'transcription':
                displayMessage(data.text, 'user');
                break;

            case 'response':
                displayMessage(data.text, 'bot');
                break;
        }
    }

    function updateStatus(status) {
        statusIndicator.className = 'status-indicator';

        switch (status) {
            case 'listening_wake':
                statusText.textContent = 'Listening for wake word...';
                statusIndicator.classList.add('status-active');
                break;
            case 'listening_question':
                statusText.textContent = 'Listening for question...';
                statusIndicator.classList.add('status-listening');
                break;
            case 'processing':
                statusText.textContent = 'Thinking...';
                statusIndicator.classList.add('status-processing');
                break;
            default:
                statusText.textContent = isVoiceRunning ? 'Voice Active' : 'Idle';
        }
    }

    // Welcome message
    const welcomeMessage = `Hello! I'm your voice assistant. You can:
                           <br>• Type your question below
                           <br>• Click "Voice" and say "Anka" to use voice mode
                           <br><br>How can I help you?`;
    displayMessage(welcomeMessage, 'bot');

    // Text input handlers
    sendButton.addEventListener('click', sendTextMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendTextMessage();
        }
    });

    // Voice toggle
    toggleBtn.addEventListener('click', async () => {
        if (isVoiceRunning) {
            await fetch('/api/stop', { method: 'POST' });
            toggleBtn.innerHTML = '<span class="icon">▶</span> Voice';
            toggleBtn.classList.remove('danger');
            toggleBtn.classList.add('voice-btn');
            statusText.textContent = 'Idle';
            statusIndicator.className = 'status-indicator';
            displayMessage('Voice assistant stopped.', 'system');
        } else {
            await fetch('/api/start', { method: 'POST' });
            toggleBtn.innerHTML = '<span class="icon">⏹</span> Stop';
            toggleBtn.classList.remove('voice-btn');
            toggleBtn.classList.add('danger');
            displayMessage('Voice assistant started. Say "Anka" to begin.', 'system');
        }
        isVoiceRunning = !isVoiceRunning;
    });

    async function sendTextMessage() {
        const questionText = messageInput.value.trim();
        if (questionText === '') {
            return;
        }

        displayMessage(questionText, 'user');
        messageInput.value = '';

        sendButton.disabled = true;
        sendButton.classList.add('loading');

        showTypingIndicator();

        try {
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question: questionText })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Response will come through SSE events, not direct response
            console.log('Question sent successfully');

        } catch (error) {
            console.error('Error sending question:', error);
            displayMessage('Error sending request. Please try again.', 'bot');
        } finally {
            hideTypingIndicator();
            sendButton.disabled = false;
            sendButton.classList.remove('loading');
            messageInput.focus();
        }
    }

    function showTypingIndicator() {
        typingIndicatorElement = document.createElement('div');
        typingIndicatorElement.classList.add('message', 'bot-message', 'typing-message');

        const textSpan = document.createElement('span');
        textSpan.classList.add('typing-text');

        const workingTexts = [
            'Analyzing your question...',
            'Searching for information...',
            'Processing data...',
            'Preparing answer...',
            'Thinking...'
        ];

        const jokes = [
            'Why did the AI go to school? To improve its learning model!',
            'Processing... faster than a human, I promise!',
            'Converting to binary... just kidding!',
            'Consulting my neural nets...',
            'Tea break for my circuits... kidding!'
        ];

        let currentIndex = 0;
        let isJoke = Math.random() < 0.2;
        const texts = isJoke ? jokes : workingTexts;

        textSpan.textContent = texts[currentIndex];

        const interval = setInterval(() => {
            currentIndex = (currentIndex + 1) % texts.length;
            textSpan.textContent = texts[currentIndex];
        }, 1800);

        typingIndicatorElement.typing_interval = interval;
        typingIndicatorElement.appendChild(textSpan);

        chatHistory.appendChild(typingIndicatorElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function hideTypingIndicator() {
        if (typingIndicatorElement) {
            if (typingIndicatorElement.typing_interval) {
                clearInterval(typingIndicatorElement.typing_interval);
            }
            typingIndicatorElement.remove();
            typingIndicatorElement = null;
        }
    }

    function displayMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');

        if (sender === 'user') {
            messageDiv.classList.add('user-message');
        } else if (sender === 'system') {
            messageDiv.classList.add('system-message');
        } else {
            messageDiv.classList.add('bot-message');
        }

        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;

        // Typing animation
        const typingSpeed = 5;
        let index = 0;

        function typeNextChar() {
            if (index < text.length) {
                const remainingText = text.substring(index);
                const brTag = '<br>';

                if (remainingText.startsWith(brTag)) {
                    messageDiv.innerHTML += brTag;
                    index += brTag.length;
                } else {
                    messageDiv.innerHTML += text.charAt(index);
                    index++;
                }

                chatHistory.scrollTop = chatHistory.scrollHeight;
                setTimeout(typeNextChar, typingSpeed);
            }
        }

        typeNextChar();
    }
});
