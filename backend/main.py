from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from models import ChatRequest
from services import rag_chain, extract_courses_from_pdf

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/upload_transcript")
async def upload_transcript(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        courses = extract_courses_from_pdf(file_bytes)
        return {"status": "success", "courses": courses}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/chat")
async def chat_with_bot(request: ChatRequest):
    try:
        transcript_str = "ไม่มีข้อมูล Transcript"
        if request.transcript_data:
            transcript_str = "\n".join([f"- {c.code} {c.title}: เกรด {c.grade}" for c in request.transcript_data])

        response = rag_chain.invoke({
            "question": request.question,
            "transcript_info": transcript_str
        })
        return {"answer": response}
    except Exception as e:
        return {"answer": f"เกิดข้อผิดพลาด: {str(e)}"}