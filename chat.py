from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import re
import secrets
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv
from functools import wraps
import json
from collections import defaultdict
import tempfile
import base64

# Load environment variables
load_dotenv()
print("Environment variables loaded")

# Flask setup
app = Flask(__name__, 
    static_url_path='',
    static_folder='static',
    template_folder='templates'
)
CORS(app)
app.secret_key = secrets.token_hex(32)  # Generate a secure random key
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
print(f"Upload folder created/verified: {app.config['UPLOAD_FOLDER']}")

# Rate limiting config
RATE_LIMIT_WINDOW = 60  # 1 minute window
MAX_REQUESTS_PER_WINDOW = 30  # 30 requests per minute

# In-memory rate limiting
request_history = defaultdict(list)

def check_rate_limit():
    now = datetime.now()
    client_ip = request.remote_addr
    
    # Clean up old requests
    request_history[client_ip] = [t for t in request_history[client_ip] 
                                if now - t < timedelta(seconds=RATE_LIMIT_WINDOW)]
    
    # Check if rate limit exceeded
    if len(request_history[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
        return False
    
    # Add current request
    request_history[client_ip].append(now)
    return True

# Gemini API config
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
print(f"API Key loaded: {'Yes' if GEMINI_API_KEY else 'No'}")

if not GEMINI_API_KEY:
    raise EnvironmentError("❌ GEMINI_API_KEY not found. Please check your .env file.")

genai.configure(api_key=GEMINI_API_KEY)

# Model initialization
try:
    # List available models
    print("Checking available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Available model: {m.name}")
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini model initialized.")
except Exception as e:
    print(f"❌ Failed to initialize Gemini model: {e}")
    model = None

def initialize_model():
    global model
    try:
        print("Initializing Gemini model...")
        model = genai.GenerativeModel('gemini-1.5-flash',
            generation_config={
                'temperature': 0.85,  # More creative, less robotic
                'top_p': 0.9,
                'top_k': 40,
                'max_output_tokens': 2048,
                'candidate_count': 1,
            }
        )
        print("Testing model with a simple prompt...")
        response = model.generate_content("Hello")
        if response and response.text:
            print("Gemini model initialized successfully.")
            return True
        else:
            print("Warning: Model initialized but test response was empty")
            return False
    except Exception as e:
        print(f"Error initializing model: {str(e)}")
        return False

def format_response(text):
    """Format the AI response for better readability and ChatGPT-like structure"""
    if not text:
        return "I'm not sure how to answer that."
    
    # Clean up the text first
    text = text.strip()
    
    # Remove ALL asterisks completely
    text = re.sub(r'\*+', '', text)
    
    # Remove other markdown symbols that might be used for emphasis
    text = re.sub(r'[_~`]+', '', text)
    
    # Clean up any double spaces created by removing symbols
    text = re.sub(r'\s+', ' ', text)
    
    # Improve paragraph structure
    # Add proper spacing around headers and sections
    text = re.sub(r'\n([A-Z][A-Z\s:]+:)\n', r'\n\n\1\n', text)
    
    # Ensure proper spacing after colons in headers
    text = re.sub(r'([A-Z][A-Z\s]+:)([^\n])', r'\1\n\2', text)
    
    # Add spacing around numbered lists
    text = re.sub(r'\n(\d+\.)', r'\n\n\1', text)
    
    # Add spacing around bullet points (dashes)
    text = re.sub(r'\n(-\s)', r'\n\n\1', text)
    
    # Improve code block formatting
    text = re.sub(r'```(\w+)?\n', r'\n```\1\n', text)
    text = re.sub(r'\n```\n', r'\n\n```\n\n', text)
    
    # Add spacing around dividers but keep them clean
    text = re.sub(r'\n(---+)\n', r'\n\n\1\n\n', text)
    
    # Ensure proper paragraph breaks
    text = re.sub(r'([.!?])\s*\n([A-Z])', r'\1\n\n\2', text)
    
    # Clean up excessive line breaks (more than 3)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    
    # Preserve and clean code blocks
    def clean_code_block(match):
        code_content = match.group(0)
        return re.sub(r'\*+', '', code_content)
    
    text = re.sub(r'```[\s\S]*?```', clean_code_block, text)
    
    # Final cleanup of multiple spaces and tabs
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Ensure the response starts cleanly
    text = text.strip()
    
    return text

def handle_api_error(e):
    error_message = str(e)
    if "API key" in error_message.lower():
        return "Authentication error with the AI service. Please contact support.", 401
    elif "quota" in error_message.lower():
        return "Service quota exceeded. Please try again later.", 429
    elif "rate limit" in error_message.lower():
        return "Too many requests. Please try again later.", 429
    else:
        return f"An error occurred: {error_message}", 500
    
# Flask Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signin')
def signin():
    return render_template('signin.html')

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        system_instruction = (
            "You are a helpful, knowledgeable, and professional AI assistant. Provide clear, accurate, and well-structured responses.\n\n"
            "RESPONSE FORMATTING GUIDELINES:\n"
            "- Write in a conversational yet professional tone\n"
            "- Structure your responses with clear organization\n"
            "- Use proper headings and subheadings when appropriate\n"
            "- Break down complex information into digestible parts\n"
            "- Use numbered lists for step-by-step instructions\n"
            "- Use bullet points for features, benefits, or key points\n"
            "- Include examples when they help clarify concepts\n"
            "- Keep paragraphs concise and focused\n"
            "- Use line breaks to improve readability\n"
            "- NEVER use asterisks (*) for formatting\n"
            "- Use dashes (-) for bullet points\n"
            "- Use CAPITAL LETTERS sparingly for emphasis\n"
            "- Format code snippets clearly when relevant\n\n"
            "CONTENT GUIDELINES:\n"
            "- Be comprehensive but concise\n"
            "- Provide practical, actionable information\n"
            "- Explain technical concepts in accessible language\n"
            "- Offer multiple perspectives when appropriate\n"
            "- Include relevant context and background\n"
            "- End with a summary or key takeaway when helpful\n"
            "- When analyzing files or images, provide detailed structured analysis\n"
            "- Always aim for clarity and helpfulness\n"
            "- Use conversation history to provide contextually relevant responses\n"
            "- Reference previous messages when answering follow-up questions\n\n"
            "Remember: Your goal is to be as helpful as possible while maintaining a clean, professional presentation."
        )

        # Get conversation history from request
        conversation_history = []
        
        # Check if this is a file upload request
        if 'file' in request.files:
            file = request.files['file']
            message = request.form.get('message', '')
            
            # Get conversation history from form data
            history_json = request.form.get('conversation_history', '[]')
            try:
                conversation_history = json.loads(history_json)
            except:
                conversation_history = []
            
            if not file or file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            print(f"Processing file: {file.filename}, type: {file.mimetype}")
            
            # Create a secure filename
            filename = secrets.token_hex(8) + "_" + file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(file_path)
                print(f"File saved to: {file_path}")
            except Exception as e:
                print(f"Error saving file: {e}")
                return jsonify({"error": "Failed to save file"}), 500

            # Handle different file types
            if file.mimetype.startswith('image/'):
                # Handle image files
                try:
                    with open(file_path, 'rb') as img_file:
                        image_data = img_file.read()
                    
                    # Convert to base64 for Gemini
                    image_b64 = base64.b64encode(image_data).decode('utf-8')
                    
                    # Build conversation context
                    context = ""
                    if conversation_history:
                        context = "\n\nCONVERSATION CONTEXT:\n"
                        for msg in conversation_history[-10:]:  # Last 10 messages for context
                            role = "User" if msg.get('role') == 'user' else "Assistant"
                            context += f"{role}: {msg.get('content', '')}\n"
                        context += "\n"
                    
                    # Create proper format for Gemini Vision
                    prompt_text = system_instruction + context + "\n\n" + (
                        message if message else 
                        "Please analyze this image for me. I'd like to understand what's shown here.\n\n"
                        "Could you provide:\n\n"
                        "1. A brief overview of what you see\n"
                        "2. Key details about the main subjects or objects\n"
                        "3. Information about colors, composition, and setting\n"
                        "4. Any text or important details you notice\n"
                        "5. Notable features, patterns, or technical aspects\n\n"
                        "Please organize your response in a clear, easy-to-read format."
                    )
                    
                    # Use the correct Gemini format
                    content = [
                        prompt_text,
                        {
                            "mime_type": file.mimetype,
                            "data": image_b64
                        }
                    ]
                    
                    if model:
                        response = model.generate_content(content)
                        answer = format_response(response.text) if response and response.text else "I couldn't analyze this image."
                    else:
                        answer = "AI model is not available."
                        
                except Exception as e:
                    print(f"Error processing image: {e}")
                    answer = f"Sorry, I couldn't process this image. Error: {str(e)}"
                    
            elif file.mimetype.startswith('text/') or file.filename.endswith(('.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv')):
                # Handle text files
                try:
                    with open(file_path, 'r', encoding='utf-8') as text_file:
                        file_content = text_file.read()
                    
                    # Build conversation context
                    context = ""
                    if conversation_history:
                        context = "\n\nCONVERSATION CONTEXT:\n"
                        for msg in conversation_history[-10:]:  # Last 10 messages for context
                            role = "User" if msg.get('role') == 'user' else "Assistant"
                            context += f"{role}: {msg.get('content', '')}\n"
                        context += "\n"
                    
                    prompt_text = system_instruction + context + "\n\n" + (
                        f"I've uploaded a file called '{file.filename}'. Could you analyze it for me?\n\n"
                        f"Here's the content:\n\n```\n{file_content}\n```\n\n" +
                        (message if message else 
                         "Please help me understand this file by providing:\n\n"
                         "1. What type of file this is and its main purpose\n"
                         "2. Key components, functions, or sections\n"
                         "3. How it's structured and organized\n"
                         "4. Any notable features or important aspects\n"
                         "5. If it's code, any observations about quality or potential improvements\n\n"
                         "Please explain everything in a clear, helpful way.")
                    )
                    
                    if model:
                        response = model.generate_content(prompt_text)
                        answer = format_response(response.text) if response and response.text else "I couldn't analyze this file."
                    else:
                        answer = "AI model is not available."
                        
                except UnicodeDecodeError:
                    answer = "Sorry, I couldn't read this file. It might be in a format I don't support or contain non-text data."
                except Exception as e:
                    print(f"Error processing text file: {e}")
                    answer = f"Sorry, I couldn't process this file. Error: {str(e)}"
            else:
                answer = f"Sorry, I don't support files of type '{file.mimetype}'. I can analyze images and text files."

            return jsonify({
                "response": answer,
                "file_url": f"/static/uploads/{filename}",
                "file_name": file.filename,
                "file_type": file.mimetype
            })

        # Handle regular text chat (no file)
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        message = data.get('message', '')
        conversation_history = data.get('conversation_history', [])
        
        if not message:
            return jsonify({"error": "No message provided"}), 400

        # Build conversation context for text messages
        context = ""
        if conversation_history:
            context = "\n\nCONVERSATION CONTEXT:\n"
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                role = "User" if msg.get('role') == 'user' else "Assistant"
                context += f"{role}: {msg.get('content', '')}\n"
            context += "\nCurrent User Message: "

        prompt_text = system_instruction + context + message + "\n\nAssistant:"
        
        if model:
            response = model.generate_content(prompt_text)
            answer = format_response(response.text) if response and response.text else "I'm not sure how to respond to that."
        else:
            answer = "AI model is not available."

        return jsonify({"response": answer})
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Serve uploaded files (if not already handled)
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Entry point
if __name__ == '__main__':
    # Only kill existing processes if we're not in a reloader subprocess
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        import subprocess
        try:
            result = subprocess.run(['lsof', '-ti:5000'], capture_output=True, text=True)
            if result.stdout.strip():
                print("Port 5000 is in use, clearing it...")
                subprocess.run(['kill', '-TERM'] + result.stdout.strip().split(), capture_output=True)
                import time
                time.sleep(0.5)
            print("Port 5000 is ready")
        except Exception as e:
            print(f"Note: Could not check port 5000: {e}")
    
    if initialize_model():
        print("✅ AI model initialized successfully.")
    else:
        print("❌ Failed to initialize the AI model. The application will start but chat functionality will be disabled.")
    
    # Get local IP address with error handling
    import socket
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except socket.error:
        # Fallback method to get local IP
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "127.0.0.1"  # Ultimate fallback
    
    # Only show startup messages on main process
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        print(f"🌐 Server starting...")
        print(f"📱 Access from other devices:")
        print(f"   Local: http://127.0.0.1:5000")
        print(f"   Network: http://{local_ip}:5000")
        print(f"   Mobile: Use the Network URL above")
        print(f"⚠️  Make sure your devices are on the same WiFi network")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        print("Trying to start without debug mode...")
        try:
            app.run(debug=False, host='0.0.0.0', port=5000)
        except Exception as e2:
            print(f"❌ Failed to start server: {e2}")

