#!/usr/bin/env python3
"""
Latency Test Script
===================
Dispatches test calls and analyzes latency logs.

Usage:
    # Start the agent first in another terminal:
    python -m src.voice_agent.main dev

    # Then run this script:
    python scripts/latency_test.py +19086197628

    # Or analyze existing logs:
    python scripts/latency_test.py --analyze /path/to/logfile.txt
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class LatencySample:
    """A single latency measurement."""
    timestamp: str
    transcript: str
    eou_delay_ms: float = 0.0
    stt_latency_ms: float = 0.0
    llm_ttft_ms: float = 0.0
    llm_total_ms: float = 0.0
    tts_ttfb_ms: float = 0.0
    tts_total_ms: float = 0.0
    total_latency_ms: float = 0.0
    tool_calls: list = None

    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []


def parse_latency_logs(log_content: str) -> list[LatencySample]:
    """Parse latency information from log content."""
    samples = []
    current_sample = None

    lines = log_content.split('\n')

    for line in lines:
        # Look for USER_SPEECH_END to start a new sample
        if 'USER_SPEECH_END' in line:
            if current_sample:
                samples.append(current_sample)
            timestamp = line.split(' - ')[0] if ' - ' in line else ''
            transcript_match = re.search(r'"([^"]+)"', line)
            transcript = transcript_match.group(1) if transcript_match else ''
            current_sample = LatencySample(timestamp=timestamp, transcript=transcript)

        elif current_sample:
            # Parse EOU metrics
            if 'EOU:' in line or 'EOU Delay:' in line:
                match = re.search(r'(\d+)ms', line)
                if match:
                    current_sample.eou_delay_ms = float(match.group(1))

            # Parse STT latency
            elif 'STT Latency:' in line or 'STT:' in line:
                match = re.search(r'(\d+)ms', line)
                if match:
                    current_sample.stt_latency_ms = float(match.group(1))

            # Parse LLM metrics
            elif 'LLM:' in line:
                ttft_match = re.search(r'TTFT=(\d+)ms', line)
                total_match = re.search(r'total=(\d+)ms', line)
                if ttft_match:
                    current_sample.llm_ttft_ms = float(ttft_match.group(1))
                if total_match:
                    current_sample.llm_total_ms = float(total_match.group(1))

            # Parse TTS metrics
            elif 'TTS:' in line:
                ttfb_match = re.search(r'TTFB=(\d+)ms', line)
                total_match = re.search(r'total=(\d+)ms', line)
                if ttfb_match:
                    current_sample.tts_ttfb_ms = float(ttfb_match.group(1))
                if total_match:
                    current_sample.tts_total_ms = float(total_match.group(1))

            # Parse tool calls
            elif 'Tool call:' in line:
                tool_match = re.search(r'Tool call: (\w+)', line)
                if tool_match:
                    current_sample.tool_calls.append(tool_match.group(1))

            # Parse total latency
            elif 'TOTAL RESPONSE TIME:' in line or 'TOTAL LATENCY:' in line:
                match = re.search(r'(\d+)ms', line)
                if match:
                    current_sample.total_latency_ms = float(match.group(1))

    # Don't forget the last sample
    if current_sample:
        samples.append(current_sample)

    return samples


def analyze_samples(samples: list[LatencySample]) -> dict:
    """Analyze latency samples and compute statistics."""
    if not samples:
        return {"error": "No samples found"}

    stats = {
        "count": len(samples),
        "eou_delay": {"values": [], "avg": 0, "min": 0, "max": 0},
        "stt_latency": {"values": [], "avg": 0, "min": 0, "max": 0},
        "llm_ttft": {"values": [], "avg": 0, "min": 0, "max": 0},
        "llm_total": {"values": [], "avg": 0, "min": 0, "max": 0},
        "tts_ttfb": {"values": [], "avg": 0, "min": 0, "max": 0},
        "tts_total": {"values": [], "avg": 0, "min": 0, "max": 0},
        "total_latency": {"values": [], "avg": 0, "min": 0, "max": 0},
        "tool_calls": defaultdict(int),
    }

    for sample in samples:
        if sample.eou_delay_ms > 0:
            stats["eou_delay"]["values"].append(sample.eou_delay_ms)
        if sample.stt_latency_ms > 0:
            stats["stt_latency"]["values"].append(sample.stt_latency_ms)
        if sample.llm_ttft_ms > 0:
            stats["llm_ttft"]["values"].append(sample.llm_ttft_ms)
        if sample.llm_total_ms > 0:
            stats["llm_total"]["values"].append(sample.llm_total_ms)
        if sample.tts_ttfb_ms > 0:
            stats["tts_ttfb"]["values"].append(sample.tts_ttfb_ms)
        if sample.tts_total_ms > 0:
            stats["tts_total"]["values"].append(sample.tts_total_ms)
        if sample.total_latency_ms > 0:
            stats["total_latency"]["values"].append(sample.total_latency_ms)
        for tool in sample.tool_calls:
            stats["tool_calls"][tool] += 1

    # Compute statistics
    for key in ["eou_delay", "stt_latency", "llm_ttft", "llm_total", "tts_ttfb", "tts_total", "total_latency"]:
        values = stats[key]["values"]
        if values:
            stats[key]["avg"] = sum(values) / len(values)
            stats[key]["min"] = min(values)
            stats[key]["max"] = max(values)
            stats[key]["p50"] = sorted(values)[len(values) // 2]
            stats[key]["p90"] = sorted(values)[int(len(values) * 0.9)] if len(values) >= 10 else max(values)

    return stats


def print_analysis(stats: dict):
    """Print a formatted analysis report."""
    print("\n" + "=" * 70)
    print("                    LATENCY ANALYSIS REPORT")
    print("=" * 70)
    print(f"\nTotal samples analyzed: {stats['count']}")
    print("\n" + "-" * 70)
    print("PIPELINE STAGE BREAKDOWN")
    print("-" * 70)

    headers = ["Stage", "Avg", "Min", "Max", "P50", "P90"]
    row_format = "{:<20} {:>8} {:>8} {:>8} {:>8} {:>8}"
    print(row_format.format(*headers))
    print("-" * 70)

    stages = [
        ("EOU Delay", "eou_delay"),
        ("STT Latency", "stt_latency"),
        ("LLM TTFT", "llm_ttft"),
        ("LLM Total", "llm_total"),
        ("TTS TTFB", "tts_ttfb"),
        ("TTS Total", "tts_total"),
        ("TOTAL", "total_latency"),
    ]

    for label, key in stages:
        s = stats[key]
        if s["values"]:
            print(row_format.format(
                label,
                f"{s['avg']:.0f}ms",
                f"{s['min']:.0f}ms",
                f"{s['max']:.0f}ms",
                f"{s.get('p50', 0):.0f}ms",
                f"{s.get('p90', 0):.0f}ms",
            ))
        else:
            print(row_format.format(label, "N/A", "N/A", "N/A", "N/A", "N/A"))

    if stats["tool_calls"]:
        print("\n" + "-" * 70)
        print("TOOL CALLS")
        print("-" * 70)
        for tool, count in stats["tool_calls"].items():
            print(f"  {tool}: {count} calls")

    # Recommendations
    print("\n" + "-" * 70)
    print("DIAGNOSIS & RECOMMENDATIONS")
    print("-" * 70)

    total_avg = stats["total_latency"]["avg"] if stats["total_latency"]["values"] else 0

    if total_avg > 3000:
        print("  WARNING: Total latency is very high (>3s)")
    elif total_avg > 1500:
        print("  CAUTION: Total latency is elevated (>1.5s)")
    else:
        print("  OK: Total latency is acceptable (<1.5s)")

    # Find bottleneck
    bottlenecks = []
    if stats["llm_ttft"]["avg"] > 500:
        bottlenecks.append(("LLM TTFT", stats["llm_ttft"]["avg"], "Consider: smaller model, prompt caching, or streaming"))
    if stats["llm_total"]["avg"] > 2000:
        bottlenecks.append(("LLM Total", stats["llm_total"]["avg"], "Consider: shorter responses, faster model"))
    if stats["tts_ttfb"]["avg"] > 300:
        bottlenecks.append(("TTS TTFB", stats["tts_ttfb"]["avg"], "Consider: Cartesia (fastest), streaming TTS"))
    if stats["eou_delay"]["avg"] > 500:
        bottlenecks.append(("EOU Delay", stats["eou_delay"]["avg"], "Consider: lower min_endpointing_delay"))
    if stats["stt_latency"]["avg"] > 500:
        bottlenecks.append(("STT Latency", stats["stt_latency"]["avg"], "Consider: lower endpointing_ms"))

    if bottlenecks:
        print("\n  BOTTLENECKS IDENTIFIED:")
        for stage, value, suggestion in sorted(bottlenecks, key=lambda x: -x[1]):
            print(f"    - {stage}: {value:.0f}ms")
            print(f"      {suggestion}")

    print("\n" + "=" * 70)


async def dispatch_test_call(phone_number: str, log_file: Optional[str] = None):
    """Dispatch a test call and optionally capture logs."""
    from livekit import api

    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not all([livekit_url, api_key, api_secret]):
        print("Missing LIVEKIT_URL, LIVEKIT_API_KEY, or LIVEKIT_API_SECRET")
        sys.exit(1)

    print(f"\n{'=' * 50}")
    print(f"LATENCY TEST CALL")
    print(f"{'=' * 50}")
    print(f"Phone: {phone_number}")
    print(f"LiveKit: {livekit_url}")
    print(f"{'=' * 50}\n")

    lk_api = api.LiveKitAPI(url=livekit_url, api_key=api_key, api_secret=api_secret)

    room_name = f"latency-test-{int(time.time())}"

    try:
        await lk_api.room.create_room(api.CreateRoomRequest(name=room_name))
        print(f"Created room: {room_name}")
    except Exception as e:
        print(f"Room may exist: {e}")

    try:
        dispatch = await lk_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name="aidn-outbound",
                metadata=json.dumps({
                    "phone_number": phone_number,
                    "lead_id": None,
                    "agent_id": None,
                })
            )
        )
        print(f"Dispatched agent: {dispatch.id}")
        print(f"\nCall will connect shortly...")
        print(f"\nDuring the call, try these phrases to test latency:")
        print(f"  1. 'What is it?' (tests RAG tool)")
        print(f"  2. 'I'm not interested' (tests RAG tool)")
        print(f"  3. 'Yes' or 'Yeah' (simple response)")
        print(f"  4. 'Morning' or 'Afternoon' (appointment flow)")
        print(f"\nWatch the agent terminal for LATENCY BREAKDOWN logs.")

    except Exception as e:
        print(f"Failed to dispatch: {e}")
        raise

    await lk_api.aclose()


def main():
    parser = argparse.ArgumentParser(description="AIDN Latency Test Tool")
    parser.add_argument("phone_or_file", nargs="?", help="Phone number to call OR --analyze with log file")
    parser.add_argument("--analyze", "-a", metavar="FILE", help="Analyze latency from log file")

    args = parser.parse_args()

    if args.analyze:
        # Analyze existing log file
        try:
            with open(args.analyze, 'r') as f:
                content = f.read()
            samples = parse_latency_logs(content)
            stats = analyze_samples(samples)
            print_analysis(stats)
        except FileNotFoundError:
            print(f"File not found: {args.analyze}")
            sys.exit(1)

    elif args.phone_or_file:
        # Dispatch test call
        if args.phone_or_file.startswith('+'):
            asyncio.run(dispatch_test_call(args.phone_or_file))
        else:
            # Try to analyze as file
            try:
                with open(args.phone_or_file, 'r') as f:
                    content = f.read()
                samples = parse_latency_logs(content)
                stats = analyze_samples(samples)
                print_analysis(stats)
            except FileNotFoundError:
                print(f"Not a valid phone number or file: {args.phone_or_file}")
                print("Phone numbers should start with +")
                sys.exit(1)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python scripts/latency_test.py +19086197628")
        print("  python scripts/latency_test.py --analyze /tmp/agent.log")


if __name__ == "__main__":
    main()
