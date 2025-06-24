// Configuration
const CONFIG = {
    // Using a free AI API service (you'll need to get your own API key)
    API_URL: 'https://api.openai.com/v1/chat/completions', // Replace with free alternative
    API_KEY: 'your-api-key-here', // You'll need to replace this
    MAX_MESSAGES: 50,
    MAX_FILE_SIZE: 10 * 1024 * 1024 // 10MB
};

// Global variables
let chatHistory = [];
let isLoading = false;

// DOM elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const fileInput = document.getElementById('file-input');
const themeToggle = document.getElementById('theme-toggle');
const clearChat = document.getElementById('clear-chat');
const loading = document.getElementById('loading');

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    // Load chat history
    loadChatHistory();

    // Event listeners
    sendBtn.addEventListener('click', handleSendMessage);
    userInput.addEventListener('keypress', handleKeyPress);
    userInput.addEventListener('input', autoResize);
    fileInput.addEventListener('change', handleFileUpload);
    themeToggle.addEventListener('click', toggleTheme);
    clearChat.addEventListener('click', clearChatHistory);

    // Show API key setup message if not configured
    if (CONFIG.API_KEY === 'your-api-key-here') {
        showSetupMessage();
    }
}

function showSetupMessage() {
    const setupMessage = {
        type: 'ai',
        content: `
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 10px; padding: 15px; margin: 10px 0;">
                <h4 style="color: #856404; margin: 0 0 10px 0;">🔧 Setup Required</h4>
                <p style="color: #856404; margin: 0 0 10px 0;">To use this AI chat, you need to:</p>
                <ol style="color: #856404; margin: 0; padding-left: 20px;">
                    <li>Get a free API key from <a href="https://platform.openai.com" target="_blank">OpenAI</a> or use alternatives like:</li>
                    <ul style="margin: 5px 0;">
                        <li><a href="https://huggingface.co/inference-api" target="_blank">Hugging Face Inference API</a> (Free)</li>
                        <li><a href="https://cohere.ai" target="_blank">Cohere API</a> (Free tier)</li>
                        <li><a href="https://www.anthropic.com" target="_blank">Anthropic Claude</a></li>
                    </ul>
                    <li>Replace the API_KEY in script.js with your key</li>
                    <li>Update the API_URL if using a different service</li>
                </ol>
                <p style="color: #856404; margin: 10px 0 0 0;"><strong>For now, you can try the demo mode below!</strong></p>
            </div>
        `,
        timestamp: new Date()
    };
    
    addMessageToChat(setupMessage);
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSendMessage();
    }
}

function autoResize() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
}

async function handleSendMessage() {
    const message = userInput.value.trim();
    if (!message || isLoading) return;

    // Add user message
    const userMessage = {
        type: 'user',
        content: message,
        timestamp: new Date()
    };
    
    addMessageToChat(userMessage);
    chatHistory.push(userMessage);
    
    // Clear input
    userInput.value = '';
    autoResize();
    
    // Show loading
    showLoading(true);
    
    try {
        // Get AI response
        const aiResponse = await getAIResponse(message);
        
        const aiMessage = {
            type: 'ai',
            content: aiResponse,
            timestamp: new Date()
        };
        
        addMessageToChat(aiMessage);
        chatHistory.push(aiMessage);
        
    } catch (error) {
        console.error('Error getting AI response:', error);
        
        const errorMessage = {
            type: 'ai',
            content: 'Sorry, I encountered an error. Please check your API configuration or try again later.',
            timestamp: new Date()
        };
        
        addMessageToChat(errorMessage);
    }
    
    showLoading(false);
    saveChatHistory();
}

