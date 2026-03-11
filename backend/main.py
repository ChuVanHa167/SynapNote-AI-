from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routers import auth, meetings, chat, integrations

app = FastAPI(
    title="SynapNote AI Backend",
    description="API for Authentication, Meetings Analysis, AI Chat and Integrations.",
    version="1.0.0"
)

# CORS config for local dev (Next.js is on 3000/3001)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(meetings.router)
app.include_router(chat.router)
app.include_router(integrations.router)

@app.get("/", tags=["Health"])
async def root():
    return {"message": "SynapNote AI API is running. Go to /docs for Swagger UI."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
