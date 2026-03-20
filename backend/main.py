import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from scripts.processor import MeetingProcessor
import uuid
import database
import models
from sqlalchemy.orm import Session

# Initialize database
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="MeetCapsule AI API")

# ... rest of your code ...
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processor = MeetingProcessor()
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def health_check():
    return {"status": "online", "message": "MeetCapsule AI Backend is running"}

@app.get("/meetings")
async def list_meetings(db: Session = Depends(database.get_db)):
    meetings = db.query(models.Meeting).all()
    return [meeting.to_dict() for meeting in meetings]

@app.post("/process")
async def process_video(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    if not file.filename.endswith((".mp4", ".mkv", ".mov", ".avi")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a video.")

    file_id = str(uuid.uuid4())
    temp_video_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    try:
        with open(temp_video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"[*] Starting processing for {file.filename}...")
        result = processor.process(temp_video_path)
        
        if not result:
            raise HTTPException(status_code=500, detail="Processing failed.")

        # SAVE TO DATABASE
        new_meeting = models.Meeting(
            filename=file.filename,
            transcript=result["transcript"],
            summary=result["summary"]
        )
        db.add(new_meeting)
        db.commit()
        db.refresh(new_meeting)

        return new_meeting.to_dict()

    except Exception as e:
        db.rollback()
        print(f"[!] Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            print(f"[*] Cleaned up uploaded video: {temp_video_path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
