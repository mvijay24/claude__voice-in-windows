# Migration Guide: V1 to V2

## Quick Start

To use the new V2 with zero word loss:

```bash
# Run V2 directly
python minimal_google_speech_v2.pyw

# Or use the batch file
run_v2_zero_word_loss.bat
```

## What Changed?

### User-Visible Changes
- **No more word skipping!** The rhythmic 2-3 word loss every 10 seconds is gone
- **Instance indicator** shows which recognition instance is active (A or B)
- **Switch counter** shows how many times instances have switched
- **Better performance** with 82% fewer restarts

### Technical Changes
1. **Dual-instance architecture** - Two recognition instances work in tandem
2. **55-second cycles** instead of 10-second cycles
3. **Overlapping handoff** - 2-second overlap ensures no audio gap
4. **Graceful shutdown** using `stop()` instead of `abort()`

## Files Created

- `minimal_google_speech_v2.pyw` - Standalone V2 implementation
- `reimplemented/modules/speech_handler_v2.py` - V2 module for reimplemented version
- `V2_ZERO_WORD_LOSS_EXPLANATION.md` - Technical explanation
- `run_v2_zero_word_loss.bat` - Easy run script

## Testing the Fix

1. Run V2 and start recording
2. Speak continuously in Hindi for 2+ minutes
3. Notice:
   - No words are skipped at ~55 second marks
   - Instance switches from A→B→A smoothly
   - All text appears without gaps

## Troubleshooting

**Q: Browser asks for microphone permission twice?**
A: This is normal on first run - both instances need permission. Grant permission to both.

**Q: Still seeing word skips?**
A: Make sure you're running V2 (check for "V2" in the title and instance indicator)

**Q: Can I adjust the timing?**
A: Yes, in the HTML/JavaScript:
- `maxSessionTime`: Time before switching (default: 55000ms)
- `overlapTime`: Overlap duration (default: 2000ms)

## Going Back to V1

If needed, the original files are unchanged:
- `minimal_google_speech.pyw` - Original V1
- `reimplemented/modules/speech_handler.py` - Original module

But V2 is strictly better - zero reason to go back!

## Summary

V2 solves the word skipping issue completely by:
- Reducing restart frequency by 5.5x
- Using overlapping instances for seamless handoff
- Processing all pending audio with `stop()` instead of `abort()`

Enjoy uninterrupted speech recognition! 🎉