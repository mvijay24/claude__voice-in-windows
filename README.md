# 🎤 Whisper Paste - Hinglish Voice Transcription

A lightweight Windows system tray application that converts speech to text using OpenAI's Whisper API. Perfect for code-switching between Hindi and English!

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- 🔵 **System Tray Application** - Runs silently in background
- 🎯 **Two Output Modes**:
  - **Hinglish (Roman)**: Preserves Hindi words in Roman script
  - **English**: Translates everything to English
- ⌨️ **Global Hotkey** - `Ctrl+Space` to start/stop recording
- 📋 **Auto-Paste** - Transcribed text automatically pastes at cursor
- 🔴 **Visual Feedback** - Icon changes color when recording
- ⏱️ **Long Recordings** - Up to 5 minutes per session
- 💾 **Settings Persistence** - Remembers your output mode preference

## 🚀 Quick Start

### Prerequisites
- Windows 10/11
- Python 3.8+
- OpenAI API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/whisper-paste.git
   cd whisper-paste
   ```

2. **Install dependencies**
   ```batch
   setup.bat
   ```

3. **Add your OpenAI API key**
   - Open `whisper_tray.pyw`
   - Replace `YOUR_API_KEY_HERE` with your actual OpenAI API key

4. **Run the application**
   ```batch
   start_silent.vbs
   ```
   Or simply double-click `start_silent.vbs` for completely silent startup!

## 📖 Usage

1. **Look for the mic icon** in your system tray (near clock)
2. **Press `Ctrl+Space`** to start recording
3. **Speak** in Hindi, English, or Hinglish
4. **Press `Ctrl+Space`** again to stop
5. **Text automatically pastes** at your cursor position!

### Changing Output Mode

Right-click the tray icon and select your preferred output mode:
- ✓ **Hinglish (Roman)** - Default, preserves Hindi words
- **English** - Translates to English

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
└── README.md            # This file
```

## ⚙️ Configuration

The app saves settings in `settings.json`:
```json
{
  "output_mode": "hinglish"  // or "english"
}
```

## 🔧 Troubleshooting

**Can't see the tray icon?**
- Click "Show hidden icons" arrow in system tray
- Use `restart.bat` to kill old instances

**API Key issues?**
- Ensure you have a valid OpenAI API key
- Check your API usage limits

**No audio recorded?**
- Check microphone permissions in Windows Settings
- Ensure default microphone is set correctly

## 💰 Cost

- Uses OpenAI's Whisper API
- Approximately $0.006 per minute of audio
- See [OpenAI Pricing](https://openai.com/pricing)

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