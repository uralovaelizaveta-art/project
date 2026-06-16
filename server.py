# server.py
import base64
import json
import os
import time
import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import numpy as np
from starlette.concurrency import run_in_threadpool

from pose_realtime import init_model, RealtimeSession

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Инициализация модели при запуске
MODEL_PATH = os.getenv("MODEL_PATH", "pose_landmarker_lite.task")
print(f"[Server] MODEL_PATH: {MODEL_PATH}")
print(f"[Server] Model exists: {os.path.exists(MODEL_PATH)}")

try:
    print("[Server] Initializing model...")
    init_model(MODEL_PATH)
    print("[Server] Model initialized successfully")
except Exception as e:
    print(f"[Server] ERROR initializing model: {e}")
    import traceback
    traceback.print_exc()

def decode_frame(base64_str: str) -> np.ndarray:
    img_bytes = base64.b64decode(base64_str)
    return decode_frame_bytes(img_bytes)

def decode_frame_bytes(img_bytes: bytes) -> np.ndarray:
    encoded = np.frombuffer(img_bytes, dtype=np.uint8)
    frame_bgr = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if frame_bgr is None:
        raise ValueError("Invalid image data")
    return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = id(websocket)
    print(f"[WS {client_id}] Client connecting...")
    await websocket.accept()
    print(f"[WS {client_id}] Client connected")

    # Создаем одну сессию для этого подключения
    from pose_realtime import RealtimeSession
    session = RealtimeSession(MODEL_PATH)

    frame_count = 0
    try:
        while True:
            try:
                message = await websocket.receive()
                start_time = time.perf_counter()
                if message.get("bytes") is not None:
                    frame = decode_frame_bytes(message["bytes"])
                elif message.get("text") is not None:
                    payload = json.loads(message["text"])
                    frame = decode_frame(payload["frame"])
                else:
                    raise WebSocketDisconnect()
                frame_count += 1
                # Используем сессию, а не process_frame()
                result = await run_in_threadpool(session.process_frame, frame)
                process_time = time.perf_counter() - start_time
                result["processing_ms"] = round(process_time * 1000)

                if frame_count % 10 == 0:
                    print(f"[WS {client_id}] Frame {frame_count}, process time: {process_time:.2f}s")

                await websocket.send_json({
                    "type": "result",
                    "data": result
                })
            except json.JSONDecodeError as e:
                print(f"[WS {client_id}] JSON decode error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
            except KeyError as e:
                print(f"[WS {client_id}] Missing key: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Missing frame data: {e}"
                })
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"[WS {client_id}] Processing error: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                except:
                    pass
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS {client_id}] WebSocket disconnected: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await websocket.close()
        except:
            pass
        print(f"[WS {client_id}] Connection closed (frames processed: {frame_count})")

@app.get("/health")
async def health():
    return {"status": "ok"}
