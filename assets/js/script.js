// Configuration
const CONFIG = {
    // Your Railway backend URL
    API_URL: 'https://green-rainstorm-production.up.railway.app',
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

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    loadChatHistory();
    setupEventListeners();
    addWelcomeMessage();
});

// Theme management
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
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

// Event listeners
function setupEventListeners() {
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    themeToggle.addEventListener('click', toggleTheme);
    clearChat.addEventListener('click', clearChatHistory);
    fileInput.addEventListener('change', handleFileUpload);
    
    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

// Welcome message
function addWelcomeMessage() {
    if (chatHistory.length === 0) {
        const welcomeMsg = {
            type: 'ai',
            content: '👋 Welcome to Link AI! I\'m powered by Google\'s Gemini AI and ready to help you with:\n\n• 💬 **Natural conversations**\n• 📄 **File analysis** (upload documents, images, code)\n• 🧠 **Problem solving**\n• 💡 **Creative assistance**\n\nFeel free to ask me anything or upload a file to get started!',
            timestamp: new Date().toISOString()
        };
        displayMessage(welcomeMsg);
        chatHistory.push(welcomeMsg);
        saveChatHistory();
    }
}

// Message handling
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message || isLoading) return;
    
    // Add user message
    const userMsg = {
        type: 'user',
        content: message,
        timestamp: new Date().toISOString()
    };
    
    displayMessage(userMsg);
    chatHistory.push(userMsg);
    saveChatHistory();
    
    userInput.value = '';
    userInput.style.height = 'auto';
    setLoading(true);
    
    try {
        // Send to Railway backend
        const response = await fetch(`${CONFIG.API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                history: chatHistory.slice(-10) // Send last 10 messages for context
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        const aiMsg = {
            type: 'ai',
            content: data.response || 'Sorry, I couldn\'t process your request.',
            timestamp: new Date().toISOString()
        };
        
        displayMessage(aiMsg);
        chatHistory.push(aiMsg);
        saveChatHistory();
        
    } catch (error) {
        console.error('Error:', error);
        const errorMsg = {
            type: 'ai',
            content: '❌ Sorry, I\'m having trouble connecting to the server. Please try again later.\n\n**Troubleshooting:**\n• Check your internet connection\n• The backend service might be starting up (Railway cold starts can take a moment)\n• Try refreshing the page',
            timestamp: new Date().toISOString()
        };
        displayMessage(errorMsg);
        chatHistory.push(errorMsg);
        saveChatHistory();
    } finally {
        setLoading(false);
    }
}

// File upload handling
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (file.size > CONFIG.MAX_FILE_SIZE) {
        alert('File too large. Maximum size is 10MB.');
        return;
    }
    
    setLoading(true);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${CONFIG.API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Add file upload message
        const fileMsg = {
            type: 'user',
            content: `📎 Uploaded: ${file.name} (${formatFileSize(file.size)})`,
            timestamp: new Date().toISOString()
        };
        displayMessage(fileMsg);
        chatHistory.push(fileMsg);
        
        // Add AI response
        const aiMsg = {
            type: 'ai',
            content: data.analysis || 'File uploaded successfully!',
            timestamp: new Date().toISOString()
        };
        displayMessage(aiMsg);
        chatHistory.push(aiMsg);
        saveChatHistory();
        
    } catch (error) {
        console.error('Upload error:', error);
        const errorMsg = {
            type: 'ai',
            content: '❌ Failed to upload file. Please try again.',
            timestamp: new Date().toISOString()
        };
        displayMessage(errorMsg);
        chatHistory.push(errorMsg);
        saveChatHistory();
    } finally {
        setLoading(false);
        fileInput.value = ''; // Reset file input
    }
}

// UI functions
function displayMessage(msg) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${msg.type}-message`;
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    // Format content with markdown-like styling
    const formattedContent = formatMessageContent(msg.content);
    content.innerHTML = formattedContent;
    
    const timestamp = document.createElement('div');
    timestamp.className = 'message-timestamp';
    timestamp.textContent = formatTimestamp(msg.timestamp);
    
    messageDiv.appendChild(content);
    messageDiv.appendChild(timestamp);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessageContent(content) {
    return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function setLoading(loading) {
    isLoading = loading;
    sendBtn.disabled = loading;
    userInput.disabled = loading;
    
    if (loading) {
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    } else {
        sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
    }
}

// Chat history management
function saveChatHistory() {
    // Keep only last 50 messages to prevent storage overflow
    const recentHistory = chatHistory.slice(-CONFIG.MAX_MESSAGES);
    localStorage.setItem('chatHistory', JSON.stringify(recentHistory));
}

function loadChatHistory() {
    try {
        const saved = localStorage.getItem('chatHistory');
        if (saved) {
            chatHistory = JSON.parse(saved);
            chatHistory.forEach(msg => displayMessage(msg));
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
        chatHistory = [];
    }
}

function clearChatHistory() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        chatHistory = [];
        chatMessages.innerHTML = '';
        localStorage.removeItem('chatHistory');
        addWelcomeMessage();
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