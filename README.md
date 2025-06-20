# 🎤 Whisper Paste - Hinglish Voice Transcription

A lightweight Windows system tray application that converts speech to text using OpenAI's Whisper API. Perfect for code-switching between Hindi and English!

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- 🔵 **System Tray Application** - Runs silently in background
- 🔑 **Easy API Key Setup** - Set your API key directly from the tray menu
- 🎯 **Two Output Modes**:
  - **Hinglish (Roman)**: Preserves Hindi words in Roman script
  - **English**: Translates everything to English
- ⌨️ **Global Hotkey** - `Ctrl+Space` to start/stop recording
- 📋 **Auto-Paste** - Transcribed text automatically pastes at cursor
- 🔴 **Visual Feedback** - Icon changes color when recording
- ⏱️ **Long Recordings** - Up to 5 minutes per session
- 💾 **Settings Persistence** - Remembers your API key and preferences

## 🚀 Quick Start

### Prerequisites
- Windows 10/11
- Python 3.8+
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mvijay24/whisper-paste.git
   cd whisper-paste
   ```

2. **Install dependencies**
   ```batch
   setup.bat
   ```

3. **Run the application**
   ```batch
   start_silent.vbs
   ```
   Or simply double-click `start_silent.vbs` for completely silent startup!

4. **Set your API key**
   - Right-click the tray icon
   - Select "🔑 Set API Key..."
   - Enter your OpenAI API key
   - Click Save

## 📖 Usage

1. **Look for the mic icon** in your system tray (near clock)
2. **Right-click the icon** to access settings:
   - Set/Update API Key
   - Choose output mode (Hinglish or English)
3. **Press `Ctrl+Space`** to start recording
4. **Speak** in Hindi, English, or Hinglish
5. **Press `Ctrl+Space`** again to stop
6. **Text automatically pastes** at your cursor position!

### Menu Options

- **🔑 Set API Key...** - Add or update your OpenAI API key
- **API Status** - Shows connection status (✓ Connected or ⚠️ No API Key)
- **📝 Output Mode** - Choose between Hinglish (Roman) or English
- **🐛 Enable and Display Debug Panel** - Shows real-time execution logs
- **📊 Session Log Summary** - Shows detailed report after each recording
- **Exit** - Properly closes the application

### Examples

**Hinglish Mode:**
- You say: "Bhai ye file jaldi bhej de"
- Output: `bhai ye file jaldi bhej de`

**English Mode:**
- You say: "Bhai ye file jaldi bhej de"
- Output: `brother send this file quickly`

## 🛠️ Building Executable

To create a standalone `.exe` file:

```batch
build.bat
```

The executable will be created in the `dist` folder.

## 📁 Project Structure

```
whisper-paste/
├── whisper_tray.pyw      # Main application (no console window)
├── start_silent.vbs      # Silent launcher
├── start.bat            # Standard launcher
├── restart.bat          # Kill old instances & restart
├── setup.bat            # Install dependencies
├── build.bat            # Build executable
├── icon.ico             # Application icon
├── settings.json        # Saved settings (auto-created)
└── README.md            # This file
```

## ⚙️ Configuration

Settings are automatically saved in `settings.json`:
```json
{
  "output_mode": "hinglish",
  "api_key": "sk-..."
}
```

## 🔧 Troubleshooting

**Can't see the tray icon?**
- Click "Show hidden icons" arrow in system tray
- Use `restart.bat` to kill old instances

**API Key issues?**
- Ensure you have a valid OpenAI API key
- Check your API usage limits at [OpenAI Dashboard](https://platform.openai.com/usage)

**No audio recorded?**
- Check microphone permissions in Windows Settings
- Ensure default microphone is set correctly

**Text not pasting or cursor errors?**
- **Close clipboard managers** like BeefText, Ditto, or ClipboardFusion - they interfere with paste functionality
- Disable any text expander software temporarily
- If you see "[WinError 1402] Invalid cursor handle", it's likely due to clipboard manager interference

## 💰 Cost

- Uses OpenAI's Whisper API
- Approximately $0.006 per minute of audio
- See [OpenAI Pricing](https://openai.com/pricing)

## 💡 Why "Toast"?

The small popup notification that shows transcribed text is called a "toast" because:
- It "pops up" like bread from a toaster
- It appears briefly and then disappears
- Common UI term from Android/Windows for temporary notifications
- Shows at the corner of the screen without interrupting workflow

## 🤝 Contributing

Feel free to open issues or submit pull requests!

## 📜 License

MIT License - feel free to use this in your projects!

## 🙏 Acknowledgments

- OpenAI for the amazing Whisper API
- The Python community for excellent libraries
- Special thanks to the Hinglish-speaking community!

---

Made with ❤️ for the Hinglish-speaking developers!