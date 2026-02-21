# Link AI - HTML/CSS/JavaScript Chat Application

A modern, responsive AI chat application built with pure HTML, CSS, and JavaScript, powered by Google Gemini AI.

## 🚀 Features

- **AI Chat Interface**: Powered by Google Gemini AI
- **File Upload Support**: Upload images, documents, and code files
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Dark/Light Theme**: Toggle between themes
- **Modern UI**: Clean, intuitive interface with smooth animations
- **Authentication**: User sign-in and sign-up functionality

## 📁 Project Structure

```
gemini-1/
├── assets/
│   ├── css/
│   │   └── style.css          # Main stylesheet
│   ├── js/
│   │   └── script.js          # Main JavaScript functionality
│   └── images/
│       └── logos/             # Technology logos
├── templates/                  # Original HTML templates
├── static/                     # Static assets
├── chat.py                     # Python backend for AI chat
├── run_server.py               # Local development server
├── index.html                  # Main landing page
├── chat.html                   # Chat interface
├── welcome.html                # Welcome page
├── signin.html                 # Sign in page
├── signup.html                 # Sign up page
└── README.md                   # This file
```

## 🛠️ Technologies Used

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python (Flask-like structure)
- **AI**: Google Gemini API
- **Styling**: Custom CSS with modern design principles
- **Icons**: Font Awesome

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- Modern web browser
- Google Gemini API key (for AI functionality)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd gemini-1
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

### Running the Application

#### Option 1: Python HTTP Server (Recommended for development)
   ```bash
python run_server.py
   ```
This will start a local server at `http://localhost:8000`

#### Option 2: Python Backend
```bash
python chat.py
```
This runs the AI chat backend service

#### Option 3: Direct File Opening
Simply open any HTML file in your web browser (some features may not work without a server)

## 📱 Pages

- **`/index.html`** - Main landing page with technology showcase
- **`/chat.html`** - AI chat interface
- **`/welcome.html`** - Welcome page
- **`/signin.html`** - User authentication
- **`/signup.html`** - User registration

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
```

### API Keys

- **Google Gemini**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## 🎨 Customization

### Styling
- Main styles are in `assets/css/style.css`
- Each HTML file contains inline styles for specific components
- Use CSS variables for consistent theming

### JavaScript
- Main functionality is in `assets/js/script.js`
- Each HTML file contains page-specific JavaScript
- Modular structure for easy maintenance

## 🌐 Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the code examples

## 🔄 Migration Notes

This project has been migrated from Next.js to pure HTML/CSS/JavaScript for:
- **Simpler deployment**: No build process required
- **Easier maintenance**: Standard web technologies
- **Better performance**: No JavaScript framework overhead
- **Wider compatibility**: Works with any web server

---

**Built with ❤️ using modern web technologies** 