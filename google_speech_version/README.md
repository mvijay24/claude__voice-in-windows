# 🎤 Google Speech Recognition - Minimal Version

**FREE Speech-to-Text using Google's Web Speech API (same as Google Docs)!**

## 🚀 Key Features

- **No API Key Required** - Uses browser's built-in speech recognition
- **Hindi-English Support** - Perfect for Hinglish code-switching
- **Auto-restart Logic** - Handles 60-second timeout automatically
- **Smart Silence Detection** - Continues recording even during pauses
- **Error Recovery** - Automatic reconnection on network issues
- **Minimal & Fast** - Lightweight system tray app

## 🔧 Technical Advantages over Whisper Version

1. **FREE** - No OpenAI API costs
2. **Real-time** - Instant transcription (no upload delay)
3. **Continuous** - Auto-handles timeout limits
4. **Browser-based** - Uses Google's powerful speech engine

## 📋 Requirements

- Windows 10/11
- Python 3.8+
- Chrome/Edge browser (for Web Speech API)
- Internet connection

## 🎯 Quick Start

1. **Run the setup:**
   ```
   setup_and_run.bat
   ```

2. **Use Ctrl+Space to start/stop recording**

3. **Text auto-pastes where your cursor is!**

## 🐛 Fixed Issues

✅ **60-second timeout** - Auto-restarts at 55 seconds
✅ **Silence detection** - Continues recording through pauses  
✅ **Connection drops** - Automatic reconnection
✅ **5-11 second delays** - Instant restart (100ms)
✅ **Session conflicts** - Proper state management

## ⚙️ How It Works

```
Your Voice → Browser Engine → Google Speech API → Text → Auto-paste
```

- Uses `webkitSpeechRecognition` API
- Hidden browser window runs in background
- System tray controls everything
- Zero configuration needed!

## 🎨 System Tray Menu

- 🎤 **Toggle Recording** (Ctrl+Space)
- 📊 **Show Debug Window** - See live transcription
- 🙈 **Hide Debug Window** - Run in background
- ❌ **Quit** - Exit application

## 🔍 Debug Features

- Real-time transcription display
- Session timing information
- Error logging
- Auto-restart counter

## 📝 Language Support

Default: **Hindi-India (hi-IN)** - Best for Hinglish
- Handles Hindi words in Roman script
- Switches seamlessly between Hindi and English
- Better accuracy than generic English mode

---

**Made with ❤️ using Google's Web Speech API**