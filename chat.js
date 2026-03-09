/* ========================================
   RONDEAU & CO. — RAG Chat Widget
   Connects to FastAPI /ask endpoint with SSE streaming
   ======================================== */

document.addEventListener('DOMContentLoaded', () => {

    /** @type {string} Backend API base URL */
    const API_BASE = 'http://127.0.0.1:8000';

    /** @type {HTMLElement} Main widget container */
    const widget = document.getElementById('chat-widget');
    /** @type {HTMLButtonElement} Floating toggle button */
    const toggleBtn = document.getElementById('chat-toggle');
    /** @type {HTMLButtonElement} Header close button */
    const closeBtn = document.getElementById('chat-close');
    /** @type {HTMLElement} Messages container */
    const messagesContainer = document.getElementById('chat-messages');
    /** @type {HTMLElement} Typing indicator */
    const typingIndicator = document.getElementById('chat-typing');
    /** @type {HTMLFormElement} Input form */
    const inputForm = document.getElementById('chat-input-form');
    /** @type {HTMLInputElement} Text input */
    const inputField = document.getElementById('chat-input');
    /** @type {HTMLButtonElement} Send button */
    const sendBtn = document.getElementById('chat-send-btn');

    /** @type {Array<{role: string, content: string}>} Conversation history */
    let chatHistory = [];
    /** @type {boolean} Whether a request is in-flight */
    let isStreaming = false;

    /**
     * Toggle the chat panel open/closed.
     */
    function toggleChat() {
        const isOpen = widget.classList.toggle('open');
        toggleBtn.setAttribute('aria-label', isOpen ? 'Close chat' : 'Open chat');
        if (isOpen) {
            inputField.focus();
            scrollToBottom();
        }
    }

    /**
     * Close the chat panel.
     */
    function closeChat() {
        widget.classList.remove('open');
        toggleBtn.setAttribute('aria-label', 'Open chat');
    }

    /**
     * Scroll messages container to the bottom.
     */
    function scrollToBottom() {
        requestAnimationFrame(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });
    }

    /**
     * Show or hide the typing indicator.
     * @param {boolean} visible - Whether to show the indicator
     */
    function setTypingVisible(visible) {
        typingIndicator.style.display = visible ? 'block' : 'none';
        if (visible) {
            scrollToBottom();
        }
    }

    /**
     * Create and append a message bubble to the chat.
     * @param {string} role - 'user' or 'assistant'
     * @param {string} text - The message content
     * @returns {HTMLElement} The bubble's inner paragraph element
     */
    function addMessage(role, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-msg chat-msg-${role}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'chat-msg-bubble';

        const paragraph = document.createElement('p');
        paragraph.textContent = text;

        bubbleDiv.appendChild(paragraph);
        msgDiv.appendChild(bubbleDiv);
        messagesContainer.appendChild(msgDiv);
        scrollToBottom();

        return bubbleDiv;
    }

    /**
     * Append source citation tags to an assistant message bubble.
     * @param {HTMLElement} bubbleEl - The bubble element
     * @param {string[]} sources - Array of source filenames
     */
    function addSources(bubbleEl, sources) {
        if (!sources || sources.length === 0) return;

        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'chat-sources';

        sources.forEach((source) => {
            const tag = document.createElement('span');
            tag.className = 'chat-source-tag';
            // Extract just the filename from full path
            const filename = source.split(/[\\/]/).pop() || source;
            tag.textContent = filename;
            sourcesDiv.appendChild(tag);
        });

        bubbleEl.appendChild(sourcesDiv);
        scrollToBottom();
    }

    /**
     * Toggle the disabled state of input controls.
     * @param {boolean} disabled - Whether to disable the controls
     */
    function setInputDisabled(disabled) {
        inputField.disabled = disabled;
        sendBtn.disabled = disabled;
        isStreaming = disabled;
    }

    /**
     * Send a user question to the /ask endpoint and stream the response.
     * @param {string} question - The user's question
     */
    async function sendMessage(question) {
        // Add user message to UI and history
        addMessage('user', question);
        chatHistory.push({ role: 'user', content: question });

        setInputDisabled(true);
        setTypingVisible(true);

        /** @type {HTMLElement|null} The assistant bubble being streamed into */
        let assistantBubble = null;
        /** @type {HTMLElement|null} The paragraph element for token streaming */
        let assistantParagraph = null;
        /** @type {string} Accumulated response text */
        let fullResponse = '';
        /** @type {string[]} Retrieved sources */
        let sources = [];

        try {
            const response = await fetch(`${API_BASE}/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    history: chatHistory.slice(0, -1), // Send history before current message
                }),
            });

            if (!response.ok) {
                if (response.status === 429) {
                    throw new Error('Too many requests. Please wait a minute and try again.');
                }
                if (response.status === 400) {
                    const data = await response.json();
                    throw new Error(data.detail || 'Invalid input.');
                }
                throw new Error(`Server returned ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                // Keep the last potentially incomplete line in the buffer
                buffer = lines.pop() || '';

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed.startsWith('data: ')) continue;

                    try {
                        const payload = JSON.parse(trimmed.slice(6));

                        if (payload.type === 'sources') {
                            sources = payload.sources || [];
                        }

                        if (payload.type === 'token') {
                            // Create the assistant bubble on first token
                            if (!assistantBubble) {
                                setTypingVisible(false);
                                assistantBubble = addMessage('assistant', '');
                                assistantParagraph = assistantBubble.querySelector('p');
                            }
                            fullResponse += payload.token;
                            assistantParagraph.textContent = fullResponse;
                            scrollToBottom();
                        }

                        if (payload.type === 'done') {
                            // Append sources if present
                            if (assistantBubble && sources.length > 0) {
                                addSources(assistantBubble, sources);
                            }
                        }
                    } catch (parseError) {
                        // Skip malformed SSE lines silently
                    }
                }
            }

            // Add assistant response to history
            if (fullResponse) {
                chatHistory.push({ role: 'assistant', content: fullResponse });
            }

        } catch (error) {
            setTypingVisible(false);
            const errorBubble = addMessage('assistant', '');
            const errorText = errorBubble.querySelector('p');
            errorText.textContent = 'I apologize, but I\'m having trouble connecting right now. Please try again in a moment.';
            errorText.style.fontStyle = 'italic';
        } finally {
            setTypingVisible(false);
            setInputDisabled(false);
            inputField.focus();
        }
    }

    // --- Event Listeners ---

    toggleBtn.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', closeChat);

    inputForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const question = inputField.value.trim();
        if (!question || isStreaming) return;

        // CLIENT-SIDE VALIDATION
        if (question.length > 500) {
            addMessage('assistant', 'Please keep your question under 500 characters.');
            return;
        }

        inputField.value = '';
        sendMessage(question);
    });

    // Close on Escape key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && widget.classList.contains('open')) {
            closeChat();
        }
    });

    // Register chat elements with the cursor hover system
    const cursorRing = document.querySelector('.cursor-ring');
    if (cursorRing) {
        const chatInteractives = widget.querySelectorAll('a, button, input, textarea');
        chatInteractives.forEach((el) => {
            el.addEventListener('mouseenter', () => cursorRing.classList.add('hover'));
            el.addEventListener('mouseleave', () => cursorRing.classList.remove('hover'));
        });
    }
});
