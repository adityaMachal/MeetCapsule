import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from scripts.processor import MeetingProcessor
import uuid
import database
import models
from sqlalchemy.orm import Session

# Initialize database
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="MeetCapsule AI API")

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

def run_processing(meeting_id: int, video_path: str):
    """Background task to process the video and update the database."""
    db = database.SessionLocal()
    try:
        meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
        if not meeting:
            print(f"[!] Meeting {meeting_id} not found in database.")
            return

        meeting.status = "PROCESSING"
        db.commit()

        print(f"[*] Background processing started for {meeting.filename}...")
        result = processor.process(video_path)

        if not result:
            meeting.status = "FAILED"
            meeting.error = "Processing failed."
        else:
            meeting.transcript = result.get("transcript")
            meeting.summary = result.get("summary")
            meeting.status = "COMPLETED"
        
        db.commit()
        print(f"[+] Background processing completed for {meeting.filename}.")

    except Exception as e:
        db.rollback()
        meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
        if meeting:
            meeting.status = "FAILED"
            meeting.error = str(e)
            db.commit()
        print(f"[!] Background Server Error: {e}")
    finally:
        db.close()
        if os.path.exists(video_path):
            os.remove(video_path)
            print(f"[*] Cleaned up uploaded video: {video_path}")

@app.get("/")
async def health_check():
    return {"status": "online", "message": "MeetCapsule AI Backend is running"}

@app.get("/meetings")
async def list_meetings(db: Session = Depends(database.get_db)):
    meetings = db.query(models.Meeting).all()
    return [meeting.to_dict() for meeting in meetings]

@app.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: int, db: Session = Depends(database.get_db)):
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting.to_dict()

@app.post("/process")
async def process_video(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    db: Session = Depends(database.get_db)
):
    if not file.filename.endswith((".mp4", ".mkv", ".mov", ".avi")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a video.")

    file_id = str(uuid.uuid4())
    temp_video_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    try:
        with open(temp_video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # CREATE INITIAL RECORD
        new_meeting = models.Meeting(
            filename=file.filename,
            status="PENDING"
        )
        db.add(new_meeting)
        db.commit()
        db.refresh(new_meeting)

        # ADD TO BACKGROUND TASKS
        background_tasks.add_task(run_processing, new_meeting.id, temp_video_path)

        return new_meeting.to_dict()

    except Exception as e:
        db.rollback()
        print(f"[!] Server Error during upload: {e}")
        # Clean up file if it was created but background task didn't start
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
