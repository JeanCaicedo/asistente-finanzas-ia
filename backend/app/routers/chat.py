"""Endpoint del chat de IA anclado a datos reales."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..db import get_db
from ..schemas import ChatAnswer, ChatRequest
from ..services import chat as chat_service

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatAnswer)
def chat(body: ChatRequest, conn: sqlite3.Connection = Depends(get_db)):
    return chat_service.answer(conn, body.question)
