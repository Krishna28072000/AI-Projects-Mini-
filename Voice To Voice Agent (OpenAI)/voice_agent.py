"""
Voice-to-voice assistant CLI (OpenAI Agents SDK + microphone + speakers).

Setup (Windows Command Prompt):
  set OPENAI_API_KEY=sk-...
  python -m venv .venv
  .venv\\Scripts\\activate
  pip install -r requirements.txt
  python voice_agent.py

First prompt: press Enter to start recording, or type q and Enter to quit.
While "Listening...": speak, then press Enter to stop and send audio to the agent.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

import numpy as np
import sounddevice as sd

try:
    from agents import Agent  # pyright: ignore[reportMissingImports]
    from agents.voice import (  # pyright: ignore[reportMissingImports]
        AudioInput,
        SingleAgentVoiceWorkflow,
        TTSModelSettings,
        VoicePipeline,
        VoicePipelineConfig,
    )
except ModuleNotFoundError as exc:
    name = getattr(exc, "name", "") or ""
    if name in ("agents", "agents.voice") or "agents.voice" in str(exc):
        print(
            "Could not import OpenAI Agents voice API (`agents.voice`).\n\n"
            "Install the SDK with the voice extra (use the same Python you use to run this script):\n"
            '  python -m pip install -U "openai-agents[voice]"\n\n'
            "If this error persists, another library may be shadowing the `agents` package.\n"
            'Check with: python -c "import agents; print(agents.__file__)"\n'
            "(expect a path under site-packages from the `openai-agents` distribution.)\n",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    raise

# TTS output from the voice pipeline uses this rate (matches SDK / OpenAI voice).
#  OPENAI_TTS_SAMPLE_RATE = 24_000  #Normal Standard rate 
OPENAI_TTS_SAMPLE_RATE = 26_400  #Normal Standard rate 


def _maybe_load_dotenv() -> None:
    # Optional: load OPENAI_API_KEY from a local .env if present.
    # This helps when running from an IDE that doesn't inherit shell env vars.
    try:
        from dotenv import load_dotenv  # type: ignore[import-not-found]
    except Exception:
        return
    load_dotenv(override=False)


def require_openai_api_key() -> None:
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print(
            "Missing OPENAI_API_KEY. In Command Prompt run:\n"
            "  set OPENAI_API_KEY=sk-your-key-here\n"
            "then run this script again.",
            file=sys.stderr,
        )
        sys.exit(1)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Voice-to-voice assistant (OpenAI Agents SDK).")
    p.add_argument(
        "--api-key",
        dest="api_key",
        default=None,
        help="OpenAI API key (overrides OPENAI_API_KEY env var).",
    )
    return p.parse_args(argv)


def build_agent() -> Agent:
    return Agent(
        name="Assistant",
        instructions=(
            "Repeat the user's question back to them, and answer it. Note that the user is speaking "
            "with you via a voice interface, although you are reading and writing text to respond. "
            "Nonetheless, ensure that your written response is easily translatable to voice."
        ),
        model="gpt-4.1-nano",
    )


def build_pipeline(agent: Agent) -> VoicePipeline:
    custom_tts = TTSModelSettings(
        instructions=(
            "Personality: upbeat, friendly, persuasive guide.\n"
            "Tone: Friendly, clear, and reassuring, creating a calm atmosphere and making "
            "the listener feel confident and comfortable.\n"
            "Pronunciation: Clear, articulate, and steady, ensuring each instruction is "
            "easily understood while maintaining a natural, conversational flow.\n"
            "Tempo: Speak relatively fast, include brief pauses and after before questions.\n"
            "Emotion: Warm and supportive, conveying empathy and care, ensuring the listener "
            "feels guided and safe throughout the journey."
        )
    )
    config = VoicePipelineConfig(tts_settings=custom_tts)
    workflow = SingleAgentVoiceWorkflow(agent)
    return VoicePipeline(workflow=workflow, config=config)


async def record_until_enter(sample_rate: int) -> np.ndarray:
    recorded_chunks: list[np.ndarray] = []

    def callback(indata, frames, time, status) -> None:
        if status:
            print(status, file=sys.stderr)
        recorded_chunks.append(indata.copy())

    print("Listening... Press Enter when you are done speaking.")
    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype=np.int16,
        callback=callback,
    ):
        await asyncio.to_thread(input)

    if not recorded_chunks:
        return np.empty((0, 1), dtype=np.int16)
    return np.concatenate(recorded_chunks, axis=0)


async def collect_and_play_response(result) -> None:
    response_chunks: list[np.ndarray] = []
    async for event in result.stream():
        if event.type == "voice_stream_event_audio":
            response_chunks.append(event.data)

    if not response_chunks:
        print("No audio returned from the pipeline.", file=sys.stderr)
        return

    audio = np.concatenate(response_chunks, axis=0)
    sd.play(audio, samplerate=OPENAI_TTS_SAMPLE_RATE)
    sd.wait()


async def voice_assistant_loop(pipeline: VoicePipeline, input_device: dict) -> None:
    sample_rate = int(input_device["default_samplerate"])

    while True:
        cmd = await asyncio.to_thread(
            input,
            "Press Enter to speak (or type 'q' to exit): ",
        )
        if cmd.strip().lower() == "q":
            print("Exiting.")
            break

        recording = await record_until_enter(sample_rate)
        if recording.size == 0:
            print("No audio captured; try again.")
            continue

        channels = int(recording.shape[1]) if recording.ndim == 2 else 1
        audio_input = AudioInput(
            buffer=recording,
            frame_rate=sample_rate,
            channels=channels,
        )

        print("Processing...")
        result = await pipeline.run(audio_input=audio_input)

        print("Assistant is responding...")
        await collect_and_play_response(result)
        print("---")


def main() -> None:
    args = parse_args(sys.argv[1:])
    _maybe_load_dotenv()
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
    require_openai_api_key()

    input_device = sd.query_devices(kind="input")
    output_device = sd.query_devices(kind="output")
    print(f"Input device:  {input_device['name']} ({int(input_device['default_samplerate'])} Hz)")
    print(f"Output device: {output_device['name']} ({int(output_device['default_samplerate'])} Hz)")

    agent = build_agent()
    pipeline = build_pipeline(agent)
    asyncio.run(voice_assistant_loop(pipeline, input_device))


if __name__ == "__main__":
    main()
