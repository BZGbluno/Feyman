import asyncio
import json
import base64
import websockets
import numpy as np
import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter

load_dotenv(".env")
REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SILENCE_CHUNKS = 10
router = APIRouter()


def is_silent(audio_bytes: bytes, threshold=1000) -> bool:
    # PCM16
    audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
    return np.abs(audio_np).mean() < threshold


@router.websocket("/voice")
async def voice_chat(client_ws: WebSocket):
    await client_ws.accept()
    print("Client connected")

    buffer = []
    silence_counter = 0

    try:
        # Connect to OpenAI Realtime
        async with websockets.connect(
            "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview",
            additional_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1",
            },
        ) as openai_ws:
            await openai_ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "instructions": "You are a tutor and you are meant to provide helpful explanations in english"
                }
            }))
            
            
            print("Connected to OpenAI")
            async def forward_client_audio():
                while True:
                    audio_base64 = await client_ws.receive_text()

                    # You can decode for any local processing if needed
                    audio_bytes = base64.b64decode(audio_base64)

                    # Just forward audio to OpenAI
                    await openai_ws.send(json.dumps({
                        "type": "input_audio_buffer.append",
                        "audio": audio_base64
                    }))
            # async def forward_client_audio():
            #     nonlocal buffer, silence_counter
            #     while True:
            #         audio_base64 = await client_ws.receive_text()
            #         audio_bytes = base64.b64decode(audio_base64)

            #         # Optionally, check silence
            #         if is_silent(audio_bytes):
            #             silence_counter += 1
            #         else:
            #             silence_counter = 0

            #         # Send chunk to OpenAI
            #         await openai_ws.send(json.dumps({
            #             "type": "input_audio_buffer.append",
            #             "audio": audio_base64
            #         }))

            #         # If enough silence, commit & request response
            #         if silence_counter >= SILENCE_CHUNKS:
            #             await openai_ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
            #             await openai_ws.send(json.dumps({
            #                 "type": "response.create",
            #                 "response": {
            #                     "modalities": ["text"],
            #                     "instructions": "Transcribe and respond"
            #                 }
            #             }))
            #             buffer = []
            #             silence_counter = 0

            async def forward_openai_responses():
                while True:
                    message = await openai_ws.recv()
                    data = json.loads(message)
                    # Send any text responses to client
                    # print(data['text'])
                    # if "response.audio_transcript.done" == data["type"]:
                    # await client_ws.send_text(json.dumps(data))
                    # if data["type"] == "output_audio_buffer.delta":
                    #     audio_b64 = data["audio"]  # already base64-encoded PCM16
                    #     await client_ws.send_text(json.dumps({
                    #         "type": "audio",
                    #         "audio": audio_b64
                    #     }))
                    if data["type"] == "response.audio.delta":
                        await client_ws.send_text(json.dumps({
                            "type": "audio_delta",
                            "delta": data["delta"]
                        
                        }))

            
            # allows for multitrheading of sending/recieving to client
            await asyncio.gather(
                forward_client_audio(),
                forward_openai_responses()
            )

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print("Error:", e)