async function getAIResponse(message) {
    // Demo responses for when API is not configured
    if (CONFIG.API_KEY === 'your-api-key-here') {
        return getDemoResponse(message);
    }

    // Real API call (when properly configured)
    const response = await fetch(CONFIG.API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${CONFIG.API_KEY}`
        },
        body: JSON.stringify({
            model: 'gpt-3.5-turbo',
            messages: [
                {
                    role: 'system',
                    content: 'You are Link AI, a helpful AI assistant. Be concise, friendly, and helpful.'
                },
                {
                    role: 'user',
                    content: message
                }
            ],
            max_tokens: 500,
            temperature: 0.7
        })
    });

    if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
    }

    const data = await response.json();
    return data.choices[0].message.content;
}

function getDemoResponse(message) {
    // Demo responses for testing
    const demoResponses = [
        "This is a demo response! To get real AI responses, please configure your API key in the script.js file.",
        "I'm currently in demo mode. Here are some free AI API options you can use:\n\n• Hugging Face Inference API\n• Cohere API (free tier)\n• OpenAI API\n• Anthropic Claude",
        "Demo mode: I can help you with various tasks once you set up a real AI API. Check the setup instructions above!",
        "In demo mode, I can't provide real AI responses. Please configure your API key to unlock full functionality.",
        "This is a placeholder response. Connect a real AI API to get intelligent responses to your questions!"
    ];
    
    return new Promise((resolve) => {
        setTimeout(() => {
            const randomResponse = demoResponses[Math.floor(Math.random() * demoResponses.length)];
            resolve(randomResponse);
        }, 1000 + Math.random() * 2000); // Simulate API delay
    });
}

function addMessageToChat(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.type}-message`;
    
    const iconClass = message.type === 'user' ? 'fas fa-user' : 'fas fa-robot';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <i class="${iconClass} message-icon"></i>
            <div class="message-text">
                ${message.content}
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Limit chat history
    if (chatHistory.length > CONFIG.MAX_MESSAGES) {
        chatHistory = chatHistory.slice(-CONFIG.MAX_MESSAGES);
        const messages = chatMessages.querySelectorAll('.message');
        if (messages.length > CONFIG.MAX_MESSAGES) {
            messages[0].remove();
        }
    }
}

function handleFileUpload(event) {
    const files = Array.from(event.target.files);
    
    files.forEach(file => {
        if (file.size > CONFIG.MAX_FILE_SIZE) {
            alert(`File ${file.name} is too large. Maximum size is 10MB.`);
            return;
        }
        
        const fileMessage = {
            type: 'user',
            content: `📎 Uploaded file: ${file.name} (${formatFileSize(file.size)})`,
            timestamp: new Date()
        };
        
        addMessageToChat(fileMessage);
        
        // Demo response for file upload
        setTimeout(() => {
            const response = {
                type: 'ai',
                content: `I can see you've uploaded "${file.name}". In demo mode, I can't actually analyze files. With a proper AI API setup, I could help you analyze images, documents, and other file types!`,
                timestamp: new Date()
            };
            addMessageToChat(response);
        }, 1000);
    });
    
    // Clear file input
    event.target.value = '';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = themeToggle.querySelector('i');
    icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

function clearChatHistory() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        chatHistory = [];
        chatMessages.innerHTML = '';
        localStorage.removeItem('chatHistory');
        
        // Re-add welcome message
        setTimeout(() => {
            const welcomeMessage = {
                type: 'ai',
                content: `
                    <h3>Welcome back to Link AI! 🚀</h3>
                    <p>Chat history cleared. How can I help you today?</p>
                `,
                timestamp: new Date()
            };
            addMessageToChat(welcomeMessage);
            
            if (CONFIG.API_KEY === 'your-api-key-here') {
                showSetupMessage();
            }
        }, 500);
    }
}

function showLoading(show) {
    isLoading = show;
    sendBtn.disabled = show;
    loading.classList.toggle('hidden', !show);
}

function saveChatHistory() {
    try {
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    } catch (error) {
        console.warn('Could not save chat history:', error);
    }
}

function loadChatHistory() {
    try {
        const saved = localStorage.getItem('chatHistory');
        if (saved) {
            chatHistory = JSON.parse(saved);
            
            // Clear the welcome message and reload history
            chatMessages.innerHTML = '';
            
            chatHistory.forEach(message => {
                addMessageToChat(message);
            });
        }
    } catch (error) {
        console.warn('Could not load chat history:', error);
        chatHistory = [];
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Service Worker for offline functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
} 