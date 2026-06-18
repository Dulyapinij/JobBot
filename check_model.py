import google.generativeai as genai

# ใส่ API Key ของคุณตรงนี้
GOOGLE_API_KEY = "AIzaSyArufpJJB7XfdNvxlro7popG5v2wS4kfuY"

genai.configure(api_key=GOOGLE_API_KEY)

print("🔍 กำลังค้นหาโมเดลทั้งหมดที่ API Key ของคุณสามารถใช้งานได้...")
print("-" * 50)

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ ใช้งานได้: {m.name}")
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")