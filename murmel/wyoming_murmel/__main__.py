import argparse
import asyncio
import functools
import json
import logging
import os
import socket
from pathlib import Path
from urllib.request import Request, urlopen

from wyoming.server import AsyncServer
from .backend import load_backend
from .server import Engine, Handler

LOG = logging.getLogger(__name__)


def validate(options):
    if not 1 <= options.get("beam_size", 4) <= 16:
        raise ValueError("beam_size moet tussen 1 en 16 liggen")
    if not 0 <= options.get("cpu_threads", 0) <= 64:
        raise ValueError("cpu_threads moet tussen 0 en 64 liggen")
    if not isinstance(options.get("log_transcripts", False), bool):
        raise ValueError("log_transcripts moet true of false zijn")
    words = options.get("hotwords", [])
    if not isinstance(words, list) or not all(isinstance(w, str) for w in words):
        raise ValueError("hotwords moet een lijst tekstwaarden zijn")
    import re
    if not re.fullmatch(r"(main|[0-9a-f]{40})", options.get("model_revision", "main")):
        raise ValueError("model_revision moet een volledige commit-SHA zijn")
    return options


def publish_discovery():
    payload = json.dumps({"service": "wyoming", "config": {
        "uri": f"tcp://{socket.gethostname()}:10300"}}).encode()
    request = Request("http://supervisor/discovery", data=payload, headers={
        "Authorization": "Bearer " + os.environ["SUPERVISOR_TOKEN"],
        "Content-Type": "application/json"})
    with urlopen(request, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError("Discovery failed")


async def discovery_loop():
    if not os.environ.get("SUPERVISOR_TOKEN"):
        return
    while True:
        try:
            await asyncio.to_thread(publish_discovery)
            LOG.info("Wyoming-dienst aangemeld bij Home Assistant.")
            return
        except Exception:
            LOG.warning("Discovery tijdelijk niet beschikbaar; nieuwe poging over 30 seconden.")
            await asyncio.sleep(30)


async def run(args):
    options = validate(json.loads(Path(args.options).read_text()))
    try:
        backend = await asyncio.to_thread(load_backend, options, args.data_dir)
    except Exception:
        LOG.error("Model laden mislukt. Controleer modeltoegang, token, netwerk en vrije opslag.")
        raise SystemExit(1) from None
    engine = Engine(backend, log_transcripts=options.get("log_transcripts", False))
    server = AsyncServer.from_uri(args.uri)
    task = asyncio.create_task(server.run(functools.partial(Handler, engine)))
    # Wait until a real describe request succeeds before publishing discovery.
    from wyoming.client import AsyncTcpClient
    from wyoming.info import Describe
    discovery = None
    try:
        for _ in range(100):
            if task.done():
                await task
            try:
                async with AsyncTcpClient("127.0.0.1", int(args.uri.rsplit(":", 1)[1])) as client:
                    await client.write_event(Describe().event())
                    if await asyncio.wait_for(client.read_event(), 2):
                        break
            except (OSError, asyncio.TimeoutError):
                await asyncio.sleep(0.1)
        else:
            raise RuntimeError("Wyoming-server start niet")
        LOG.info("Murmel gereed voor Nederlandse spraakherkenning.")
        discovery = asyncio.create_task(discovery_loop())
        await task
    finally:
        task.cancel()
        if discovery:
            discovery.cancel()
        await asyncio.gather(task, *([discovery] if discovery else []), return_exceptions=True)
        engine.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--options", default="/data/options.json")
    parser.add_argument("--data-dir", default="/data")
    parser.add_argument("--uri", default="tcp://0.0.0.0:10300")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    # Third party HTTP logs must not expose download credentials.
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
