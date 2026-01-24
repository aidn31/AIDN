"""
AIDN Latency Tracker
====================

Comprehensive latency tracking for voice pipeline components:
- STT (Speech-to-Text) latency
- LLM TTFT (Time To First Token)
- TTS TTFB (Time To First Byte)
- Total response latency

Tracks metrics per-turn to verify KV caching effectiveness.
Turn 2+ should be faster than Turn 1 if caching is working.
"""

import time
import logging
import json
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger("aidn.latency")


@dataclass
class TurnMetrics:
    """Metrics for a single conversation turn."""
    turn_number: int
    timestamp: str = ""

    # Component latencies (in milliseconds)
    stt_latency_ms: Optional[float] = None      # Speech end -> transcript ready
    llm_ttft_ms: Optional[float] = None         # Transcript ready -> first LLM token
    tts_ttfb_ms: Optional[float] = None         # First LLM token -> first audio byte
    total_latency_ms: Optional[float] = None    # Speech end -> agent starts speaking

    # Additional context
    user_transcript: str = ""
    response_preview: str = ""
    response_token_count: Optional[int] = None

    # Timing checkpoints (internal, not logged)
    _speech_end_time: float = field(default=0, repr=False)
    _transcript_ready_time: float = field(default=0, repr=False)
    _llm_first_token_time: float = field(default=0, repr=False)
    _tts_first_byte_time: float = field(default=0, repr=False)
    _agent_speaking_time: float = field(default=0, repr=False)

    def calculate_latencies(self) -> None:
        """Calculate all latencies from checkpoint times."""
        if self._speech_end_time and self._transcript_ready_time:
            self.stt_latency_ms = (self._transcript_ready_time - self._speech_end_time) * 1000

        if self._transcript_ready_time and self._llm_first_token_time:
            self.llm_ttft_ms = (self._llm_first_token_time - self._transcript_ready_time) * 1000

        if self._llm_first_token_time and self._tts_first_byte_time:
            self.tts_ttfb_ms = (self._tts_first_byte_time - self._llm_first_token_time) * 1000

        if self._speech_end_time and self._agent_speaking_time:
            self.total_latency_ms = (self._agent_speaking_time - self._speech_end_time) * 1000

    def to_log_dict(self) -> dict:
        """Return dict suitable for logging (excludes internal fields)."""
        return {
            "turn": self.turn_number,
            "timestamp": self.timestamp,
            "stt_ms": round(self.stt_latency_ms, 0) if self.stt_latency_ms else None,
            "llm_ttft_ms": round(self.llm_ttft_ms, 0) if self.llm_ttft_ms else None,
            "tts_ttfb_ms": round(self.tts_ttfb_ms, 0) if self.tts_ttfb_ms else None,
            "total_ms": round(self.total_latency_ms, 0) if self.total_latency_ms else None,
            "user": self.user_transcript[:50] + "..." if len(self.user_transcript) > 50 else self.user_transcript,
        }


