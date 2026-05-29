# Relation Warning System - API Server
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.analyzer import create_analyzer


app = FastAPI(title="Relation Warning API")

# Enable CORS for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global analyzer
analyzer = create_analyzer()


# Request models
class MessageInput(BaseModel):
    turn: int
    speaker: str  # "我" or "对方"
    content: str


class AnalysisRequest(BaseModel):
    dialogue: list[MessageInput]
    my_color: str = ""
    their_color: str = ""


class QuickCheckRequest(BaseModel):
    message: str
    my_color: str = ""
    their_color: str = ""


# Routes
@app.get("/")
def root():
    return {"message": "Relation Warning API", "version": "0.1"}


@app.post("/analyze")
def analyze(req: AnalysisRequest) -> dict[str, Any]:
    """Analyze dialogue for conflict signals."""
    dialogue = [
        {"turn": m.turn, "speaker": m.speaker, "content": m.content}
        for m in req.dialogue
    ]

    result = analyzer.analyze(
        dialogue=dialogue,
        my_color=req.my_color,
        their_color=req.their_color,
    )

    return result.to_dict()


@app.get("/quick")
def quick_check(q: str, my_color: str = "", their_color: str = ""):
    """Quick single message check."""
    signal = analyzer.quick_check(q, my_color, their_color)

    if signal:
        return signal.to_dict()
    else:
        return {"risk": "low", "message": "无明显冲突"}


# CLI helper
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)