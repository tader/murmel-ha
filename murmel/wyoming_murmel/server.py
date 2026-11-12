"""Bounded Wyoming STT server with an injectable inference backend."""
import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioStart, AudioChunk, AudioStop, AudioChunkConverter
from wyoming.error import Error
from wyoming.info import Info, Describe, AsrProgram, AsrModel, Attribution
from wyoming.server import AsyncEventHandler

from . import __version__

MAX_BYTES = 60 * 16000 * 2


def service_info():
    attribution = Attribution(name="The AI Factory", url="https://murmel.nl")
    return Info(asr=[AsrProgram(
        name="Murmel", attribution=attribution, installed=True,
        description="Lokale Nederlandse spraakherkenning", version=__version__,
        models=[AsrModel(name="murmel-flash-m-v5", attribution=attribution,
                         installed=True, description="Nederlandse spraakherkenning",
                         version="5", languages=["nl"])],
    )])


class Engine:
    def __init__(self, backend):
        self.backend = backend
        self.active = 0
        self.executor = ThreadPoolExecutor(max_workers=1)

    async def transcribe(self, audio):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self.backend, audio)

    def close(self):
        self.executor.shutdown(wait=True, cancel_futures=True)


class Handler(AsyncEventHandler):
    def __init__(self, engine, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = engine
        self.buffer = bytearray()
        self.reserved = False
        self.started = False
        self.converter = AudioChunkConverter(rate=16000, width=2, channels=1)

    def release(self):
        if self.reserved:
            self.engine.active -= 1
            self.reserved = False
        self.buffer.clear()
        self.started = False
        self.converter = AudioChunkConverter(rate=16000, width=2, channels=1)

    async def disconnect(self):
        self.release()

    async def fail(self, code, message):
        await self.write_event(Error(code=code, text=message).event())
        self.release()
        return False

    async def handle_event(self, event):
        try:
            if Describe.is_type(event.type):
                await self.write_event(service_info().event())
            elif Transcribe.is_type(event.type):
                if Transcribe.from_event(event).language not in (None, "nl", "nl-NL", "nl-BE"):
                    return await self.fail("unsupported-language", "Selecteer Nederlands.")
            elif AudioStart.is_type(event.type):
                if self.started:
                    return await self.fail("invalid-audio", "Audio is al gestart.")
                if self.engine.active >= 4:
                    return await self.fail("busy", "De spraakherkenner is bezet.")
                start = AudioStart.from_event(event)
                if start.rate not in (8000, 16000, 22050, 24000, 44100, 48000) or start.width not in (1, 2, 3, 4) or start.channels not in (1, 2):
                    return await self.fail("invalid-audio", "Gebruik 16 kHz, 16-bit mono PCM.")
                self.input_format = (start.rate, start.width, start.channels)
                self.engine.active += 1
                self.reserved = self.started = True
            elif AudioChunk.is_type(event.type):
                chunk = AudioChunk.from_event(event)
                if not self.started or (chunk.rate, chunk.width, chunk.channels) != self.input_format or len(chunk.audio) % (chunk.width * chunk.channels):
                    return await self.fail("invalid-audio", "Ongeldige PCM-audio.")
                if len(chunk.audio) > 60 * chunk.rate * chunk.width * chunk.channels:
                    return await self.fail("audio-too-long", "Maximaal 60 seconden audio.")
                chunk = self.converter.convert(chunk)
                if len(self.buffer) + len(chunk.audio) > MAX_BYTES:
                    return await self.fail("audio-too-long", "Maximaal 60 seconden audio.")
                self.buffer.extend(chunk.audio)
            elif AudioStop.is_type(event.type):
                if not self.started:
                    return await self.fail("invalid-audio", "Audio is niet gestart.")
                audio = np.frombuffer(bytes(self.buffer), dtype="<i2").astype(np.float32) / 32768.0
                text = await self.engine.transcribe(audio) if len(audio) else ""
                await self.write_event(Transcript(text=text).event())
                self.release()
                return False
            return True
        except (KeyError, ValueError, TypeError):
            return await self.fail("invalid-request", "Ongeldig Wyoming-verzoek.")
        except Exception:
            return await self.fail("transcription-failed", "Spraakherkenning mislukt.")
