"""SQLAlchemy models for games and moves (TECH_DESIGN.md #5)."""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from db import Base


def utcnow():
    return datetime.now(timezone.utc)


class Game(Base):
    __tablename__ = "games"

    id = Column(String, primary_key=True)
    alias = Column(String, nullable=True)
    player1_color = Column(String, nullable=False)
    player2_color = Column(String, nullable=False)
    status = Column(String, nullable=False, default="in_progress")
    result = Column(String, nullable=True)
    termination = Column(String, nullable=True)
    fen = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    finished_at = Column(DateTime, nullable=True)

    moves = relationship(
        "Move", back_populates="game", order_by="Move.ply", cascade="all, delete-orphan"
    )

    def player_label_for_color(self, color):
        """Map a side ('white'/'black') to its fixed stat label ('player1'/'player2')."""
        if color == self.player1_color:
            return "player1"
        return "player2"


class Move(Base):
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String, ForeignKey("games.id"), nullable=False, index=True)
    ply = Column(Integer, nullable=False)
    move_number = Column(Integer, nullable=False)
    color = Column(String, nullable=False)
    uci = Column(String, nullable=False)
    san = Column(String, nullable=False)

    game = relationship("Game", back_populates="moves")
