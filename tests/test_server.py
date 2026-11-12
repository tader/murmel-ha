import asyncio
import unittest
import numpy as np
from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioStart, AudioChunk, AudioStop
from wyoming.client import AsyncTcpClient
from wyoming.info import Describe, Info
from wyoming.error import Error
from wyoming.server import AsyncServer
from functools import partial
from wyoming_murmel.server import Engine, Handler
from wyoming_murmel.__main__ import validate

class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.audio = []
        def backend(audio):
            self.audio.append(audio)
            return "Doe de lamp aan."
        self.engine = Engine(backend)
        # Bind port zero through the actual Wyoming server factory.
        self.server = AsyncServer.from_uri("tcp://127.0.0.1:0")
        self.task = asyncio.create_task(self.server.run(partial(Handler, self.engine)))
        # The public TCP server exposes the asyncio server via ._server.
        for _ in range(100):
            await asyncio.sleep(.01)
            srv = getattr(self.server, "_server", None)
            if srv and srv.sockets:
                self.port = srv.sockets[0].getsockname()[1]
                break
        else:
            raise RuntimeError("Test server did not bind")

    async def asyncTearDown(self):
        await self.server.stop()
        self.task.cancel()
        await asyncio.gather(self.task, return_exceptions=True)
        self.engine.close()

    async def request(self, events):
        async with AsyncTcpClient("127.0.0.1", self.port) as client:
            for event in events:
                await client.write_event(event.event())
            return await asyncio.wait_for(client.read_event(), 3)

    async def test_describe(self):
        event = await self.request([Describe()])
        self.assertEqual(Info.from_event(event).asr[0].models[0].languages, ["nl"])

    async def test_transcript_and_pcm(self):
        event = await self.request([Transcribe(language="nl"), AudioStart(16000, 2, 1),
            AudioChunk(16000, 2, 1, b"\x00\x40" * 1600), AudioStop()])
        self.assertEqual(Transcript.from_event(event).text, "Doe de lamp aan.")
        self.assertEqual(self.audio[0].dtype, np.float32)
        self.assertAlmostEqual(float(self.audio[0][0]), .5)

    async def test_empty(self):
        event = await self.request([AudioStart(16000, 2, 1), AudioStop()])
        self.assertEqual(Transcript.from_event(event).text, "")
        self.assertFalse(self.audio)

    async def test_invalid_sequence(self):
        event = await self.request([AudioStop()])
        self.assertTrue(Error.is_type(event.type))

    async def test_unsupported_language(self):
        event = await self.request([Transcribe(language="de")])
        self.assertTrue(Error.is_type(event.type))

    async def test_resampling(self):
        await self.request([AudioStart(8000, 2, 1), AudioChunk(8000, 2, 1, b"\x00\x10" * 800), AudioStop()])
        self.assertTrue(1500 < len(self.audio[0]) <= 1600)

    async def test_disconnect_releases_slot(self):
        async with AsyncTcpClient("127.0.0.1", self.port) as client:
            await client.write_event(AudioStart(16000, 2, 1).event())
            await asyncio.sleep(.05)
        await asyncio.sleep(.05)
        self.assertEqual(self.engine.active, 0)

    async def test_backend_failure(self):
        def fail(audio):
            raise RuntimeError("private text must never be returned")
        self.engine.backend = fail
        event = await self.request([AudioStart(16000, 2, 1), AudioChunk(16000, 2, 1, b"\0\0"), AudioStop()])
        self.assertEqual(Error.from_event(event).code, "transcription-failed")

    async def test_overload(self):
        self.engine.active = 4
        event = await self.request([AudioStart(16000, 2, 1)])
        self.assertEqual(Error.from_event(event).code, "busy")
        self.engine.active = 0

    async def test_duration_limit(self):
        from unittest.mock import patch
        with patch("wyoming_murmel.server.MAX_BYTES", 2):
            event = await self.request([AudioStart(16000, 2, 1),
                AudioChunk(16000, 2, 1, b"\0\0" * 2)])
        self.assertEqual(Error.from_event(event).code, "audio-too-long")

class ConfigTests(unittest.TestCase):
    def test_defaults(self):
        validate({})
    def test_invalid_beam(self):
        with self.assertRaises(ValueError):
            validate({"beam_size": 0})
