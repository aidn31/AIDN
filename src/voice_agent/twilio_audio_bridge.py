"""
Twilio-LiveKit Audio Bridge
============================

Bridges audio between Twilio phone calls and LiveKit rooms for real-time AI voice agent.

This module handles:
- WebSocket connection from Twilio <Stream>
- Audio format conversion (μ-law 8kHz ↔ PCM 16kHz)
- Bidirectional audio streaming to/from LiveKit room
"""

import asyncio
import base64
import json
import logging
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from uuid import UUID

import numpy as np
from livekit import api, rtc

logger = logging.getLogger(__name__)


@dataclass
class TwilioStreamMessage:
    """Parsed Twilio Stream WebSocket message."""
    event: str
    stream_sid: Optional[str] = None
    sequence_number: Optional[int] = None
    media: Optional[Dict[str, Any]] = None
    start: Optional[Dict[str, Any]] = None
    stop: Optional[Dict[str, Any]] = None
    mark: Optional[Dict[str, Any]] = None


class AudioConverter:
    """Handles audio format conversion between Twilio and LiveKit using numpy."""
    
    # Twilio sends μ-law 8kHz mono
    TWILIO_SAMPLE_RATE = 8000
    TWILIO_CHANNELS = 1
    
    # LiveKit typically uses 16kHz or 48kHz PCM
    LIVEKIT_SAMPLE_RATE = 16000
    LIVEKIT_CHANNELS = 1
    
    # μ-law lookup table for decoding (pre-computed for efficiency)
    _MULAW_DECODE_TABLE = None
    _MULAW_ENCODE_TABLE = None
    
    @classmethod
    def _init_tables(cls):
        """Initialize μ-law lookup tables."""
        if cls._MULAW_DECODE_TABLE is None:
            # μ-law decoding table
            cls._MULAW_DECODE_TABLE = np.array([
                -32124, -31100, -30076, -29052, -28028, -27004, -25980, -24956,
                -23932, -22908, -21884, -20860, -19836, -18812, -17788, -16764,
                -15996, -15484, -14972, -14460, -13948, -13436, -12924, -12412,
                -11900, -11388, -10876, -10364,  -9852,  -9340,  -8828,  -8316,
                 -7932,  -7676,  -7420,  -7164,  -6908,  -6652,  -6396,  -6140,
                 -5884,  -5628,  -5372,  -5116,  -4860,  -4604,  -4348,  -4092,
                 -3900,  -3772,  -3644,  -3516,  -3388,  -3260,  -3132,  -3004,
                 -2876,  -2748,  -2620,  -2492,  -2364,  -2236,  -2108,  -1980,
                 -1884,  -1820,  -1756,  -1692,  -1628,  -1564,  -1500,  -1436,
                 -1372,  -1308,  -1244,  -1180,  -1116,  -1052,   -988,   -924,
                  -876,   -844,   -812,   -780,   -748,   -716,   -684,   -652,
                  -620,   -588,   -556,   -524,   -492,   -460,   -428,   -396,
                  -372,   -356,   -340,   -324,   -308,   -292,   -276,   -260,
                  -244,   -228,   -212,   -196,   -180,   -164,   -148,   -132,
                  -120,   -112,   -104,    -96,    -88,    -80,    -72,    -64,
                   -56,    -48,    -40,    -32,    -24,    -16,     -8,      0,
                 32124,  31100,  30076,  29052,  28028,  27004,  25980,  24956,
                 23932,  22908,  21884,  20860,  19836,  18812,  17788,  16764,
                 15996,  15484,  14972,  14460,  13948,  13436,  12924,  12412,
                 11900,  11388,  10876,  10364,   9852,   9340,   8828,   8316,
                  7932,   7676,   7420,   7164,   6908,   6652,   6396,   6140,
                  5884,   5628,   5372,   5116,   4860,   4604,   4348,   4092,
                  3900,   3772,   3644,   3516,   3388,   3260,   3132,   3004,
                  2876,   2748,   2620,   2492,   2364,   2236,   2108,   1980,
                  1884,   1820,   1756,   1692,   1628,   1564,   1500,   1436,
                  1372,   1308,   1244,   1180,   1116,   1052,    988,    924,
                   876,    844,    812,    780,    748,    716,    684,    652,
                   620,    588,    556,    524,    492,    460,    428,    396,
                   372,    356,    340,    324,    308,    292,    276,    260,
                   244,    228,    212,    196,    180,    164,    148,    132,
                   120,    112,    104,     96,     88,     80,     72,     64,
                    56,     48,     40,     32,     24,     16,      8,      0
            ], dtype=np.int16)
    
    @staticmethod
    def _ulaw_decode(mulaw_byte: int) -> int:
        """Decode a single μ-law byte to linear PCM."""
        mulaw_byte = ~mulaw_byte
        sign = (mulaw_byte & 0x80)
        exponent = (mulaw_byte >> 4) & 0x07
        mantissa = mulaw_byte & 0x0F
        sample = (((mantissa << 3) + 0x84) << exponent) - 0x84
        if sign != 0:
            sample = -sample
        return sample
    
    @staticmethod
    def _ulaw_encode(sample: int) -> int:
        """Encode a linear PCM sample to μ-law."""
        MULAW_MAX = 32635
        MULAW_BIAS = 0x84
        
        # Clip the sample
        if sample > MULAW_MAX:
            sample = MULAW_MAX
        elif sample < -MULAW_MAX:
            sample = -MULAW_MAX
        
        # Get sign
        sign = 0
        if sample < 0:
            sign = 0x80
            sample = -sample
        
        # Add bias
        sample = sample + MULAW_BIAS
        
        # Find exponent and mantissa
        exponent = 7
        for exp_val in [0x4000, 0x2000, 0x1000, 0x0800, 0x0400, 0x0200, 0x0100]:
            if sample >= exp_val:
                break
            exponent -= 1
        
        mantissa = (sample >> (exponent + 3)) & 0x0F
        mulaw_byte = ~(sign | (exponent << 4) | mantissa)
        
        return mulaw_byte & 0xFF
    
    @classmethod
    def mulaw_to_pcm16(cls, mulaw_data: bytes) -> bytes:
        """Convert μ-law 8kHz audio to PCM 16-bit 16kHz for LiveKit."""
        cls._init_tables()
        
        # Convert μ-law bytes to numpy array
        mulaw_array = np.frombuffer(mulaw_data, dtype=np.uint8)
        
        # Decode μ-law to PCM using lookup table
        pcm_8k = cls._MULAW_DECODE_TABLE[mulaw_array]
        
        # Upsample from 8kHz to 16kHz using linear interpolation
        # Simple 2x upsampling
        pcm_16k = np.zeros(len(pcm_8k) * 2, dtype=np.int16)
        pcm_16k[0::2] = pcm_8k
        pcm_16k[1::2] = pcm_8k  # Duplicate samples (simple upsampling)
        
        # Smooth with simple averaging (optional, reduces aliasing)
        # pcm_16k[1:-1:2] = (pcm_8k[:-1] + pcm_8k[1:]) // 2
        
        return pcm_16k.tobytes()
    
    @classmethod
    def pcm16_to_mulaw(cls, pcm_data: bytes, source_rate: int = 16000) -> bytes:
        """Convert PCM 16-bit audio to μ-law 8kHz for Twilio."""
        cls._init_tables()
        
        # Convert bytes to numpy array
        pcm_array = np.frombuffer(pcm_data, dtype=np.int16)
        
        # Downsample if needed
        if source_rate != cls.TWILIO_SAMPLE_RATE:
            ratio = source_rate // cls.TWILIO_SAMPLE_RATE
            if ratio > 1:
                # Simple decimation (take every Nth sample)
                pcm_array = pcm_array[::ratio]
        
        # Encode to μ-law
        mulaw_array = np.zeros(len(pcm_array), dtype=np.uint8)
        for i, sample in enumerate(pcm_array):
            mulaw_array[i] = cls._ulaw_encode(int(sample))
        
        return mulaw_array.tobytes()


