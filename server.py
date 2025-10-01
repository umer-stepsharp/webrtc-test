import asyncio
import aiohttp
from aiohttp import web
import os

from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.base_transport import TransportParams
from pipecat.frames.frames import AudioRawFrame, EndFrame

async def handle_webrtc(request):
    print("WebRTC connection received")
    
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    print("WebSocket connected")
    
    transport = None
    
    try:
        connection = SmallWebRTCConnection(ws)
        params = TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            transcription_enabled=False,
        )
        
        transport = SmallWebRTCTransport(connection, params)
        print("Transport created")
        
        input_queue = transport.input()
        
        async def audio_loopback():
            print("Audio loopback started")
            try:
                while True:
                    frame = await input_queue.get()
                    print(f"Got frame: {type(frame).__name__}")
                    
                    if isinstance(frame, EndFrame):
                        break
                    
                    if isinstance(frame, AudioRawFrame):
                        print(f"Audio: {len(frame.audio)} bytes")
                        await transport.send_audio(frame)
                        
            except asyncio.CancelledError:
                print("Loopback cancelled")
            except Exception as e:
                print(f"Loopback error: {e}")
        
        loopback_task = asyncio.create_task(audio_loopback())
        
        async for msg in ws:
            print(f"WS message: {msg.type}")
            if msg.type == aiohttp.WSMsgType.ERROR:
                break
        
        print("WebSocket closed")
        loopback_task.cancel()
        await loopback_task
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Cleanup")
        if transport:
            await transport.cleanup()
    
    return ws

async def serve_html(request):
    filename = request.match_info.get('filename', 'client.html')
    if not filename.endswith('.html'):
        filename += '.html'
    
    path = os.path.join(os.path.dirname(__file__), filename)
    
    if not os.path.exists(path):
        return web.Response(text="404 Not Found", status=404)
    
    with open(path, 'r') as f:
        return web.Response(text=f.read(), content_type='text/html')

async def main():
    app = web.Application()
    app.router.add_get('/', serve_html)
    app.router.add_get('/{filename}.html', serve_html)
    app.router.add_get('/ws', handle_webrtc)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    
    print("Server running at http://localhost:8080")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())