from flask import Flask, request, jsonify, render_template, send_from_directory, Response
from flask_cors import CORS
import os
import secrets
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv
import json
from collections import defaultdict
import base64
import threading

# Load environment variables
load_dotenv()

# Flask setup
app = Flask(__name__,
    static_url_path='',
    static_folder='static',
    template_folder='templates'
)
CORS(app)
app.secret_key = secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Rate limiting config
RATE_LIMIT_WINDOW = 60  # 1 minute window
MAX_REQUESTS_PER_WINDOW = 30  # 30 requests per minute

# In-memory rate limiting
request_history = defaultdict(list)

def check_rate_limit():
    now = datetime.now()
    client_ip = request.remote_addr
    request_history[client_ip] = [t for t in request_history[client_ip]
                                if now - t < timedelta(seconds=RATE_LIMIT_WINDOW)]
    if len(request_history[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
        return False
    request_history[client_ip].append(now)
    return True

# Gemini API config
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found. Please check your .env file.")

genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = None
model = None

SYSTEM_INSTRUCTION = (
    "You are ENKU, a smart assistant embedded in the ENKU superapp. "
    "Beyond conversation, you can trigger in-app actions called 'mini-apps' based on user requests.\n\n"

    "LANGUAGE RULES:\n"
    "- You speak Amharic (አማርኛ), Afaan Oromo, Tigrinya, and English fluently.\n"
    "- Auto-detect the user's language from their message and respond in the same language.\n"
    "- If a user types Amharic in Latin characters (e.g., 'selam', 'dehna neh', 'eshi'), "
    "understand it and respond in proper Ge'ez script (ግዕዝ) with a Latin transliteration below.\n"
    "- If unsure of the language, default to Amharic and politely ask the user's preference.\n"
    "- Never mix languages in a single response unless the user does.\n\n"

    "CULTURAL AWARENESS:\n"
    "- You use the Ethiopian calendar (e.g., Yekatit 12, 2018 E.C.) alongside the Gregorian calendar when relevant.\n"
    "- You are aware of Ethiopian holidays: Enkutatash, Meskel, Timkat, Genna, Irreecha, Eid al-Fitr, Eid al-Adha "
    "and greet users appropriately during these times.\n"
    "- During Orthodox and Islamic fasting seasons, you are sensitive about food recommendations "
    "(no meat/dairy suggestions during fasting unless asked).\n"
    "- You naturally incorporate Ethiopian proverbs (ተረትና ምሳሌ) when they fit the conversation — but don't force them.\n"
    "- You understand Ethiopian cultural norms: respect for elders, communal values, coffee culture, and local humor.\n\n"

    "PERSONALITY:\n"
    "- Warm, respectful, and slightly playful — like a smart Ethiopian friend.\n"
    "- Use 'አንተ/አንቺ' appropriately based on context.\n"
    "- Keep responses concise for mobile users.\n"
    "- When greeting, use culturally natural greetings like 'ሰላም! ደህና ነህ/ነሽ?' not robotic ones.\n\n"

    "KNOWLEDGE:\n"
    "- You know Ethiopian geography, cities, zones, woredas.\n"
    "- You know local businesses, popular culture, music artists, and trending topics.\n"
    "- You understand the Ethiopian telecom landscape (Ethio Telecom, Safaricom Ethiopia).\n"
    "- You understand local payment systems (Telebirr, CBE Birr, Amole).\n\n"

    "AVAILABLE MINI-APPS:\n"
    "You have access to the following services. When a user's intent matches one, "
    "trigger the appropriate action using the JSON format specified below.\n\n"

    "1. PAYMENTS (Telebirr/CBE Birr)\n"
    "   - Trigger: User wants to send money, pay bills, check balance\n"
    '   - Action: { "mini_app": "payment", "type": "transfer|bill_pay|balance", '
    '"details": { "recipient": "", "amount": "", "provider": "telebirr|cbe_birr|amole" } }\n\n'

    "2. RIDE HAILING\n"
    "   - Trigger: User wants a ride, taxi, or transport\n"
    '   - Action: { "mini_app": "ride", "details": { "pickup": "", "destination": "", '
    '"ride_type": "standard|premium" } }\n\n'

    "3. FOOD ORDERING\n"
    "   - Trigger: User wants to order food or drinks\n"
    '   - Action: { "mini_app": "food_order", "details": { "query": "", "location": "", '
    '"dietary": "fasting|regular" } }\n\n'

    "4. UTILITY PAYMENTS\n"
    "   - Trigger: User wants to pay electricity, water, or telecom bills\n"
    '   - Action: { "mini_app": "utility", "type": "electricity|water|telecom|internet", '
    '"details": { "account_number": "", "amount": "" } }\n\n'

    "5. EVENT DISCOVERY\n"
    "   - Trigger: User asks about events, parties, concerts, meetups\n"
    '   - Action: { "mini_app": "events", "details": { "city": "", '
    '"category": "music|sports|cultural|nightlife|tech", "date_range": "" } }\n\n'

    "6. MARKETPLACE\n"
    "   - Trigger: User wants to buy, sell, or browse products\n"
    '   - Action: { "mini_app": "marketplace", "details": { "action": "browse|search|sell", '
    '"query": "", "category": "" } }\n\n'

    "CONVERSATION FLOW:\n"
    "- When a user expresses an intent matching a mini-app, acknowledge their request "
    "conversationally FIRST, then trigger the action.\n"
    "- If details are missing, ask naturally. Example:\n"
    '  User: "Send money to Abebe"\n'
    '  You: "እሺ! ለአበበ ስንት ብር ልላክ? (How much should I send to Abebe?)"\n'
    '  User: "500"\n'
    '  You: "500 ብር ለአበበ እልካለሁ። Confirm?" → then trigger payment action.\n'
    "- After triggering an action, provide a clear confirmation message.\n\n"

    "INTENT DETECTION RULES:\n"
    "- Parse both Amharic and English requests.\n"
    "- Understand informal phrasing:\n"
    '  "ሂሳቤን ክፈልልኝ" → bill payment\n'
    '  "ምግብ አዝልኝ" → food order\n'
    '  "ታክሲ ጥራልኝ" → ride request\n'
    '  "ዛሬ ምሽት ምን አለ?" → event discovery\n'
    "- If intent is ambiguous, ask for clarification — never assume.\n\n"

    "STRICT RULES:\n"
    "- NEVER process payments without explicit user confirmation.\n"
    "- NEVER store or display full account numbers — mask them (e.g., ****1234).\n"
    "- If a service is unavailable, apologize and suggest alternatives.\n"
    "- For amounts over 10,000 birr, add an extra confirmation step.\n"
    "- Always show a summary before executing: amount, recipient, and service.\n"
    "- If the user is just chatting (no mini-app intent), respond normally without triggering any action.\n"
    "- Never assume all Ethiopians speak Amharic — respect linguistic diversity.\n"
    "- Avoid making assumptions about ethnicity, religion, or politics.\n"
    "- If a user asks about sensitive political topics, remain neutral and respectful.\n"
    "- Always prioritize user privacy and never share personal data.\n\n"

    "FORMATTING:\n"
    "- Use **bold** for emphasis\n"
    "- Use `code` for inline code\n"
    "- Use ```language for code blocks\n"
    "- Use headings (##, ###) for sections\n"
    "- Use numbered lists for steps\n"
    "- Use bullet points for lists\n"
    "- Keep paragraphs concise and focused\n"
    "- When analyzing files or images, provide detailed structured analysis\n"
    "- Use conversation history to provide contextually relevant responses"
)

def get_default_model_name():
    global MODEL_NAME
    if MODEL_NAME:
        return MODEL_NAME

    try:
        print("Discovering available Gemini models...")
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in getattr(m, 'supported_generation_methods', []):
                available_models.append(m.name)

        if not available_models:
            print("No models with generateContent support found.")
            return None

        preferred = [
            "gemini-3-flash-preview",
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.5-pro",
        ]

        for target in preferred:
            for name in available_models:
                if target in name:
                    MODEL_NAME = name
                    print(f"Using model: {MODEL_NAME}")
                    return MODEL_NAME

        MODEL_NAME = available_models[0]
        print(f"Using fallback model: {MODEL_NAME}")
        return MODEL_NAME

    except Exception as e:
        print(f"Failed to list models: {e}")
        return None

def initialize_model():
    global model, MODEL_NAME
    try:
        if not MODEL_NAME:
            MODEL_NAME = get_default_model_name()

        if not MODEL_NAME:
            print("Could not determine a valid model name.")
            model = None
            return False

        print(f"Initializing Gemini model: {MODEL_NAME}")
        model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config={
                'temperature': 0.85,
                'top_p': 0.9,
                'top_k': 40,
                'max_output_tokens': 8192,
            },
            system_instruction=SYSTEM_INSTRUCTION
        )
        print("Model initialized successfully.")
        return True
    except Exception as e:
        print(f"Error initializing model: {str(e)}")
        model = None
        return False

def handle_api_error(e):
    error_message = str(e)
    if "API key" in error_message.lower():
        return "Authentication error with the AI service.", 401
    elif "quota" in error_message.lower():
        return "Service quota exceeded. Please try again later.", 429
    elif "rate limit" in error_message.lower():
        return "Too many requests. Please try again later.", 429
    elif "blocked" in error_message.lower():
        return "The response was blocked by safety filters. Please try rephrasing.", 400
    else:
        return f"An error occurred: {error_message}", 500

LANGUAGE_INSTRUCTIONS = {
    'am': 'You MUST respond ONLY in Amharic (አማርኛ). No matter what language the user writes in, always reply in Amharic script. This is mandatory.',
    'en': '',
    'so': 'You MUST respond ONLY in Somali (Af-Soomaali). No matter what language the user writes in, always reply in Somali. This is mandatory.',
    'om': 'You MUST respond ONLY in Afaan Oromoo (Oromo). No matter what language the user writes in, always reply in Afaan Oromoo. This is mandatory.',
    'ti': 'You MUST respond ONLY in Tigrinya (ትግርኛ). No matter what language the user writes in, always reply in Tigrinya script. This is mandatory.',
}

def build_contents(conversation_history, message=None, language='en'):
    """Build a proper contents list for Gemini API from conversation history."""
    contents = []
    for msg in conversation_history[-10:]:
        role = 'user' if msg.get('role') == 'user' else 'model'
        content = msg.get('content', '')
        if content:
            contents.append({'role': role, 'parts': [content]})
    if message:
        lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, '')
        if lang_instruction:
            message = f"[{lang_instruction}]\n\n{message}"
        contents.append({'role': 'user', 'parts': [message]})
    return contents

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
    """Handle file uploads and non-streaming chat."""
    if not check_rate_limit():
        return jsonify({"error": "Too many requests. Please wait a moment."}), 429

    try:
        conversation_history = []

        # File upload request
        if 'file' in request.files:
            file = request.files['file']
            message = request.form.get('message', '')

            history_json = request.form.get('conversation_history', '[]')
            file_language = request.form.get('language', 'en')
            try:
                conversation_history = json.loads(history_json)
            except Exception:
                conversation_history = []

            if not file or file.filename == '':
                return jsonify({"error": "No file selected"}), 400

            # Create a secure filename
            filename = secrets.token_hex(8) + "_" + file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            try:
                file.save(file_path)
            except Exception as e:
                return jsonify({"error": "Failed to save file"}), 500

            if file.mimetype.startswith('image/'):
                try:
                    with open(file_path, 'rb') as img_file:
                        image_data = img_file.read()

                    image_b64 = base64.b64encode(image_data).decode('utf-8')

                    prompt_text = message if message else (
                        "Please analyze this image. Provide:\n"
                        "1. A brief overview of what you see\n"
                        "2. Key details about the main subjects or objects\n"
                        "3. Any text or important details you notice"
                    )
                    lang_instr = LANGUAGE_INSTRUCTIONS.get(file_language, '')
                    if lang_instr:
                        prompt_text = f"[{lang_instr}]\n\n{prompt_text}"

                    content = [
                        prompt_text,
                        {"mime_type": file.mimetype, "data": image_b64}
                    ]

                    if model:
                        try:
                            response = model.generate_content(content)
                            answer = response.text if response and response.text else "I couldn't analyze this image."
                        except Exception as e:
                            error_msg, _ = handle_api_error(e)
                            answer = error_msg
                    else:
                        answer = "AI model is not available. Please restart the server."

                except Exception as e:
                    answer = f"Sorry, I couldn't process this image. Error: {str(e)}"

            elif file.mimetype.startswith('text/') or file.filename.endswith(('.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.md', '.ts', '.tsx', '.jsx')):
                try:
                    with open(file_path, 'r', encoding='utf-8') as text_file:
                        file_content = text_file.read()[:50000]  # Limit to 50k chars

                    prompt_text = (
                        f"I've uploaded a file called '{file.filename}'.\n\n"
                        f"```\n{file_content}\n```\n\n"
                        + (message if message else "Please analyze this file.")
                    )
                    lang_instr = LANGUAGE_INSTRUCTIONS.get(file_language, '')
                    if lang_instr:
                        prompt_text = f"[{lang_instr}]\n\n{prompt_text}"

                    if model:
                        try:
                            response = model.generate_content(prompt_text)
                            answer = response.text if response and response.text else "I couldn't analyze this file."
                        except Exception as e:
                            error_msg, _ = handle_api_error(e)
                            answer = error_msg
                    else:
                        answer = "AI model is not available. Please restart the server."

                except UnicodeDecodeError:
                    answer = "Sorry, I couldn't read this file. It may contain non-text data."
                except Exception as e:
                    answer = f"Sorry, I couldn't process this file. Error: {str(e)}"
            else:
                answer = f"Sorry, I don't support files of type '{file.mimetype}'. I can analyze images and text files."

            return jsonify({
                "response": answer,
                "file_url": f"/static/uploads/{filename}",
                "file_name": file.filename,
                "file_type": file.mimetype
            })

        # Regular text chat (no file)
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        message = data.get('message', '').strip()
        conversation_history = data.get('conversation_history', [])
        language = data.get('language', 'en')

        if not message:
            return jsonify({"error": "No message provided"}), 400

        if not model:
            return jsonify({"error": "AI model is not available. Please restart the server."}), 503

        contents = build_contents(conversation_history, message, language)

        try:
            response = model.generate_content(contents)
            answer = response.text if response and response.text else "I'm not sure how to respond to that."
        except Exception as e:
            error_msg, status_code = handle_api_error(e)
            return jsonify({"error": error_msg}), status_code

        return jsonify({"response": answer})

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    """Streaming chat endpoint using Server-Sent Events."""
    if not check_rate_limit():
        return jsonify({"error": "Too many requests. Please wait a moment."}), 429

    data = request.get_json()
    if not data or not data.get('message', '').strip():
        return jsonify({"error": "No message provided"}), 400

    if not model:
        return jsonify({"error": "AI model is not available."}), 503

    message = data['message'].strip()
    conversation_history = data.get('conversation_history', [])
    language = data.get('language', 'en')
    contents = build_contents(conversation_history, message, language)

    def generate():
        try:
            response = model.generate_content(contents, stream=True)
            for chunk in response:
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            error_msg, _ = handle_api_error(e)
            yield f"data: {json.dumps({'error': error_msg})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )

