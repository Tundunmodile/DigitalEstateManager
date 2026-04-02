/**
 * Apex Residences Chatbot - Frontend Script
 * Handles chat interaction, API calls, and UI updates
 */

class ApexChatbot {
    constructor() {
        this.messageContainer = document.getElementById('chatMessages');
        this.form = document.getElementById('chatForm');
        this.input = document.getElementById('messageInput');
        this.sendBtn = this.form.querySelector('.send-btn');
        this.clearBtn = document.getElementById('clearBtn');
        this.isWaitingForResponse = false;

        this.init();
    }

    init() {
        // Event listeners
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        this.clearBtn.addEventListener('click', () => this.clearConversation());

        // Welcome message
        this.addWelcomeMessage();

        // Focus on input
        this.input.focus();
    }

    addWelcomeMessage() {
        const welcomeHtml = `
            <div class="message bot">
                <div class="message-content">
                    <strong>Welcome to Apex Residences Concierge</strong>
                    <p style="margin-top: 0.5rem; font-size: 0.95rem; color: #cccccc;">
                        Good day. I'm here to answer your questions about our premium home management services,
                        discuss our offerings, or help with any inquiries you may have. How may I assist you?
                    </p>
                </div>
            </div>
        `;
        this.messageContainer.innerHTML += welcomeHtml;
        this.scrollToBottom();
    }

    async handleSubmit(e) {
        e.preventDefault();

        const message = this.input.value.trim();

        if (!message) {
            return;
        }

        if (this.isWaitingForResponse) {
            return;
        }

        // Add user message to UI
        this.addMessage(message, 'user');

        // Clear input
        this.input.value = '';
        this.input.focus();

        // Show loading indicator
        this.showLoadingIndicator();
        this.isWaitingForResponse = true;
        this.sendBtn.disabled = true;

        try {
            // Send to API
            const response = await this.sendMessage(message);

            // Remove loading indicator
            this.removeLoadingIndicator();

            // Add chatbot response
            this.addMessage(response.response, 'bot', response.source);
        } catch (error) {
            // Remove loading indicator
            this.removeLoadingIndicator();

            // Show error message
            const errorMsg = error.message || 'An error occurred. Please try again.';
            this.addMessage(errorMsg, 'bot', 'error');
        } finally {
            this.isWaitingForResponse = false;
            this.sendBtn.disabled = false;
            this.input.focus();
        }
    }

    async sendMessage(message) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                include_source: true,
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP Error: ${response.status}`);
        }

        return response.json();
    }

    addMessage(text, role, source = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Basic markdown support (links, bold, italic)
        const formattedText = this.formatText(text);
        contentDiv.innerHTML = formattedText;

        messageDiv.appendChild(contentDiv);

        // Add source badge if bot message with source
        if (role === 'bot' && source && source !== 'error') {
            const sourceDiv = document.createElement('div');
            sourceDiv.className = `message-source ${source}`;
            
            if (source === 'company') {
                sourceDiv.innerHTML = '<span class="source-icon"></span> Company Knowledge';
            } else if (source === 'web') {
                sourceDiv.innerHTML = '<span class="source-icon"></span> Web Search';
            }
            
            messageDiv.appendChild(sourceDiv);
        }

        this.messageContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatText(text) {
        // Escape HTML
        let formatted = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');

        // Convert URLs to links
        formatted = formatted.replace(
            /\[([^\]]+)\]\(([^)]+)\)/g,
            '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
        );

        // Bold text - **text** pattern
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // Italic text - *text* or _text_ pattern (but not inside bold)
        formatted = formatted.replace(/(?<!\*)\*([^*]+)\*(?!\*)(?<!\*)/g, '<em>$1</em>');
        formatted = formatted.replace(/_([^_]+)_/g, '<em>$1</em>');

        // Line breaks
        formatted = formatted.replace(/\n/g, '<br>');

        return formatted;
    }

    showLoadingIndicator() {
        const loadingHtml = `
            <div class="message loading bot">
                <div class="message-content">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        this.messageContainer.innerHTML += loadingHtml;
        this.scrollToBottom();
    }

    removeLoadingIndicator() {
        const loadingMessage = this.messageContainer.querySelector('.message.loading');
        if (loadingMessage) {
            loadingMessage.remove();
        }
    }

    async clearConversation() {
        if (!confirm('Are you sure you want to clear the conversation history?')) {
            return;
        }

        try {
            const response = await fetch('/api/history', {
                method: 'DELETE',
            });

            if (!response.ok) {
                throw new Error(`Failed to clear history: ${response.status}`);
            }

            // Clear UI
            this.messageContainer.innerHTML = '';
            this.addWelcomeMessage();
            this.input.focus();
        } catch (error) {
            alert('Error clearing conversation: ' + error.message);
        }
    }

    scrollToBottom() {
        // Use setTimeout to ensure DOM is updated
        setTimeout(() => {
            this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
        }, 0);
    }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatbot = new ApexChatbot();
});
