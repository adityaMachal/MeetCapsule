from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base
from datetime import datetime

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String(50), default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "transcript": self.transcript,
            "summary": self.summary,
            "status": self.status,
            "error": self.error,
            "created_at": self.created_at
        }
