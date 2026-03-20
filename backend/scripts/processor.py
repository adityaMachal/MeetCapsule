import os
import subprocess
import requests
from google import genai
from dotenv import load_dotenv
import time

# Load environment variables from backend/.env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class MeetingProcessor:
    def __init__(self):
        # API Keys
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        # Initialize new Google GenAI Client
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            print("[!] Warning: No Gemini API Key found in environment.")
        
        # Paths
        self.temp_dir = os.path.join(os.path.dirname(__file__), '..', 'temp_audio')
        os.makedirs(self.temp_dir, exist_ok=True)

    def extract_audio(self, video_path):
        """Extracts mono audio at 16k for optimal processing."""
        print(f"[*] Extracting audio from: {video_path}")
        audio_output = os.path.join(self.temp_dir, f"temp_{int(time.time())}.mp3")
        
        try:
            command = [
                'ffmpeg', '-i', video_path,
                '-vn', '-acodec', 'libmp3lame',
                '-ac', '1', '-ar', '16000',
                '-y', audio_output
            ]
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return audio_output
        except Exception as e:
            print(f"[!] FFmpeg Error: {e}")
            return None

    def transcribe_with_gemini(self, audio_path):
        """Transcribes audio using the new Gemini SDK (Handles 1hr+ meetings)."""
        print(f"[*] Uploading {os.path.basename(audio_path)} to Google AI...")
        
        try:
            # 1. Upload the file to Google
            with open(audio_path, "rb") as f:
                uploaded_file = self.client.files.upload(file=audio_path)
            
            # 2. Wait for processing
            print("[*] Processing audio", end="")
            while uploaded_file.state == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(3)
                uploaded_file = self.client.files.get(name=uploaded_file.name)
            
            if uploaded_file.state == "FAILED":
                raise Exception("Google file processing failed.")

            print("\n[*] Audio processed. Transcribing...")
            
            # 3. Use Gemini to transcribe
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    "Please provide a word-for-word transcript of this audio. Do not summarize yet.",
                    uploaded_file
                ]
            )
            
            # 4. Cleanup Google's storage
            self.client.files.delete(name=uploaded_file.name)
            
            return response.text
            
        except Exception as e:
            print(f"[!] Gemini Transcription Error: {e}")
            return None

    def summarize(self, transcript):
        """Summarizes transcript using Gemini with high detail."""
        print("[*] Generating Detailed AI Summary (300-400 words)...")
        
        prompt = f"""
        You are an expert Meeting Intelligence Assistant. 
        Analyze the following meeting transcript and provide a HIGHLY DETAILED and ELABORATED structured summary.
        The final summary should be between 300 and 400 words long.
        
        Structure the output as follows:
        1. **Main Topic**: A detailed one-paragraph summary.
        2. **Key Concepts & Technical Deep-Dive**: Elaborated bullet points.
        3. **Action Items & Next Steps**: Comprehensive list.
        4. **Detailed Q&A Summary**: Specific questions and context-rich answers.

        Transcript:
        {transcript}
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"[!] Summarization Error: {e}")
            return None

    def process(self, video_path):
        """Full pipeline optimized for long 1-hour+ meetings."""
        start_time = time.time()
        
        # 1. Extraction
        audio_path = self.extract_audio(video_path)
        if not audio_path: return None
        
        # 2. Transcription
        transcript = self.transcribe_with_gemini(audio_path)
        
        # 3. Summarization
        summary = self.summarize(transcript) if transcript else None
        
        # 4. Cleanup Local File
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"[*] Cleaned up local temporary audio.")

        end_time = time.time()
        print(f"[+] Processing complete in {end_time - start_time:.2f} seconds.")
        
        return {
            "transcript": transcript,
            "summary": summary
        }

if __name__ == "__main__":
    processor = MeetingProcessor()
    # Path to a test file if running locally
    test_video = "scripts/test_vid.mp4"
    if os.path.exists(test_video):
        result = processor.process(test_video)
        if result: print(result['summary'])