class TwilioAudioBridge:
    """
    Bridges audio between a Twilio phone call and a LiveKit room.
    
    This is the core component that enables the AI voice agent to speak on phone calls.
    """
    
    def __init__(
        self,
        room_name: str,
        lead_id: str,
        agent_id: str,
        livekit_url: Optional[str] = None,
        livekit_api_key: Optional[str] = None,
        livekit_api_secret: Optional[str] = None
    ):
        self.room_name = room_name
        self.lead_id = lead_id
        self.agent_id = agent_id
        
        # LiveKit configuration
        self.livekit_url = livekit_url or os.getenv("LIVEKIT_URL")
        self.livekit_api_key = livekit_api_key or os.getenv("LIVEKIT_API_KEY")
        self.livekit_api_secret = livekit_api_secret or os.getenv("LIVEKIT_API_SECRET")

        # Validate configuration
        logger.info(f"🔧 Validating LiveKit configuration...")
        logger.info(f"🌐 LIVEKIT_URL: {self.livekit_url}")
        logger.info(f"🔑 LIVEKIT_API_KEY: {'✅ SET' if self.livekit_api_key else '❌ MISSING'}")
        logger.info(f"🔐 LIVEKIT_API_SECRET: {'✅ SET' if self.livekit_api_secret else '❌ MISSING'}")

        if not all([self.livekit_url, self.livekit_api_key, self.livekit_api_secret]):
            missing = []
            if not self.livekit_url: missing.append("LIVEKIT_URL")
            if not self.livekit_api_key: missing.append("LIVEKIT_API_KEY")
            if not self.livekit_api_secret: missing.append("LIVEKIT_API_SECRET")
            logger.error(f"❌ Missing required LiveKit environment variables: {missing}")
        else:
            logger.info(f"✅ All LiveKit configuration present")

        # Runtime state
        self.room: Optional[rtc.Room] = None
        self.audio_source: Optional[rtc.AudioSource] = None
        self.local_track: Optional[rtc.LocalAudioTrack] = None
        self.stream_sid: Optional[str] = None
        self.is_connected = False

        # Audio converter
        self.converter = AudioConverter()

        # Queue for outgoing audio to Twilio
        self.outgoing_audio_queue: asyncio.Queue = asyncio.Queue()

        logger.info(f"🎉 TwilioAudioBridge initialized for room: {room_name}")
    
    async def connect_to_livekit(self) -> bool:
        """Connect to LiveKit room and set up audio tracks."""
        logger.info(f"🔄 Starting LiveKit connection for room: {self.room_name}")
        try:
            # Create room token with proper permissions
            logger.info("🎫 Creating room token...")
            token = self._create_room_token()
            logger.info(f"✅ Room token created successfully")

            # Create and connect to room
            logger.info("🏠 Creating LiveKit room object...")
            self.room = rtc.Room()
            logger.info("✅ Room object created")

            # Set up event handlers using synchronous wrappers
            # LiveKit .on() requires sync callbacks - use asyncio.create_task for async work
            logger.info("📋 Setting up event handlers...")
            @self.room.on("track_subscribed")
            def on_track_subscribed(
                track: rtc.Track,
                publication: rtc.RemoteTrackPublication,
                participant: rtc.RemoteParticipant
            ):
                asyncio.create_task(self._on_track_subscribed(track, publication, participant))

            @self.room.on("disconnected")
            def on_disconnected():
                asyncio.create_task(self._on_disconnected())
            logger.info("✅ Event handlers configured")

            # Connect to the room
            logger.info(f"🌐 Connecting to LiveKit at {self.livekit_url}...")
            await self.room.connect(self.livekit_url, token)
            logger.info("✅ Connected to LiveKit room successfully")

            # Create audio source for publishing Twilio audio to LiveKit
            logger.info("🎤 Creating audio source...")
            self.audio_source = rtc.AudioSource(
                sample_rate=AudioConverter.LIVEKIT_SAMPLE_RATE,
                num_channels=AudioConverter.LIVEKIT_CHANNELS
            )
            logger.info(f"✅ Audio source created ({AudioConverter.LIVEKIT_SAMPLE_RATE}Hz, {AudioConverter.LIVEKIT_CHANNELS} channels)")

            # Create local audio track
            logger.info("🎵 Creating local audio track...")
            self.local_track = rtc.LocalAudioTrack.create_audio_track(
                "twilio-audio",
                self.audio_source
            )
            logger.info("✅ Local audio track created")

            # Publish the track
            logger.info("📡 Publishing audio track to LiveKit...")
            await self.room.local_participant.publish_track(self.local_track)
            logger.info("✅ Audio track published successfully")

            self.is_connected = True
            logger.info(f"🎉 FULL SUCCESS: Connected to LiveKit room: {self.room_name}")

            return True

        except Exception as e:
            logger.error(f"❌ FAILED to connect to LiveKit at step: {e}")
            import traceback
            logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")
            return False
    
    def _create_room_token(self) -> str:
        """Create a LiveKit room token for the bridge participant."""
        token = api.AccessToken(
            api_key=self.livekit_api_key,
            api_secret=self.livekit_api_secret
        )
        
        token.with_identity(f"twilio-bridge-{self.lead_id}")
        token.with_name("Twilio Phone Bridge")
        
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=self.room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        ))
        
        # Add room metadata with lead and agent info for bridge participant
        token.with_metadata(json.dumps({
            "lead_id": self.lead_id,
            "agent_id": self.agent_id,
            "type": "twilio_bridge"
        }))

        # CRITICAL: Also set room-level metadata attributes for voice agent access
        token.with_attributes({
            "lead_id": self.lead_id,
            "agent_id": self.agent_id
        })
        
        return token.to_jwt()
    
    async def _on_track_subscribed(
        self,
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant
    ):
        """Handle when we subscribe to the voice agent's audio track."""
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info(f"Subscribed to audio track from: {participant.identity}")
            
            # Create audio stream to receive the voice agent's audio
            audio_stream = rtc.AudioStream(track)
            
            # Process audio frames and queue for Twilio
            asyncio.create_task(self._process_agent_audio(audio_stream))
    
    async def _process_agent_audio(self, audio_stream: rtc.AudioStream):
        """Process audio from the voice agent and queue for Twilio."""
        logger.info("🎵 Starting to process voice agent audio stream")
        frame_count = 0

        try:
            async for frame_event in audio_stream:
                if not self.is_connected:
                    logger.warning("❌ Audio bridge disconnected, stopping audio processing")
                    break

                frame = frame_event.frame
                frame_count += 1

                # Log first few frames and then every 100th frame
                if frame_count <= 3 or frame_count % 100 == 0:
                    logger.info(f"🎤 Received audio frame #{frame_count}: {len(frame.data)} samples, {frame.sample_rate}Hz")

                # Convert PCM to μ-law for Twilio
                pcm_data = frame.data.tobytes()
                mulaw_data = self.converter.pcm16_to_mulaw(
                    pcm_data,
                    source_rate=frame.sample_rate
                )

                # Queue for sending to Twilio
                await self.outgoing_audio_queue.put(mulaw_data)

                # Log first few successful queues
                if frame_count <= 3:
                    logger.info(f"✅ Queued audio frame #{frame_count} for Twilio ({len(mulaw_data)} bytes μ-law)")

        except Exception as e:
            logger.error(f"❌ Error processing agent audio after {frame_count} frames: {e}")

        logger.info(f"🎵 Finished processing voice agent audio stream (processed {frame_count} frames total)")
    
    async def _on_disconnected(self):
        """Handle LiveKit room disconnection."""
        logger.info("Disconnected from LiveKit room")
        self.is_connected = False
    
    async def process_twilio_message(self, message: str) -> Optional[str]:
        """
        Process incoming WebSocket message from Twilio.
        
        Returns a response message if one should be sent back, or None.
        """
        try:
            data = json.loads(message)
            event = data.get("event")
            
            if event == "connected":
                logger.info("Twilio WebSocket connected")
                return None
                
            elif event == "start":
                # Call has started, extract stream info
                start_info = data.get("start", {})
                self.stream_sid = start_info.get("streamSid")
                
                call_sid = start_info.get("callSid")
                logger.info(f"Twilio stream started: {self.stream_sid}, call: {call_sid}")
                
                # Connect to LiveKit room now
                if not self.is_connected:
                    await self.connect_to_livekit()
                
                return None
                
            elif event == "media":
                # Incoming audio from Twilio
                media = data.get("media", {})
                payload = media.get("payload", "")

                # INCOMING AUDIO DEBUG LOGGING
                if not hasattr(self, '_incoming_media_count'):
                    self._incoming_media_count = 0
                self._incoming_media_count += 1

                # Log first few media events and every 50th
                if self._incoming_media_count <= 3 or self._incoming_media_count % 50 == 0:
                    logger.info(f"📥 Received media event #{self._incoming_media_count} from Twilio (payload: {len(payload)} chars)")

                if payload and self.is_connected and self.audio_source:
                    try:
                        # Decode base64 μ-law audio
                        mulaw_audio = base64.b64decode(payload)
                        if self._incoming_media_count <= 3:
                            logger.info(f"🔓 Decoded payload: {len(payload)} chars → {len(mulaw_audio)} bytes μ-law")

                        # Convert to PCM for LiveKit
                        pcm_audio = self.converter.mulaw_to_pcm16(mulaw_audio)
                        if self._incoming_media_count <= 3:
                            logger.info(f"🎵 Converted audio: {len(mulaw_audio)} bytes μ-law → {len(pcm_audio)} bytes PCM")

                        # Create audio frame and publish to LiveKit
                        frame = rtc.AudioFrame(
                            data=pcm_audio,
                            sample_rate=AudioConverter.LIVEKIT_SAMPLE_RATE,
                            num_channels=AudioConverter.LIVEKIT_CHANNELS,
                            samples_per_channel=len(pcm_audio) // 2  # 16-bit = 2 bytes per sample
                        )

                        await self.audio_source.capture_frame(frame)
                        if self._incoming_media_count <= 3:
                            logger.info(f"✅ Published audio frame #{self._incoming_media_count} to LiveKit ({frame.samples_per_channel} samples, {frame.sample_rate}Hz)")

                    except Exception as e:
                        logger.error(f"❌ Error processing incoming audio #{self._incoming_media_count}: {e}")
                        import traceback
                        traceback.print_exc()

                elif not payload:
                    if self._incoming_media_count <= 3:
                        logger.warning(f"⚠️ Media event #{self._incoming_media_count} has empty payload")
                elif not self.is_connected:
                    if self._incoming_media_count <= 3:
                        logger.warning(f"⚠️ Media event #{self._incoming_media_count} received but bridge not connected to LiveKit")
                elif not self.audio_source:
                    if self._incoming_media_count <= 3:
                        logger.warning(f"⚠️ Media event #{self._incoming_media_count} received but no audio_source available")
                
                return None
                
            elif event == "stop":
                logger.info("Twilio stream stopped")
                await self.disconnect()
                return None
                
            elif event == "mark":
                # Mark events are acknowledgments
                mark_name = data.get("mark", {}).get("name", "")
                logger.debug(f"Mark received: {mark_name}")
                return None
                
            else:
                logger.debug(f"Unknown Twilio event: {event}")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from Twilio: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing Twilio message: {e}")
            return None
    
    async def get_outgoing_audio(self) -> Optional[str]:
        """
        Get the next audio chunk to send to Twilio.

        Returns base64-encoded μ-law audio wrapped in Twilio media message format.
        """
        try:
            # Use a short timeout to avoid blocking forever
            mulaw_data = await asyncio.wait_for(
                self.outgoing_audio_queue.get(),
                timeout=0.05
            )

            if mulaw_data and self.stream_sid:
                # Log every 50th audio message to avoid spam
                if not hasattr(self, '_audio_send_count'):
                    self._audio_send_count = 0
                self._audio_send_count += 1

                if self._audio_send_count <= 3 or self._audio_send_count % 50 == 0:
                    logger.info(f"📤 Sending audio message #{self._audio_send_count} to Twilio ({len(mulaw_data)} bytes μ-law)")

                message = json.dumps({
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {
                        "payload": base64.b64encode(mulaw_data).decode("ascii")
                    }
                })

                if self._audio_send_count <= 3:
                    logger.info(f"✅ Generated Twilio media message #{self._audio_send_count} ({len(message)} chars)")

                return message
            else:
                if not mulaw_data:
                    logger.debug("🔇 No audio data available")
                if not self.stream_sid:
                    logger.warning("❌ No stream_sid available for sending audio")

        except asyncio.TimeoutError:
            # This is expected when no audio is ready - don't log it
            pass
        except Exception as e:
            logger.error(f"❌ Error getting outgoing audio: {e}")

        return None
    
    async def disconnect(self):
        """Disconnect from LiveKit room and clean up."""
        self.is_connected = False
        
        if self.room:
            await self.room.disconnect()
            self.room = None
        
        self.audio_source = None
        self.local_track = None
        self.stream_sid = None
        
        logger.info(f"TwilioAudioBridge disconnected for room: {self.room_name}")


