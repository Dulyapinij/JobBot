let globalTranscriptData = null;

function toggleTheme() {
    const body = document.body;
    body.classList.toggle('dark-theme');
    
    const themeBtn = document.getElementById('themeToggle');
    if (body.classList.contains('dark-theme')) {
        themeBtn.innerText = 'โหมดสว่าง (Light Mode)';
    } else {
        themeBtn.innerText = 'โหมดมืด (Dark Mode)';
    }
}

async function uploadTranscript() {
    const fileInput = document.getElementById("transcriptFile");
    const statusDiv = document.getElementById("uploadStatus");
    
    if (!fileInput.files[0]) {
        alert("กรุณาเลือกไฟล์ PDF ก่อนครับ");
        return;
    }

    statusDiv.innerHTML = "⏳ กำลังประมวลผล...";
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch("http://localhost:8000/api/upload_transcript", {
            method: "POST",
            body: formData
        });
        const result = await response.json();

        if (result.status === "success") {
            globalTranscriptData = result.courses;
            statusDiv.innerHTML = "อัปโหลดสำเร็จ!";
        }
    } catch (error) {
        statusDiv.innerHTML = "เกิดข้อผิดพลาด";
    }
}

async function sendMessage() {
    const inputField = document.getElementById("userInput");
    const chatBox = document.getElementById("chatBox");
    const question = inputField.value.trim();
    if (!question) return;

    chatBox.innerHTML += `<div class="message user-msg"><b>You:</b> ${question}</div>`;
    inputField.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;

    const loadingId = "loading-" + Date.now();
    chatBox.innerHTML += `<div class="message bot-msg" id="${loadingId}"><b>Bot:</b> กำลังคิด... ⏳</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch("http://localhost:8000/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                question: question,
                transcript_data: globalTranscriptData 
            })
        });
        const data = await response.json();

        document.getElementById(loadingId).remove();
        
        const formattedAnswer = data.answer
            .replace(/<details>\s+/g, "<details>")
            .replace(/<\/summary>\s+/g, "</summary>")
            .replace(/\s+<\/details>/g, "</details>");
        chatBox.innerHTML += `<div class="message bot-msg"><b>Bot:</b> ${formattedAnswer}</div>`;
    } catch (error) {
        document.getElementById(loadingId).remove();
        chatBox.innerHTML += `<div class="message bot-msg" style="color: red;"><b>Bot:</b> เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ครับ</div>`;
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

function handleKeyPress(event) {
    if (event.key === "Enter") sendMessage();
}