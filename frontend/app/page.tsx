"use client";

import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileVideo, CheckCircle, Clock, BookOpen, Brain, ChevronRight, X } from "lucide-react";

import ReactMarkdown from "react-markdown";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [meetings, setMeetings] = useState<any[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedMeeting, setSelectedMeeting] = useState<any>(null);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch past meetings on load
  useEffect(() => {
    fetchMeetings();
  }, []);

  const fetchMeetings = async () => {
    try {
      const res = await axios.get(`${API_BASE}/meetings`);
      setMeetings(res.data); // Backend now returns newest first
    } catch (err) {
      console.error("Failed to fetch meetings");
    }
  };

  const pollMeetingStatus = async (meetingId: number) => {
    const pollInterval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_BASE}/meetings/${meetingId}`);
        const updatedMeeting = res.data;

        // Update meetings list
        setMeetings(prev => prev.map(m => m.id === meetingId ? updatedMeeting : m));

        // Update selected meeting if it's the one being polled
        setSelectedMeeting((prev: any) => prev?.id === meetingId ? updatedMeeting : prev);

        if (updatedMeeting.status === "COMPLETED" || updatedMeeting.status === "FAILED") {
          clearInterval(pollInterval);
          if (updatedMeeting.status === "FAILED") {
            setError(`Processing failed for ${updatedMeeting.filename}: ${updatedMeeting.error}`);
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
        clearInterval(pollInterval);
      }
    }, 3000); // Poll every 3 seconds
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError("");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API_BASE}/process`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const initialMeeting = res.data;
      setMeetings([initialMeeting, ...meetings]);
      setSelectedMeeting(initialMeeting);
      
      // Start polling for this meeting
      pollMeetingStatus(initialMeeting.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Upload failed. Check if server is running.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="animate-fade">
      {/* Header */}
      <div style={{ marginBottom: "3rem" }}>
        <h1>MeetCapsule AI</h1>
        <p className="subtitle">Transform long meeting recordings into structured, actionable intelligence.</p>
      </div>

      {/* Main Grid */}
      <div style={{ 
        display: "grid", 
        gridTemplateColumns: selectedMeeting ? "1fr 1.5fr" : "1fr", 
        gap: "2rem", 
        transition: "all 0.5s ease" 
      }}>
        
        {/* Left Column: List & Upload */}
        <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
          
          {/* Upload Card */}
          <div className="card" style={{ textAlign: "center", position: "relative", overflow: "hidden" }}>
            <div 
              onClick={() => !isUploading && fileInputRef.current?.click()}
              style={{ padding: "2rem", border: "2px dashed var(--border)", borderRadius: "12px", cursor: isUploading ? "not-allowed" : "pointer", opacity: isUploading ? 0.7 : 1 }}
            >
              <Upload size={32} style={{ color: "var(--primary)", marginBottom: "1rem" }} />
              <h3>{isUploading ? "Uploading video..." : "Upload Meeting Video"}</h3>
              <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>MP4, MOV, MKV up to 500MB</p>
              {isUploading && (
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 10, ease: "linear" }}
                  style={{ 
                    position: "absolute", 
                    bottom: 0, 
                    left: 0, 
                    height: "4px", 
                    background: "var(--primary)" 
                  }}
                />
              )}
            </div>
            <input 
              type="file" 
              hidden 
              ref={fileInputRef} 
              onChange={handleFileUpload} 
              accept="video/*" 
            />
            {error && <p style={{ color: "var(--error)", marginTop: "1rem", fontSize: "0.875rem" }}>{error}</p>}
          </div>

          {/* Meeting List */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <h2 style={{ fontSize: "1.25rem", marginBottom: "0.5rem" }}>Meeting Vault</h2>
            {meetings.length === 0 && !isUploading && (
               <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>No meetings processed yet.</p>
            )}
            {meetings.map((m) => (
              <div 
                key={m.id} 
                className={`card meeting-card ${selectedMeeting?.id === m.id ? 'active' : ''}`}
                onClick={() => setSelectedMeeting(m)}
                style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: "1rem", padding: "16px" }}
              >
                <div style={{ background: "rgba(99, 102, 241, 0.1)", padding: "10px", borderRadius: "8px" }}>
                  {m.status === "COMPLETED" ? (
                    <FileVideo size={20} color="var(--primary)" />
                  ) : m.status === "FAILED" ? (
                    <X size={20} color="var(--error)" />
                  ) : (
                    <Clock size={20} color="var(--warning)" className="animate-spin" />
                  )}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <p style={{ fontWeight: 600, fontSize: "0.95rem" }}>{m.filename}</p>
                    {m.status !== "COMPLETED" && (
                      <span style={{ 
                        fontSize: "0.65rem", 
                        padding: "2px 6px", 
                        borderRadius: "4px", 
                        background: m.status === "FAILED" ? "rgba(239, 68, 68, 0.1)" : "rgba(245, 158, 11, 0.1)",
                        color: m.status === "FAILED" ? "var(--error)" : "var(--warning)",
                        textTransform: "uppercase",
                        fontWeight: 700
                      }}>
                        {m.status}
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {new Date(m.created_at).toLocaleDateString()}
                  </p>
                </div>
                <ChevronRight size={16} color="var(--text-muted)" />
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Detail View */}
        <AnimatePresence>
          {selectedMeeting && (
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="card" 
              style={{ height: "fit-content", minHeight: "600px" }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
                <h2 style={{ fontSize: "1.5rem" }}>Meeting Intelligence</h2>
                <X 
                  size={20} 
                  style={{ cursor: "pointer", color: "var(--text-muted)" }} 
                  onClick={() => setSelectedMeeting(null)} 
                />
              </div>

              {selectedMeeting.status === "COMPLETED" ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}>
                  <section>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem", color: "var(--primary)" }}>
                      <Brain size={20} />
                      <h3 style={{ fontSize: "1.1rem" }}>Detailed AI Summary</h3>
                    </div>
                    <div 
                      className="summary-content"
                      style={{ color: "var(--text)", fontSize: "0.95rem" }}
                    >
                      <ReactMarkdown>{selectedMeeting.summary}</ReactMarkdown>
                    </div>
                  </section>

                  <hr style={{ border: "none", borderTop: "1px solid var(--border)" }} />

                  <section>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem", color: "var(--text-muted)" }}>
                      <BookOpen size={20} />
                      <h3 style={{ fontSize: "1.1rem" }}>Full Transcript</h3>
                    </div>
                    <div style={{ 
                      maxHeight: "300px", 
                      overflowY: "auto", 
                      fontSize: "0.875rem", 
                      color: "var(--text-muted)", 
                      padding: "1rem", 
                      background: "var(--surface-light)", 
                      borderRadius: "8px" 
                    }}>
                      {selectedMeeting.transcript}
                    </div>
                  </section>
                </div>
              ) : selectedMeeting.status === "FAILED" ? (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "400px", gap: "1rem" }}>
                  <X size={48} color="var(--error)" />
                  <h3 style={{ color: "var(--error)" }}>Processing Failed</h3>
                  <p style={{ color: "var(--text-muted)", textAlign: "center", maxWidth: "300px" }}>
                    {selectedMeeting.error || "An unknown error occurred during processing."}
                  </p>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "400px", gap: "1rem" }}>
                  <Clock size={48} color="var(--primary)" className="animate-spin" />
                  <h3 style={{ color: "var(--primary)", textTransform: "capitalize" }}>
                    {selectedMeeting.status.toLowerCase()}...
                  </h3>
                  <p style={{ color: "var(--text-muted)", textAlign: "center", maxWidth: "300px" }}>
                    {selectedMeeting.status === "PENDING" && "Waiting to start processing..."}
                    {selectedMeeting.status === "EXTRACTING" && "Converting video to audio for analysis..."}
                    {selectedMeeting.status === "TRANSCRIBING" && "Converting speech to text using Gemini 1.5 Flash..."}
                    {selectedMeeting.status === "SUMMARIZING" && "Generating your detailed intelligence summary..."}
                  </p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <style jsx>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin {
          animation: spin 2s linear infinite;
        }
        .meeting-card.active {
          border-color: var(--primary);
          background: rgba(99, 102, 241, 0.05);
        }
        .summary-content :global(h1), 
        .summary-content :global(h2), 
        .summary-content :global(h3) {
          margin-top: 1.5rem;
          margin-bottom: 0.75rem;
          color: white;
          border-bottom: 1px solid var(--border);
          padding-bottom: 0.25rem;
        }
        .summary-content :global(ul), .summary-content :global(ol) {
          margin-left: 1.5rem;
          margin-bottom: 1rem;
        }
        .summary-content :global(li) {
          margin-bottom: 0.75rem;
          padding-left: 0.25rem;
        }
        .summary-content :global(p) {
          margin-bottom: 1rem;
          line-height: 1.7;
        }
        .summary-content :global(strong) {
          color: var(--primary);
        }
      `}</style>
    </div>
  );
}

