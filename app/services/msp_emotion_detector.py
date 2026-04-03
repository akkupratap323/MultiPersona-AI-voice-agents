"""
MSP-PODCAST Emotion Detection Service

Uses wav2vec2-large-robust trained on MSP-PODCAST for natural conversational speech emotion detection.
This model outputs dimensional emotions (arousal, dominance, valence) which are better suited
for real podcast/conversational speech than categorical models trained on acted speech.

Model: audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim
Training data: MSP-Podcast v1.7 (real podcast conversations)

Output dimensions (0-1 scale):
- Arousal: Low (calm) to High (excited/energetic)
- Dominance: Low (submissive) to High (dominant/confident)
- Valence: Low (negative/sad) to High (positive/happy)

Emotion mapping strategy:
- High arousal + low valence = frustrated/angry
- High arousal + high valence = excited/happy
- Low arousal + low valence = sad
- Low arousal + high valence = calm/neutral

OPTIMIZATIONS for 4GB RAM / 2 vCPU:
- INT8 Dynamic Quantization: 2-3x faster inference, 75% smaller model
- Thread Tuning: Optimized for 2 vCPU (prevents over-threading)
- Inference Mode: Faster than no_grad, no tensor tracking
- Periodic GC: Prevents memory fragmentation
"""

import os
import gc
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional
from dataclasses import dataclass

import torch
import torch.nn as nn
import numpy as np
from loguru import logger

# ===== CPU OPTIMIZATIONS FOR 2 vCPU LIGHTSAIL =====
# Set thread count BEFORE any torch operations
# 2 threads = match vCPU count, prevents CPU thrashing
torch.set_num_threads(2)
torch.set_num_interop_threads(1)  # Reduce inter-op parallelism overhead

# Enable Intel MKL-DNN optimizations (Lightsail uses Intel Xeon)
if hasattr(torch.backends, 'mkldnn'):
    torch.backends.mkldnn.enabled = True

logger.debug(
    f"PyTorch CPU config: threads={torch.get_num_threads()}, "
    f"interop={torch.get_num_interop_threads()}, "
    f"mkldnn={getattr(torch.backends, 'mkldnn', None) and torch.backends.mkldnn.enabled}"
)

# Lazy load model
_model = None
_processor = None
_model_loading = False
_model_quantized = False  # Track if model has been quantized


class RegressionHead(nn.Module):
    """Regression head for dimensional emotion prediction."""

    def __init__(self, config):
        super().__init__()
        self.dense = nn.Linear(config.hidden_size, config.hidden_size)
        self.dropout = nn.Dropout(config.final_dropout)
        self.out_proj = nn.Linear(config.hidden_size, config.num_labels)

    def forward(self, features, **kwargs):
        x = features
        x = self.dropout(x)
        x = self.dense(x)
        x = torch.tanh(x)
        x = self.dropout(x)
        x = self.out_proj(x)
        return x


