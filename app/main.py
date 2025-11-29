from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from . import models, database, websocket_manager, auth, crud
from .routers import users, spaces, messages
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:5173",  # Frontend URL
    "http://127.0.0.1:5173",  # Frontend URL
    "https://chat-app-frontend-build.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(spaces.router)
app.include_router(messages.router)

@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=database.engine)

@app.websocket("/ws/{space_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    space_id: int,
    token: str,
    db: Session = Depends(database.get_db)
):
    try:
        current_user = auth.get_current_user(db=db, token=token)
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # TODO: Verify if current_user is a member of space_id

    await websocket_manager.manager.connect(websocket, space_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Messages are already encrypted on the client-side
            # The backend just broadcasts them
            await websocket_manager.manager.broadcast(data, space_id)
    except WebSocketDisconnect:
        websocket_manager.manager.disconnect(websocket, space_id)