async def create_livekit_room_for_call(
    room_name: str,
    lead_id: str,
    agent_id: str
) -> bool:
    """
    Create a LiveKit room for an incoming call.
    
    This room will host the Twilio audio bridge and the AIDN voice agent.
    """
    try:
        livekit_url = os.getenv("LIVEKIT_URL")
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")
        
        if not all([livekit_url, api_key, api_secret]):
            logger.error("Missing LiveKit configuration")
            return False
        
        # Create LiveKit API client (new API style)
        lkapi = api.LiveKitAPI(
            url=livekit_url,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Create room with metadata
        room_metadata = json.dumps({
            "lead_id": lead_id,
            "agent_id": agent_id,
            "call_type": "outbound"
        })
        
        async with lkapi:
            await lkapi.room.create_room(api.CreateRoomRequest(
                name=room_name,
                metadata=room_metadata,
                empty_timeout=300,  # 5 minutes
                max_participants=3   # Bridge + Voice Agent + (maybe admin monitor)
            ))
        
        logger.info(f"Created LiveKit room: {room_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create LiveKit room: {e}")
        return False


def generate_stream_twiml(
    websocket_url: str,
    room_name: str,
    lead_id: str,
    agent_id: str
) -> str:
    """
    Generate TwiML response that connects call audio to WebSocket stream.
    
    This is the key to enabling real-time AI voice on phone calls.
    Uses <Start><Stream> with a long pause to keep call alive.
    """
    # Use Twilio's official <Parameter> elements to pass data to WebSocket
    # This is the correct way to pass custom data to Stream WebSockets
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Please hold while I connect you to our agent.</Say>
    <Start>
        <Stream url="{websocket_url}" track="both_tracks">
            <Parameter name="room" value="{room_name}"/>
            <Parameter name="lead_id" value="{lead_id}"/>
            <Parameter name="agent_id" value="{agent_id}"/>
        </Stream>
    </Start>
    <Pause length="120"/>
    <Say voice="Polly.Matthew">Thank you for your time. Goodbye.</Say>
</Response>"""
    
    return twiml