def get_msp_model():
    """Get or initialize the MSP-PODCAST emotion model (lazy loading).

    OPTIMIZATIONS APPLIED:
    1. INT8 Dynamic Quantization: 2-3x faster inference, 75% smaller model size
    2. Eval mode: Disables dropout/batchnorm training behavior
    3. CPU placement: Explicit CPU placement for Lightsail
    """
    global _model, _processor, _model_loading, _model_quantized

    if _model is not None and _processor is not None:
        logger.debug("MSP model cache hit")
        return _model, _processor

    if _model_loading:
        logger.error(
            "get_msp_model: _model_loading=True but model is None — "
            "loading flag was not reset after a previous failed load. "
            "Emotion detection is disabled for this session."
        )
        return None, None

    _model_loading = True
    logger.info("🚀 Starting MSP-PODCAST model initialization...")

    try:
        logger.info("📦 Importing transformers library...")
        from transformers import Wav2Vec2Processor
        from transformers.models.wav2vec2.modeling_wav2vec2 import (
            Wav2Vec2Model,
            Wav2Vec2PreTrainedModel,
        )
        logger.info("✅ Transformers imported successfully")

        # Define the EmotionModel class
        class EmotionModel(Wav2Vec2PreTrainedModel):
            """Wav2Vec2 model with regression head for dimensional emotions."""

            # Required for transformers >=4.40 and >=5.x
            _tied_weights_keys = []
            all_tied_weights_keys = {}

            def __init__(self, config):
                super().__init__(config)
                self.config = config
                self.wav2vec2 = Wav2Vec2Model(config)
                self.classifier = RegressionHead(config)
                self.init_weights()

            def forward(self, input_values):
                outputs = self.wav2vec2(input_values)
                hidden_states = outputs[0]
                hidden_states = torch.mean(hidden_states, dim=1)
                logits = self.classifier(hidden_states)
                return hidden_states, logits

        model_name = "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim"
        logger.info(f"📥 Loading MSP-PODCAST emotion model: {model_name}")
        logger.info("   (First load may take ~60s, subsequent loads use cache)")

        _processor = Wav2Vec2Processor.from_pretrained(model_name)
        _model = EmotionModel.from_pretrained(model_name)
        _model.eval()
        _model = _model.to("cpu")

        original_size = sum(p.numel() * p.element_size() for p in _model.parameters()) / 1e6

        # ===== INT8 DYNAMIC QUANTIZATION (Optional) =====
        # Converts FP32 weights to INT8 at runtime
        # Benefits: 2-3x faster inference, 75% smaller memory footprint
        # NOTE: Not supported on Apple Silicon (M1/M2/M3) - skip gracefully
        import platform
        is_arm = platform.machine() in ('arm64', 'aarch64')

        if is_arm:
            logger.info("⚠️ Skipping INT8 quantization (not supported on Apple Silicon)")
            logger.info(f"✅ MSP-PODCAST model loaded (FP32, ~{original_size:.0f}MB)")
            _model_quantized = False
        else:
            try:
                logger.info("🔧 Applying INT8 dynamic quantization...")
                _model = torch.quantization.quantize_dynamic(
                    _model,
                    {torch.nn.Linear},  # Quantize Linear layers (main compute)
                    dtype=torch.qint8
                )
                _model_quantized = True
                quantized_size = original_size * 0.3  # ~70% reduction for Linear layers
                logger.info(f"✅ MSP-PODCAST model loaded and optimized:")
                logger.info(f"   Original size: ~{original_size:.0f}MB")
                logger.info(f"   Quantized size: ~{quantized_size:.0f}MB (INT8)")
                logger.info(f"   Speed improvement: 2-3x faster inference")
            except RuntimeError as e:
                logger.warning(f"⚠️ INT8 quantization failed ({e}), using FP32 model")
                _model_quantized = False
                logger.info(f"✅ MSP-PODCAST model loaded (FP32, ~{original_size:.0f}MB)")
        
        # Force garbage collection after model load
        gc.collect()

        _model_loading = False
        return _model, _processor

    except ImportError as e:
        logger.error(f"❌ Failed to import transformers for MSP-PODCAST: {e}")
        logger.error("   Make sure 'transformers' and 'torch' are installed")
        _model_loading = False
        return None, None
    except Exception as e:
        logger.error(f"❌ Failed to load MSP-PODCAST model: {e}")
        import traceback
        traceback.print_exc()
        _model_loading = False
        return None, None


# Emotion mapping thresholds
# Based on dimensional emotion research:
# - Arousal > 0.55 = high energy
# - Valence > 0.55 = positive, < 0.45 = negative
# - Dominance > 0.55 = confident

DEFAULT_TONE = "neutral"


@dataclass
class MSPEmotionResult:
    """Result from MSP-PODCAST dimensional emotion detection."""
    arousal: float      # 0-1: calm to excited
    dominance: float    # 0-1: submissive to dominant
    valence: float      # 0-1: negative to positive
    emotion: str        # Mapped categorical emotion
    tone: str           # Our voice tone mapping
    confidence: float   # Confidence based on dimension clarity
    timestamp: float    # When detection occurred