# Serve uploaded files
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ---- Email Verification System ----
# In-memory store: { email: { code, expires, attempts } }
verification_codes = {}

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')
SMTP_FROM = os.getenv('SMTP_FROM', '') or SMTP_USER

def generate_verification_code():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_verification_email(to_email, code):
    """Send verification code via SMTP. Falls back to console logging."""
    if not SMTP_USER or not SMTP_PASS:
        print(f"[VERIFICATION] No SMTP configured. Code for {to_email}: {code}")
        return True

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'ENKU - Your Verification Code'
        msg['From'] = SMTP_FROM
        msg['To'] = to_email

        html = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px; background: #1a1a1a; border-radius: 12px;">
            <h1 style="color: #4285F4; text-align: center; margin-bottom: 8px;">ENKU</h1>
            <p style="color: #888; text-align: center; margin-bottom: 24px;">Email Verification</p>
            <div style="background: #2d2d2d; border-radius: 8px; padding: 24px; text-align: center; margin-bottom: 24px;">
                <p style="color: #aaa; margin-bottom: 16px;">Your verification code is:</p>
                <div style="font-size: 32px; font-weight: 700; letter-spacing: 8px; color: #4285F4;">{code}</div>
            </div>
            <p style="color: #666; font-size: 13px; text-align: center;">This code expires in 10 minutes. If you didn't request this, please ignore this email.</p>
        </div>
        """
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())

        print(f"[VERIFICATION] Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"[VERIFICATION] SMTP failed: {e}. Code for {to_email}: {code}")
        return True  # Still return True so the flow continues

@app.route('/send-verification', methods=['POST'])
def send_verification():
    data = request.get_json()
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Rate limit: don't allow resending within 60 seconds
    existing = verification_codes.get(email)
    if existing and datetime.now() < existing.get('cooldown', datetime.min):
        return jsonify({"error": "Please wait before requesting a new code"}), 429

    code = generate_verification_code()
    verification_codes[email] = {
        'code': code,
        'expires': datetime.now() + timedelta(minutes=10),
        'cooldown': datetime.now() + timedelta(seconds=60),
        'attempts': 0
    }

    send_verification_email(email, code)
    return jsonify({"message": "Verification code sent"})

@app.route('/verify-code', methods=['POST'])
def verify_code():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()

    if not email or not code:
        return jsonify({"error": "Email and code are required"}), 400

    record = verification_codes.get(email)
    if not record:
        return jsonify({"error": "No verification code found. Please request a new one."}), 400

    if datetime.now() > record['expires']:
        del verification_codes[email]
        return jsonify({"error": "Code has expired. Please request a new one."}), 400

    record['attempts'] += 1
    if record['attempts'] > 5:
        del verification_codes[email]
        return jsonify({"error": "Too many attempts. Please request a new code."}), 429

    if record['code'] != code:
        return jsonify({"error": "Invalid verification code. Please try again."}), 400

    # Code is valid - clean up
    del verification_codes[email]
    return jsonify({"message": "Email verified successfully"})

# Initialize model in background thread (so gunicorn can bind the port immediately)
def _init_model_background():
    initialize_model()
    if model:
        print("AI model ready.")
    else:
        print("Failed to initialize AI model. Chat will be disabled.")

threading.Thread(target=_init_model_background, daemon=True).start()

# Entry point
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))

    if model:
        print(f"AI model ready. Starting server on port {port}...")
    else:
        print("Failed to initialize AI model. Chat will be disabled.")

    app.run(debug=True, host='0.0.0.0', port=port)
