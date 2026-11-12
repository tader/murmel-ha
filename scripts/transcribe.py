"""Send a local WAV to Wyoming; prints only when explicitly run by the user."""
import argparse
import asyncio
import time
import wave
from wyoming.client import AsyncTcpClient
from wyoming.asr import Transcribe, Transcript
from wyoming.audio import wav_to_chunks
from wyoming.error import Error

async def run(args):
    start = time.monotonic()
    async with AsyncTcpClient(args.host, args.port) as client:
        await client.write_event(Transcribe(language="nl").event())
        with wave.open(args.wav, "rb") as audio:
            for event in wav_to_chunks(audio, 1024, start_event=True, stop_event=True):
                await client.write_event(event.event())
        event = await asyncio.wait_for(client.read_event(), 180)
        if event is None or Error.is_type(event.type):
            raise SystemExit("Transcription failed")
        print(Transcript.from_event(event).text)
        print(f"Elapsed: {time.monotonic()-start:.2f}s")

parser = argparse.ArgumentParser()
parser.add_argument("wav")
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=10300)
asyncio.run(run(parser.parse_args()))