class LatencyTracker:
    """
    Tracks latency across all conversation turns.

    Usage:
        tracker = LatencyTracker()

        # On user speech end (VAD detects silence)
        tracker.on_speech_end()

        # On STT transcript ready
        tracker.on_transcript_ready(transcript)

        # On LLM first token
        tracker.on_llm_first_token()

        # On TTS first audio byte
        tracker.on_tts_first_byte()

        # On agent starts speaking
        tracker.on_agent_speaking(response)

        # Get summary
        tracker.log_summary()
    """

    def __init__(self, call_id: str = ""):
        self.call_id = call_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.turns: List[TurnMetrics] = []
        self.current_turn: Optional[TurnMetrics] = None
        self.turn_count = 0

        logger.info(f"LatencyTracker initialized for call: {self.call_id}")

    def _start_new_turn(self) -> TurnMetrics:
        """Start tracking a new conversation turn."""
        self.turn_count += 1
        turn = TurnMetrics(
            turn_number=self.turn_count,
            timestamp=datetime.now().isoformat()
        )
        self.current_turn = turn
        return turn

    def on_speech_end(self) -> None:
        """Called when VAD detects end of user speech."""
        turn = self._start_new_turn()
        turn._speech_end_time = time.perf_counter()
        logger.debug(f"Turn {turn.turn_number}: Speech ended")

    def on_transcript_ready(self, transcript: str) -> None:
        """Called when STT provides the final transcript."""
        if not self.current_turn:
            logger.warning("on_transcript_ready called without active turn")
            return

        self.current_turn._transcript_ready_time = time.perf_counter()
        self.current_turn.user_transcript = transcript

        # Calculate STT latency immediately
        if self.current_turn._speech_end_time:
            stt_ms = (self.current_turn._transcript_ready_time - self.current_turn._speech_end_time) * 1000
            logger.info(f"Turn {self.current_turn.turn_number} STT: {stt_ms:.0f}ms - \"{transcript[:40]}...\"")

    def on_llm_first_token(self) -> None:
        """Called when LLM emits its first token."""
        if not self.current_turn:
            logger.warning("on_llm_first_token called without active turn")
            return

        self.current_turn._llm_first_token_time = time.perf_counter()

        # Calculate LLM TTFT immediately
        if self.current_turn._transcript_ready_time:
            ttft_ms = (self.current_turn._llm_first_token_time - self.current_turn._transcript_ready_time) * 1000
            logger.info(f"Turn {self.current_turn.turn_number} LLM TTFT: {ttft_ms:.0f}ms")

    def on_tts_first_byte(self) -> None:
        """Called when TTS emits first audio byte."""
        if not self.current_turn:
            logger.warning("on_tts_first_byte called without active turn")
            return

        self.current_turn._tts_first_byte_time = time.perf_counter()

        # Calculate TTS TTFB immediately
        if self.current_turn._llm_first_token_time:
            ttfb_ms = (self.current_turn._tts_first_byte_time - self.current_turn._llm_first_token_time) * 1000
            logger.info(f"Turn {self.current_turn.turn_number} TTS TTFB: {ttfb_ms:.0f}ms")

    def on_agent_speaking(self, response: str = "", token_count: int = None) -> None:
        """Called when agent starts speaking (audio playing)."""
        if not self.current_turn:
            logger.warning("on_agent_speaking called without active turn")
            return

        self.current_turn._agent_speaking_time = time.perf_counter()
        self.current_turn.response_preview = response[:100] if response else ""
        self.current_turn.response_token_count = token_count

        # Calculate all latencies and log
        self.current_turn.calculate_latencies()

        # Log the turn summary
        self._log_turn_summary()

        # Save turn and clear current
        self.turns.append(self.current_turn)
        self.current_turn = None

    def _log_turn_summary(self) -> None:
        """Log a summary for the current turn."""
        if not self.current_turn:
            return

        turn = self.current_turn

        # Build summary line
        parts = [f"Turn {turn.turn_number}:"]

        if turn.stt_latency_ms is not None:
            parts.append(f"STT={turn.stt_latency_ms:.0f}ms")

        if turn.llm_ttft_ms is not None:
            parts.append(f"LLM={turn.llm_ttft_ms:.0f}ms")

        if turn.tts_ttfb_ms is not None:
            parts.append(f"TTS={turn.tts_ttfb_ms:.0f}ms")

        if turn.total_latency_ms is not None:
            parts.append(f"TOTAL={turn.total_latency_ms:.0f}ms")

            # Add emoji indicator
            if turn.total_latency_ms < 500:
                parts.append("[OK]")
            elif turn.total_latency_ms < 1000:
                parts.append("[WARN]")
            else:
                parts.append("[SLOW]")

        logger.info(" | ".join(parts))

    def log_summary(self) -> None:
        """Log a summary of all turns (useful at end of call)."""
        if not self.turns:
            logger.info("No turns recorded")
            return

        logger.info(f"\n{'='*60}")
        logger.info(f"LATENCY SUMMARY - Call {self.call_id}")
        logger.info(f"{'='*60}")

        # Per-turn breakdown
        for turn in self.turns:
            metrics = turn.to_log_dict()
            logger.info(f"Turn {metrics['turn']}: STT={metrics['stt_ms']}ms | LLM={metrics['llm_ttft_ms']}ms | TTS={metrics['tts_ttfb_ms']}ms | Total={metrics['total_ms']}ms")

        # Averages
        total_latencies = [t.total_latency_ms for t in self.turns if t.total_latency_ms]
        llm_ttfts = [t.llm_ttft_ms for t in self.turns if t.llm_ttft_ms]
        stt_latencies = [t.stt_latency_ms for t in self.turns if t.stt_latency_ms]

        logger.info(f"-" * 60)

        if total_latencies:
            avg_total = sum(total_latencies) / len(total_latencies)
            logger.info(f"Average Total Latency: {avg_total:.0f}ms")

        if llm_ttfts:
            avg_llm = sum(llm_ttfts) / len(llm_ttfts)
            logger.info(f"Average LLM TTFT: {avg_llm:.0f}ms")

            # Check KV caching effectiveness
            if len(llm_ttfts) >= 2:
                turn1_ttft = llm_ttfts[0]
                turn2plus_avg = sum(llm_ttfts[1:]) / len(llm_ttfts[1:])
                improvement = ((turn1_ttft - turn2plus_avg) / turn1_ttft) * 100

                if improvement > 10:
                    logger.info(f"KV Caching WORKING: Turn 1={turn1_ttft:.0f}ms, Turn 2+={turn2plus_avg:.0f}ms ({improvement:.0f}% faster)")
                else:
                    logger.warning(f"KV Caching MAY NOT BE WORKING: Turn 1={turn1_ttft:.0f}ms, Turn 2+={turn2plus_avg:.0f}ms ({improvement:.0f}% change)")

        if stt_latencies:
            avg_stt = sum(stt_latencies) / len(stt_latencies)
            logger.info(f"Average STT Latency: {avg_stt:.0f}ms")

        logger.info(f"{'='*60}\n")

    def get_metrics_json(self) -> str:
        """Get all metrics as JSON (for storage/analysis)."""
        return json.dumps({
            "call_id": self.call_id,
            "turn_count": len(self.turns),
            "turns": [t.to_log_dict() for t in self.turns],
            "summary": self._calculate_summary()
        }, indent=2)

    def _calculate_summary(self) -> dict:
        """Calculate summary statistics."""
        total_latencies = [t.total_latency_ms for t in self.turns if t.total_latency_ms]
        llm_ttfts = [t.llm_ttft_ms for t in self.turns if t.llm_ttft_ms]
        stt_latencies = [t.stt_latency_ms for t in self.turns if t.stt_latency_ms]
        tts_ttfbs = [t.tts_ttfb_ms for t in self.turns if t.tts_ttfb_ms]

        def stats(values: List[float]) -> dict:
            if not values:
                return {}
            sorted_values = sorted(values)
            return {
                "avg": round(sum(values) / len(values), 0),
                "min": round(min(values), 0),
                "max": round(max(values), 0),
                "p95": round(sorted_values[int(len(values) * 0.95)] if len(values) >= 2 else values[0], 0)
            }

        return {
            "total_latency": stats(total_latencies),
            "llm_ttft": stats(llm_ttfts),
            "stt_latency": stats(stt_latencies),
            "tts_ttfb": stats(tts_ttfbs),
        }


# Singleton for easy access across modules
_tracker: Optional[LatencyTracker] = None


def get_tracker(call_id: str = "") -> LatencyTracker:
    """Get or create the global latency tracker."""
    global _tracker
    if _tracker is None or (call_id and _tracker.call_id != call_id):
        _tracker = LatencyTracker(call_id)
    return _tracker


def reset_tracker() -> None:
    """Reset the global tracker (for new calls)."""
    global _tracker
    _tracker = None
