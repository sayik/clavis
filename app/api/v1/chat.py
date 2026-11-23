"""Here chat backend comes
- websocket
- verification of chat data
- validation
- llm is connected here
- chat data is logged
-

Once doctor logs in the chat -
"""

from fastapi import (
    WebSocket,
    APIRouter,
    WebSocketDisconnect,
    WebSocketException,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import HTMLResponse
from typing import Annotated
from sqlalchemy.orm import Session
import asyncio

# from app.auth.dependencies import get_current_user_ws
from app.db.models import User
from app.db.init_db import get_db
from app.exception import InternalServerException

router = APIRouter(prefix="/chat", tags=["conversations", "consultations"])


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/chat/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@router.get("/ws/token")
@router.get("/")
async def get():
    return HTMLResponse(html)


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


# ... html template code from above ...


# @router.websocket("/ws")
# async def websocket_endpoint(
#     websocket: WebSocket, user: Annotated[User, get_current_user_ws]
# ):
#     await manager.connect(websocket)

#     try:
#         while True:
#             data = await websocket.receive_text()
#             await manager.broadcast(f"Someone said: {data}")
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         print("Client disconnected")
#     except Exception as e:
#         await websocket.send_json({"error": str(e)})
#         await websocket.close(code=1011)


"""class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), default=generate_uuid, unique=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    message_type = Column(String(20), default="text")  # text, image, video, file
    file_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="messages")
    room = relationship("ChatRoom", back_populates="messages")"""
