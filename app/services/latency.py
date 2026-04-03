"""Latency Analysis Service for Voice Assistant.

This module provides comprehensive latency tracking and analysis for voice interactions,
measuring performance at each stage of the pipeline.
"""

import json
import statistics
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from loguru import logger
from pipecat.frames.frames import (
    Frame,
    AudioRawFrame,
    TranscriptionFrame,
    TextFrame,
    TTSStartedFrame,
    TTSAudioRawFrame,
    StartFrame
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


@dataclass
class LatencyMetrics:
    """Container for latency measurements of a single interaction."""
    interaction_id: str
    start_time: float = 0.0
    audio_received_time: float = 0.0
    transcription_start_time: float = 0.0
    transcription_complete_time: float = 0.0
    llm_start_time: float = 0.0
    llm_complete_time: float = 0.0
    tts_start_time: float = 0.0
    tts_complete_time: float = 0.0
    audio_output_time: float = 0.0
    end_time: float = 0.0

    # Calculated metrics
    stt_latency: float = 0.0
    llm_latency: float = 0.0
    tts_latency: float = 0.0
    total_latency: float = 0.0
    voice_to_voice_latency: float = 0.0

    def calculate_latencies(self):
        """Calculate latency metrics from timestamps."""
        if self.transcription_start_time > 0 and self.transcription_complete_time > 0:
            self.stt_latency = (self.transcription_complete_time - self.transcription_start_time) * 1000

        if self.llm_start_time > 0 and self.llm_complete_time > 0:
            self.llm_latency = (self.llm_complete_time - self.llm_start_time) * 1000
        elif self.transcription_complete_time > 0 and self.llm_complete_time > 0:
            # If no explicit LLM start time, use transcription completion as start
            self.llm_latency = (self.llm_complete_time - self.transcription_complete_time) * 1000

        if self.tts_start_time > 0 and self.tts_complete_time > 0:
            self.tts_latency = (self.tts_complete_time - self.tts_start_time) * 1000

        if self.start_time > 0 and self.end_time > 0:
            self.total_latency = (self.end_time - self.start_time) * 1000

        # Calculate voice-to-voice latency from transcription to audio output
        if self.transcription_complete_time > 0 and self.audio_output_time > 0:
            self.voice_to_voice_latency = (self.audio_output_time - self.transcription_complete_time) * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging/analysis."""
        return {
            "interaction_id": self.interaction_id,
            "stt_latency_ms": round(self.stt_latency, 2),
            "llm_latency_ms": round(self.llm_latency, 2),
            "tts_latency_ms": round(self.tts_latency, 2),
            "total_latency_ms": round(self.total_latency, 2),
            "voice_to_voice_latency_ms": round(self.voice_to_voice_latency, 2),
            "timestamps": {
                "start": self.start_time,
                "audio_received": self.audio_received_time,
                "transcription_start": self.transcription_start_time,
                "transcription_complete": self.transcription_complete_time,
                "llm_start": self.llm_start_time,
                "llm_complete": self.llm_complete_time,
                "tts_start": self.tts_start_time,
                "tts_complete": self.tts_complete_time,
                "audio_output": self.audio_output_time,
                "end": self.end_time
            }
        }


class LatencyAnalyzer(FrameProcessor):
    """Frame processor that tracks latency metrics for voice interactions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_interactions: Dict[str, LatencyMetrics] = {}
        self.completed_interactions: List[LatencyMetrics] = []
        self.interaction_counter = 0

        # Interaction grouping variables
        self.last_audio_time = 0
        self.current_interaction_id = None
        self.interaction_timeout = 2.0  # 2 seconds timeout between interactions

        # Statistics tracking
        self.stats = {
            "total_interactions": 0,
            "average_latencies": {},
            "min_latencies": {},
            "max_latencies": {},
            "p95_latencies": {},
            "p99_latencies": {}
        }

        logger.info("Latency Analyzer initialized")

    def _generate_interaction_id(self) -> str:
        """Generate a unique interaction ID."""
        self.interaction_counter += 1
        return f"interaction_{self.interaction_counter}_{int(time.time() * 1000)}"

    def _get_or_create_interaction(self, interaction_id: Optional[str] = None) -> LatencyMetrics:
        """Get existing interaction or create new one."""
        if interaction_id is None:
            interaction_id = self._generate_interaction_id()

        if interaction_id not in self.current_interactions:
            self.current_interactions[interaction_id] = LatencyMetrics(
                interaction_id=interaction_id,
                start_time=time.time()
            )

        return self.current_interactions[interaction_id]

    def _complete_interaction(self, interaction_id: str):
        """Mark interaction as complete and calculate final metrics."""
        if interaction_id in self.current_interactions:
            metrics = self.current_interactions[interaction_id]
            metrics.end_time = time.time()
            metrics.calculate_latencies()

            # Log the completed interaction
            self._log_interaction_metrics(metrics)

            # Move to completed list
            self.completed_interactions.append(metrics)
            del self.current_interactions[interaction_id]

            # Reset current interaction tracking
            if self.current_interaction_id == interaction_id:
                self.current_interaction_id = None

            # Update statistics
            self._update_statistics()

    def _log_interaction_metrics(self, metrics: LatencyMetrics):
        """Log detailed metrics for a completed interaction."""
        logger.info(f"🔍 Latency Analysis - Interaction {metrics.interaction_id}")
        logger.info(f"  📊 Voice-to-Voice: {metrics.voice_to_voice_latency:.2f}ms")
        logger.info(f"  🎤 Speech-to-Text: {metrics.stt_latency:.2f}ms")
        logger.info(f"  🧠 LLM Processing: {metrics.llm_latency:.2f}ms")
        logger.info(f"  🔊 Text-to-Speech: {metrics.tts_latency:.2f}ms")
        logger.info(f"  ⏱️ Total Latency: {metrics.total_latency:.2f}ms")

        # Also log as structured data for analysis
        logger.info(f"LATENCY_METRICS: {json.dumps(metrics.to_dict())}")

    def _update_statistics(self):
        """Update overall statistics from completed interactions."""
        if not self.completed_interactions:
            return

        self.stats["total_interactions"] = len(self.completed_interactions)

        # Extract latency values
        latency_types = ['stt_latency', 'llm_latency', 'tts_latency', 'total_latency', 'voice_to_voice_latency']

        for latency_type in latency_types:
            values = [getattr(interaction, latency_type) for interaction in self.completed_interactions
                      if getattr(interaction, latency_type) > 0]

            if values:
                self.stats["average_latencies"][latency_type] = statistics.mean(values)
                self.stats["min_latencies"][latency_type] = min(values)
                self.stats["max_latencies"][latency_type] = max(values)

                # Calculate percentiles
                sorted_values = sorted(values)
                n = len(sorted_values)
                if n >= 20:  # Only calculate percentiles with sufficient data
                    self.stats["p95_latencies"][latency_type] = sorted_values[int(0.95 * n)]
                    self.stats["p99_latencies"][latency_type] = sorted_values[int(0.99 * n)]

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames and track latency metrics."""

        # Handle StartFrame specially - just pass it through immediately
        if isinstance(frame, StartFrame):
            await super().process_frame(frame, direction)
            return

        # For all other frames, call parent's process_frame to handle framework requirements
        await super().process_frame(frame, direction)

        # Handle different frame types for latency tracking
        if isinstance(frame, TranscriptionFrame):
            # Speech-to-text completion - start of new interaction
            current_time = time.time()

            # Check if we need to start a new interaction based on timeout
            if (self.current_interaction_id is None or
                    (current_time - self.last_audio_time) > self.interaction_timeout):
                # Start new interaction
                interaction = self._get_or_create_interaction()
                interaction.transcription_complete_time = current_time
                self.current_interaction_id = interaction.interaction_id
                logger.debug(f"🎤 New interaction started - {interaction.interaction_id}: '{frame.text}'")

            # Update last audio time for timeout tracking
            self.last_audio_time = current_time

        elif isinstance(frame, AudioRawFrame):
            if direction == FrameDirection.UPSTREAM:
                # Bot audio output - near end of interaction
                if self.current_interaction_id and self.current_interaction_id in self.current_interactions:
                    interaction = self.current_interactions[self.current_interaction_id]
                    if interaction.audio_output_time == 0:
                        interaction.audio_output_time = time.time()
                        logger.debug(f"🔊 Audio output started - {interaction.interaction_id}")

            # Note: TranscriptionFrame already handled above as interaction starter

        elif isinstance(frame, TextFrame):
            # LLM response or TTS input
            if self.current_interaction_id and self.current_interaction_id in self.current_interactions:
                interaction = self.current_interactions[self.current_interaction_id]

                # Check if this is from LLM (first text frame after transcription)
                if interaction.llm_complete_time == 0:
                    interaction.llm_complete_time = time.time()
                    logger.debug(f"🧠 LLM response complete - {interaction.interaction_id}")

        elif isinstance(frame, TTSStartedFrame):
            # TTS processing started
            if self.current_interaction_id and self.current_interaction_id in self.current_interactions:
                interaction = self.current_interactions[self.current_interaction_id]
                interaction.tts_start_time = time.time()
                logger.debug(f"🔊 TTS started - {interaction.interaction_id}")

        elif isinstance(frame, TTSAudioRawFrame):
            # TTS audio generation complete
            if self.current_interaction_id and self.current_interaction_id in self.current_interactions:
                interaction = self.current_interactions[self.current_interaction_id]
                if interaction.tts_complete_time == 0:
                    interaction.tts_complete_time = time.time()
                    logger.debug(f"🔊 TTS audio complete - {interaction.interaction_id}")

                    # This is typically the end of the interaction
                    self._complete_interaction(interaction.interaction_id)

    def get_statistics(self) -> Dict[str, Any]:
        """Get current latency statistics."""
        return {
            "current_stats": self.stats,
            "active_interactions": len(self.current_interactions),
            "completed_interactions": len(self.completed_interactions),
            "recent_interactions": [
                interaction.to_dict()
                for interaction in self.completed_interactions[-5:]  # Last 5 interactions
            ]
        }

    def reset_statistics(self):
        """Reset all statistics and completed interactions."""
        self.completed_interactions.clear()
        self.current_interactions.clear()
        self.stats = {
            "total_interactions": 0,
            "average_latencies": {},
            "min_latencies": {},
            "max_latencies": {},
            "p95_latencies": {},
            "p99_latencies": {}
        }
        logger.info("Latency statistics reset")

    def log_summary_report(self):
        """Log a comprehensive summary report of latency statistics."""
        if not self.completed_interactions:
            logger.info("📊 No completed interactions to report")
            return

        logger.info("=" * 60)
        logger.info("📊 LATENCY ANALYSIS SUMMARY REPORT")
        logger.info("=" * 60)
        logger.info(f"Total Interactions: {self.stats['total_interactions']}")
        logger.info("")

        # Average latencies
        if self.stats['average_latencies']:
            logger.info("📈 Average Latencies:")
            for latency_type, avg_value in self.stats['average_latencies'].items():
                logger.info(f"  {latency_type.replace('_', ' ').title()}: {avg_value:.2f}ms")

        logger.info("")

        # Performance ranges
        if self.stats['min_latencies'] and self.stats['max_latencies']:
            logger.info("📊 Performance Ranges:")
            for latency_type in self.stats['min_latencies']:
                min_val = self.stats['min_latencies'][latency_type]
                max_val = self.stats['max_latencies'][latency_type]
                logger.info(f"  {latency_type.replace('_', ' ').title()}: {min_val:.2f}ms - {max_val:.2f}ms")

        logger.info("")

        # Percentiles (if available)
        if self.stats['p95_latencies']:
            logger.info("📊 95th Percentile Latencies:")
            for latency_type, p95_value in self.stats['p95_latencies'].items():
                logger.info(f"  {latency_type.replace('_', ' ').title()}: {p95_value:.2f}ms")

        logger.info("=" * 60)
