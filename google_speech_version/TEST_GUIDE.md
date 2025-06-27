# 🎤 Google Speech Recognition - Test Guide

## Quick Test Options:

### 1️⃣ **Instant Browser Test** (Easiest!)
- **File:** `quick_test.html`
- Just double-click to open in browser
- Click button and speak
- Text auto-copies to clipboard

### 2️⃣ **Full Standalone Version**
- **File:** `standalone_speech.html`
- Double-click to open
- Press Space to start, Esc to stop
- Full features with stats

### 3️⃣ **System Tray Version**
- **File:** `test_now.bat`
- Double-click to run
- Check system tray (bottom-right)
- Use Ctrl+Space to record

## 🧪 Testing Steps:

1. **Open any HTML file above**
2. **Allow microphone permission** (browser will ask)
3. **Speak in Hindi/English:**
   - "Hello bhai kaise ho"
   - "Main theek hun, aap batao"
   - "Code likhna hai mujhe"

## ✅ What Should Happen:

- **Instant transcription** appears
- **Auto-copies** to clipboard
- **No 60-second timeout** (auto-restarts)
- **No silence breaks** (ignores pauses)

## 🔧 If Not Working:

1. **Check browser:** Use Chrome/Edge only
2. **Microphone permission:** Allow when asked
3. **Internet connection:** Required for Google API

## 📊 Server Status Check:

Open browser and go to:
```
http://localhost:8899
```

If page loads = server is running!

---

**Bhai, try kar ke bata kaisa laga!** 🚀