import pandas as pd
import pdfplumber
import io
import re
from data.curriculum import KMITL_CS_COURSES, CURRICULUM_KNOWLEDGE
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

def setup_rag_chain():
    print("กำลังเตรียมข้อมูล AI...")
    df = pd.read_csv("data/jobs_master_final.csv")
    
    df = df.dropna(subset=['Title', 'Description'])
    
    df['Company'] = df['Company'].fillna("-")
    df['Location'] = df['Location'].fillna("-")
    df['Link'] = df['Link'].fillna("#")
    
    df['combined_text'] = (
        "Job Title: " + df['Title'].astype(str) + "\n" +
        "Company: " + df['Company'].astype(str) + "\n" +
        "Location: " + df['Location'].astype(str) + "\n" +
        "Job Link: " + df['Link'].astype(str) + "\n" +
        "Job Description: " + df['Description'].astype(str)
    )
    
    documents = df['combined_text'].tolist()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)
    docs = text_splitter.create_documents(documents)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    vector_store = FAISS.from_documents(docs, embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 10})

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3, google_api_key=api_key)
    
    all_courses_str = "\n".join(CURRICULUM_KNOWLEDGE)

    template = """
    คุณเป็นผู้ช่วยหางานอัจฉริยะสำหรับนักศึกษา Computer Science สจล.
    คุณเข้าใจตัวย่อในสายงาน IT ดังนี้:
    - SA = System Analyst (นักวิเคราะห์ระบบ)
    - SE = Software Engineer (วิศวกรซอฟต์แวร์) หรือ System Engineer
    - QA = Quality Assurance (ผู้ตรวจสอบคุณภาพซอฟต์แวร์)
    - Tester = Software Tester
    - PM = Project Manager (ผู้จัดการโครงการ)
    - BA = Business Analyst (นักวิเคราะห์ธุรกิจ)
    - FE = Front-end Developer
    - BE = Back-end Developer
    - FS = Full-stack Developer
    - Infra = Infrastructure
    - DE = Data Engineer
    - DS = Data Scientist

    รายวิชาทั้งหมดในหลักสูตร สจล. (บังคับใช้อ้างอิงเวลาแนะนำวิชาเรียน):
    {all_courses_str}
    
    บริบทจากฐานข้อมูล (ความรู้เรื่องงานและวิชาเรียน):
    {context}
    
    ข้อมูลเกรดของผู้ใช้ (Transcript) - ถ้ามีให้ใช้วิเคราะห์เพื่อแนะนำงานหรือวิชาเรียนเพิ่มเติม:
    {transcript_info}
    
    คำถาม: {question}
    
    กฎ:
    1. ตอบอย่างเป็นกันเอง กระชับ และตรงประเด็นที่สุด ไม่อ้อมค้อม
    2. หากผู้ใช้พิมพ์ตัวย่อ ให้แปลความหมายตามพจนานุกรมข้างต้นก่อนค้นหา
    3. โฟกัสคำตอบขั้นสุด:
       - หากผู้ใช้ถามว่า "งาน...คืออะไร" หรือ "ทำหน้าที่อะไร" ให้ตอบ **เฉพาะความหมายและหน้าที่รับผิดชอบเท่านั้น** ห้ามแนะนำทักษะหรือวิชาเรียนเด็ดขาด
       - หากผู้ใช้ถามเรื่อง "ทักษะ (Skills)" ให้ตอบ **เฉพาะทักษะเท่านั้น** ห้ามอธิบายหน้าที่การทำงานหรือแนะนำวิชาเรียน
    4. การคัดกรองวิชา: หากผู้ใช้ถามว่า "ควรเรียนวิชาอะไร" ให้คัดเลือกเฉพาะวิชาที่ **ตรงและสำคัญที่สุดจริงๆ ไม่เกิน 3-5 วิชาเท่านั้น** พร้อมบอกรหัสและชื่อวิชา (ห้ามลิสต์วิชามาทั้งหมดเด็ดขาด เลือกเฉพาะ Top Matches)
    5. หากผู้ใช้ถามเรื่องความเหมาะสม ให้ใช้ข้อมูล Transcript มาวิเคราะห์ว่าเขาเด่นทักษะอะไรจากวิชาที่ได้เกรดดี
    6. หากมีการอ้างอิง Transcript ให้สรุปข้อมูลเป็นตาราง HTML เสมอ โดยบังคับใช้โครงสร้างแท็กแบบนี้เท่านั้น (ห้ามใช้ Markdown Table) และต้องอยู่ในชั้นที่เล็กที่สุด(*ต้องถูกครอบตามกฏข้อ10 เสมอ*) เพื่อใช้ประกอบการอธิบายให้ด้านนั้นๆ ห้ามเอาวิชาที่จะอ้างมาจับรวมกันเป็นตารางเดียว:
       <div class="table-wrapper">
         <table>
           <thead>
             <tr><th>ชื่อวิชา</th><th>เกรด</th><th>ความเกี่ยวข้องกับงาน</th></tr>
           </thead>
           <tbody>
             <tr><td>[รหัส ชื่อวิชา]</td><td>[เกรด]</td><td>[คำอธิบายสั้นๆ เข้าใจง่าย]</td></tr>
           </tbody>
         </table>
       </div>
    7. คำอธิบายในชั้นที่เล็กที่สุด หากเป็นประโยคยาวให้แบ่งประโยคเป็นแต่ละ Bullet
    8. ถ้าข้อมูลไม่มีใน Context ให้ตอบว่า 'ขออภัย ในฐานข้อมูลงานที่ดึงมาไม่มีข้อมูลเรื่องนี้'
    9. การจัดรูปแบบ UI (สำคัญมาก): ห้ามใช้ Markdown (เช่น **ข้อความ** หรือ ***) ในการเน้นคำหรือทำหัวข้อเด็ดขาด 
       - หากต้องการทำหัวข้อหรือเน้นตัวหนา ให้ใช้แท็ก HTML <b>ชื่อหัวข้อ</b> เท่านั้น
       - เมื่อจบหัวข้อ ให้ขึ้นบรรทัดใหม่เพื่อเขียนเนื้อหาต่อ "โดยห้ามเว้นบรรทัดว่าง" (ห้ามพิมพ์ Enter 2 ครั้ง) ให้เนื้อหาอยู่บรรทัดถัดไปแบบติดกันเลย
    10. สำคัญมาก: ไม่ว่าผู้ใช้จะถามถึงเรื่องอะไร (เช่น หน้าที่การทำงาน, ทักษะ, ตำแหน่งงาน, หรือวิชาเรียน) หากคำตอบมีการแจกแจงเป็น "หัวข้อย่อยพร้อมคำอธิบาย" ให้บังคับใช้ HTML tag <details> และ <summary> ครอบหัวข้อย่อยแต่ละอันเสมอ
       - <summary> ให้ใส่ชื่อหัวข้อย่อยสั้นๆ (เช่น ชื่อหน้าที่, ชื่อทักษะ, รหัสและชื่อวิชา)
       - ภายใน <summary> หากเป็นตำแหน่งงาน **บังคับให้ทำเป็น Link ที่กดได้** โดยใช้แท็ก <a href="[Job Link ที่ดึงมา]" target="_blank">[ชื่อตำแหน่งงาน]</a> ตามด้วยชื่อบริษัท (ถ้ามี)
       - ด้านใน <details> ให้ใส่คำอธิบายความสัมพันธ์หรือรายละเอียด
       - ห้ามมี <summary> เกิน 1 อันใน 1 <details> ให้รวมชื่อบริษัทไว้ในบรรทัดเดียวกันเลย
       - ไม่ต้องครอบที่หัวข้อใหญ่ (หมวดหมู่หลัก) ให้ครอบเฉพาะระดับย่อยเท่านั้น
       - ห้ามใช้ Bullet point (* หรือ -) กับหัวข้อที่มีคำอธิบายยาวๆ ให้เปลี่ยนมาใช้กล่อง <details> แทนทั้งหมด
       รูปแบบที่ต้องใช้:
       <details>
         <summary><a href="[Job Link]" target="_blank">[ชื่อตำแหน่งงาน]</a> - [ชื่อบริษัท ถ้ามี]</summary>
         <summary>[สถานที่ของงาน ถ้ามี] สั้นๆ</summary>
         [รายละเอียดทั้งหมดใส่ตรงนี้]
       </details>
    """
    prompt = ChatPromptTemplate.from_template(template)

    rag_chain = (
        {
            "context": (lambda x: x["question"]) | retriever | (lambda docs: "\n\n".join(d.page_content for d in docs)),
            "question": lambda x: x["question"],
            "transcript_info": lambda x: x["transcript_info"],
            "all_courses_str": lambda x: all_courses_str
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain

rag_chain = setup_rag_chain()

def extract_courses_from_pdf(file_bytes):
    extracted_data = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            pattern = r'(\d{8})\s+(.*?)\s+(\d)\s+([A-D][+]?|[FS]|W)'
            matches = re.findall(pattern, text)
            for m in matches:
                code, title, credit, grade = m
                course_info = KMITL_CS_COURSES.get(code, {"name": title.strip()})
                extracted_data.append({
                    "code": code,
                    "title": course_info["name"],
                    "grade": grade.strip()
                })
    return extracted_data