# Hybrid Emotion Detection - Testing Guide

## 🎯 What Was Implemented

A **hybrid emotion detection system** that combines:
- **Audio emotion** (70% weight) - MSP-PODCAST wav2vec2 model
- **Text sentiment** (30% weight) - BERT boltuix/bert-emotion model
- **Zero LLM tokens** - All processing is local
- **Mismatch detection** - Identifies sarcasm, politeness masking, etc.

## 🚀 Quick Start

### 1. Restart the Server

```bash
cd "/Users/apple/Desktop/nester ai bot opensource"
./restart_server.sh
```

### 2. Look for Initialization Logs

When the server starts, you should see:

```
ToneAwareProcessor HYBRID (Audio 70% + Text 30%): MSP-PODCAST, conf=0.25, buffer=1000ms, stability=2, cooldown=2.0s
```

✅ If you see "HYBRID (Audio 70% + Text 30%)" - **Hybrid mode is enabled**
❌ If you see "AUDIO-ONLY" - Hybrid mode is disabled

## 📊 What to Look for in Logs

### Every 1 Second During Conversation

Look for these log patterns:

#### **Pattern 1: Hybrid Mode Processing**
```
🔄 HYBRID MODE: Processing audio + text (transcript: 'Hello, how are you...')
```
This means the system is combining both audio and text.

#### **Pattern 2: Hybrid Results (Detailed)**
```
🎯 HYBRID RESULT:
  Primary Emotion: frustrated (confidence: 78%)
  Audio: frustrated (82%) × 70%
  Text:  neutral (70%) × 30%
  Mismatch: True User masking frustration with polite language
  Fused A/V/D: 0.72/0.36/0.58
  Tokens Used: 0
```

**How to Read This:**
- **Primary Emotion**: Final detected emotion (after fusion)
- **Audio**: Emotion from voice tone + weight applied
- **Text**: Emotion from word choice + weight applied
- **Mismatch**: Detected if audio ≠ text (sarcasm, masking)
- **Fused A/V/D**: Combined Arousal/Valence/Dominance scores
- **Tokens Used**: Should always be 0 (BERT runs locally)

#### **Pattern 3: Audio-Only Mode (If Hybrid Disabled)**
```
🎤 AUDIO-ONLY MODE: Processing audio emotion
🎤 AUDIO-ONLY RESULT: frustrated (confidence: 82%, A=0.75, V=0.35)
```

If you see this, hybrid mode is NOT active.

## 🧪 Test Scenarios

### Test 1: Aligned Emotions
**Say**: "This is really frustrating me!"
**Expected**:
```
Audio: frustrated (high arousal, negative valence)
Text:  frustrated (keyword "frustrating")
Primary: frustrated
Mismatch: False
```

### Test 2: Polite Masking (Mismatch)
**Say** (with annoyed tone): "Thank you for your help"
**Expected**:
```
Audio: frustrated (tense voice)
Text:  neutral (polite words)
Primary: frustrated (audio gets 70% weight)
Mismatch: True - "User masking frustration with polite language"
```

### Test 3: Excited but Brief
**Say** (enthusiastically): "Okay, got it!"
**Expected**:
```
Audio: excited (high arousal, positive valence)
Text:  neutral (brief acknowledgment)
Primary: excited
Mismatch: True - "User enthusiastic but using brief language"
```

### Test 4: Low Audio Confidence (Noisy)
**Say** (in noisy environment): "This damn thing isn't working!"
**Expected**:
```
Audio: neutral (low confidence due to noise)
Text:  frustrated (strong keywords)
Weights adjusted: 40% audio, 60% text
Primary: frustrated (text dominates)
```

## 📈 Log Monitoring Commands

### Real-time Hybrid Logs Only
```bash
tail -f logs/app.log | grep "HYBRID"
```

### See Emotion Results Only
```bash
tail -f logs/app.log | grep "HYBRID RESULT"
```

### Count Mismatch Detections
```bash
grep "Mismatch: True" logs/app.log | wc -l
```

### See Weight Adjustments
```bash
grep "Audio weight:" logs/app.log
```

## 🔧 Configuration

### Enable/Disable Hybrid Mode

In `app/core/voice_assistant.py`, find the ToneAwareProcessor initialization:

```python
tone_aware_processor = ToneAwareProcessor(
    tts_service=tts_service,
    use_hybrid_mode=True,  # Set to False for audio-only
    cooldown_seconds=2.0,
    enabled=True
)
```

### Adjust Weights

In `app/services/hybrid_emotion_detector.py`:

```python
HybridEmotionDetector(
    default_audio_weight=0.7,  # 70% audio (change this)
    default_text_weight=0.3,   # 30% text (change this)
    mismatch_threshold=0.8     # Mismatch sensitivity
)
```

## ✅ Success Checklist

- [ ] Server starts with "HYBRID (Audio 70% + Text 30%)" log
- [ ] Every 1 second you see "🔄 HYBRID MODE: Processing audio + text"
- [ ] You see "🎯 HYBRID RESULT" with audio and text breakdowns
- [ ] Tokens Used is always 0
- [ ] Mismatch detection works (test with sarcastic tone)
- [ ] Weights adjust based on confidence (test in noisy environment)

## 🐛 Troubleshooting

### Problem: Still seeing "AUDIO-ONLY MODE"
**Solution**: Check if `use_hybrid_mode=True` in ToneAwareProcessor initialization

### Problem: "ModuleNotFoundError: No module named 'transformers'"
**Solution**: Install dependencies:
```bash
pip install transformers torch
```

### Problem: BERT model downloading
**First run**: BERT model (boltuix/bert-emotion ~440MB) will download automatically
**Location**: `~/.cache/huggingface/hub/`

### Problem: High latency
**Check**: BERT should process text in 20-50ms
**If slow**: Ensure torch is using CPU efficiently (no GPU needed for BERT)

## 📞 Support

If logs show hybrid mode is working, you should see:
1. Both audio and text emotions calculated
2. Weights applied (default 70/30)
3. Mismatch detection when appropriate
4. Zero tokens used

**Test it now!** Speak into the system and watch the logs. 🎤
