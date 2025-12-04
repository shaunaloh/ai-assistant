from sqlalchemy import Column, Integer, Text
from .database import Base

class ChatMessage(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_input = Column(Text)
    bot_response = Column(Text)