def map_dimensions_to_emotion(arousal: float, dominance: float, valence: float) -> tuple:
    """Map dimensional emotions to categorical emotion and tone.

    Args:
        arousal: Energy level (0=calm, 1=excited)
        dominance: Confidence level (0=submissive, 1=dominant)
        valence: Positivity (0=negative, 1=positive)

    Returns:
        Tuple of (emotion, tone, confidence)
    """
    # Calculate confidence based on how clearly the emotion dimensions stand out
    # Higher confidence when values are more extreme (not near 0.5)
    arousal_clarity = abs(arousal - 0.5) * 2
    valence_clarity = abs(valence - 0.5) * 2
    confidence = (arousal_clarity + valence_clarity) / 2

    # Thresholds for emotion mapping
    HIGH_AROUSAL = 0.55
    LOW_AROUSAL = 0.45
    HIGH_VALENCE = 0.55
    LOW_VALENCE = 0.45

    # Map to emotions based on arousal-valence quadrants
    if arousal > HIGH_AROUSAL:
        if valence > HIGH_VALENCE:
            # High arousal + positive = excited/happy
            emotion = "happy"
            tone = "excited"
        else:
            # High arousal + negative = angry/frustrated
            emotion = "angry"
            tone = "frustrated"
    elif arousal < LOW_AROUSAL:
        if valence < LOW_VALENCE:
            # Low arousal + negative = sad
            emotion = "sad"
            tone = "sad"
        else:
            # Low arousal + positive = calm/relaxed
            emotion = "calm"
            tone = "neutral"
    else:
        # Medium arousal - check valence
        if valence > HIGH_VALENCE:
            emotion = "content"
            tone = "neutral"
        elif valence < LOW_VALENCE:
            emotion = "worried"
            tone = "sad"
        else:
            emotion = "neutral"
            tone = "neutral"

    return emotion, tone, confidence


