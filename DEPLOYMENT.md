# 🚀 Deployment Guide - Link AI

## Your App is Live! 🎉

### 🌐 **Frontend (GitHub Pages)**
**Your static website will be available at:**
```
https://nrbalpha.github.io/link-ai-chat/
```

### 🐍 **Backend (Railway)**
**Your Python Flask API is running at:**
```
https://green-rainstorm-production.up.railway.app
```

---

## 📋 **Enable GitHub Pages**

1. **Go to your GitHub repository:**
   - Visit: https://github.com/NRBalpha/link-ai-chat

2. **Navigate to Settings:**
   - Click the "Settings" tab at the top

3. **Enable GitHub Pages:**
   - Scroll down to "Pages" in the left sidebar
   - Under "Source", select "Deploy from a branch"
   - Choose "main" branch
   - Select "/ (root)" folder
   - Click "Save"

4. **Wait for deployment:**
   - GitHub will show a green checkmark when ready
   - Your site will be live at: `https://nrbalpha.github.io/link-ai-chat/`

---

## ✅ **What's Working**

### 🎯 **Fully Functional Features:**
- ✅ **AI Chat** - Powered by Google Gemini API
- ✅ **File Upload & Analysis** - Upload documents, images, code
- ✅ **Dark/Light Mode** - Toggle theme
- ✅ **Chat History** - Saved locally
- ✅ **Responsive Design** - Works on mobile & desktop
- ✅ **Real-time Responses** - Connected to your Railway backend

### 🔧 **Technical Stack:**
- **Frontend:** HTML, CSS, JavaScript (GitHub Pages)
- **Backend:** Python Flask (Railway)
- **AI:** Google Gemini API
- **Storage:** Local Storage (browser)

---

## 🛠️ **Configuration**

### 🔑 **API Key Setup**
Your Gemini API key is already configured in the Railway backend. No additional setup needed!

### 🌍 **Environment Variables (Railway)**
The following are set in your Railway deployment:
```
GEMINI_API_KEY=your_actual_api_key
FLASK_ENV=production
PORT=5000
```

---

## 📱 **How to Use**

1. **Visit your GitHub Pages site**
2. **Start chatting** - Type any message
3. **Upload files** - Click the 📎 button to analyze documents
4. **Toggle theme** - Use the 🌙/☀️ button
5. **Clear history** - Use the 🗑️ button

---

## 🚀 **Free Hosting Benefits**

### 💰 **Cost: $0/month**
- **GitHub Pages:** Free static hosting
- **Railway:** Free tier (500 hours/month)
- **Gemini API:** Free tier (60 requests/minute)

### ⚡ **Performance:**
- **Frontend:** Fast CDN delivery via GitHub
- **Backend:** Auto-scaling on Railway
- **Global:** Available worldwide

---

## 🔧 **Troubleshooting**

### 🐛 **Common Issues:**

1. **"Can't connect to server"**
   - Railway apps go to sleep after inactivity
   - First request may take 10-15 seconds to wake up
   - Subsequent requests will be fast

2. **File upload fails**
   - Check file size (max 10MB)
   - Ensure stable internet connection

3. **GitHub Pages not loading**
   - Wait 5-10 minutes after enabling
   - Check repository settings

### 🔍 **Debug Steps:**
1. Open browser Developer Tools (F12)
2. Check Console for errors
3. Verify network requests in Network tab

---

## 🔄 **Updates & Maintenance**

### 📝 **To Update Your App:**
1. Make changes to your local files
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update description"
   git push origin main
   ```
3. GitHub Pages will auto-deploy
4. Railway will auto-deploy backend changes

### 📊 **Monitor Usage:**
- **Railway Dashboard:** https://railway.app/dashboard
- **GitHub Pages:** Repository → Settings → Pages

---

## 🎉 **You're All Set!**

Your AI chat application is now live and fully functional! 

🌐 **Frontend:** https://nrbalpha.github.io/link-ai-chat/
🐍 **Backend:** https://green-rainstorm-production.up.railway.app

**Enjoy your free, fully-hosted AI chat app!** 🚀 