class MSPEmotionDetector:
    """Emotion detection using wav2vec2 trained on MSP-PODCAST.

    Better for natural conversational speech than acted speech models.
    Outputs dimensional emotions (arousal, dominance, valence) then maps to tones.

    Attributes:
        model: Wav2Vec2 EmotionModel
        processor: Wav2Vec2Processor
        enabled: Whether detection is available
        last_result: Most recent emotion detection result
    """

    # Shared thread pool for CPU-bound inference (1 worker to avoid CPU thrashing)
    _executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="msp-emotion")

    def __init__(self):
        """Initialize the MSP-PODCAST emotion detector."""
        self.enabled = True
        self.is_connected = False
        self.model = None
        self.processor = None
        self.device = "cpu"

        # Result tracking
        self.last_result: Optional[MSPEmotionResult] = None

        # Inference counter for periodic GC
        self._inference_count: int = 0

        logger.info("MSP-PODCAST emotion detector initialized (model loads on first use)")

    async def connect(self) -> bool:
        """Initialize the MSP-PODCAST model.

        Returns:
            True if initialization successful, False otherwise
        """
        logger.info(
            f"[EMOTION-DIAG] MSP-PODCAST connect() called. "
            f"Current state: model={self.model is not None}, processor={self.processor is not None}, "
            f"is_connected={self.is_connected}, _model_loading={_model_loading}"
        )
        try:
            self.model, self.processor = get_msp_model()
            if self.model is not None and self.processor is not None:
                self.is_connected = True
                logger.info(
                    f"[EMOTION-DIAG] MSP-PODCAST connect() SUCCESS. "
                    f"model={type(self.model).__name__}, is_connected={self.is_connected}"
                )
                return True
            else:
                self.is_connected = False
                logger.error(
                    f"[EMOTION-DIAG] MSP-PODCAST connect() FAILED - get_msp_model() returned None! "
                    f"_model_loading={_model_loading} (if True, this is the bug - flag stuck)"
                )
                return False
        except Exception as e:
            logger.error(f"[EMOTION-DIAG] MSP-PODCAST connect() EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        """Clean up resources."""
        self.is_connected = False
        logger.info("MSP-PODCAST detector disconnected")

    def _process_audio_sync(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000
    ) -> Optional[MSPEmotionResult]:
        """Synchronous CPU-bound inference — runs in thread pool executor.

        Kept off the asyncio event loop so audio output frames are never blocked.
        """
        try:
            # Convert bytes to numpy array (16-bit PCM)
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
            audio_np = audio_np / 32768.0  # Normalize to [-1, 1]

            # Resample to 16kHz if needed
            if sample_rate != 16000:
                import librosa
                audio_np = librosa.resample(audio_np, orig_sr=sample_rate, target_sr=16000)

            # Process through feature extractor
            inputs = self.processor(
                audio_np,
                sampling_rate=16000,
                return_tensors="pt",
                padding=True
            )

            # Run inference with OPTIMIZED inference_mode
            # inference_mode is faster than no_grad (no tensor version tracking)
            with torch.inference_mode():
                input_values = inputs['input_values'].to(self.device)
                _, logits = self.model(input_values)

                # Get predictions (arousal, dominance, valence)
                predictions = logits[0].cpu().numpy()

            arousal = float(predictions[0])
            dominance = float(predictions[1])
            valence = float(predictions[2])

            # Map to emotion and tone
            emotion, tone, confidence = map_dimensions_to_emotion(arousal, dominance, valence)

            result = MSPEmotionResult(
                arousal=arousal,
                dominance=dominance,
                valence=valence,
                emotion=emotion,
                tone=tone,
                confidence=confidence,
                timestamp=time.time()
            )

            self.last_result = result

            # Increment inference counter for periodic GC
            self._inference_count += 1

            # Periodic garbage collection every 10 inferences
            # Prevents memory fragmentation on constrained 4GB instance
            if self._inference_count % 10 == 0:
                gc.collect()
                logger.debug(f"🧹 GC after {self._inference_count} inferences")

            # Log detection
            logger.info(
                f"MSP: A={arousal:.2f} D={dominance:.2f} V={valence:.2f} -> "
                f"{emotion}({confidence:.0%}) -> {tone}"
            )

            return result

        except Exception as e:
            logger.error(f"MSP-PODCAST processing error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def process_audio(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000
    ) -> Optional[MSPEmotionResult]:
        """Process audio chunk and detect dimensional emotions.

        Offloads CPU-heavy inference (numpy, librosa, torch) to a thread pool
        executor so the asyncio event loop stays free for audio output frames.

        Args:
            audio_bytes: Raw PCM audio bytes (16-bit, mono)
            sample_rate: Audio sample rate (default 16000 Hz)

        Returns:
            MSPEmotionResult with arousal/dominance/valence and mapped tone, or None if failed
        """
        if not self.enabled or not self.is_connected or self.model is None:
            logger.debug(
                f"[EMOTION-DIAG] process_audio early return: "
                f"enabled={self.enabled}, is_connected={self.is_connected}, "
                f"model_loaded={self.model is not None}"
            )
            return None

        # Need at least 0.5 seconds of audio for meaningful detection
        min_bytes = int(sample_rate * 2 * 0.5)
        if len(audio_bytes) < min_bytes:
            logger.debug(
                f"[EMOTION-DIAG] process_audio: buffer too short "
                f"({len(audio_bytes)} < {min_bytes} bytes)"
            )
            return None

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self._process_audio_sync,
            audio_bytes,
            sample_rate,
        )

    def reset(self) -> None:
        """Reset detector state."""
        self.last_result = None
        self._inference_count = 0
        gc.collect()  # Clean up on reset
        logger.info("MSP-PODCAST emotion detector reset")

    def get_stats(self) -> Dict:
        """Get detector statistics."""
        return {
            "enabled": self.enabled,
            "connected": self.is_connected,
            "model_loaded": self.model is not None,
            "model_quantized": _model_quantized,
            "inference_count": self._inference_count,
            "torch_threads": torch.get_num_threads(),
            "last_arousal": self.last_result.arousal if self.last_result else None,
            "last_dominance": self.last_result.dominance if self.last_result else None,
            "last_valence": self.last_result.valence if self.last_result else None,
            "last_emotion": self.last_result.emotion if self.last_result else None,
            "last_tone": self.last_result.tone if self.last_result else None,
            "last_confidence": self.last_result.confidence if self.last_result else None,
        }


# Global instance
_msp_detector: Optional[MSPEmotionDetector] = None


def get_msp_detector() -> MSPEmotionDetector:
    """Get or create the global MSP-PODCAST detector instance."""
    global _msp_detector
    if _msp_detector is None:
        _msp_detector = MSPEmotionDetector()
    return _msp_detector


async def init_msp_detector() -> bool:
    """Initialize and connect the global MSP-PODCAST detector.

    Returns:
        True if initialization successful
    """
    detector = get_msp_detector()
    return await detector.connect()
