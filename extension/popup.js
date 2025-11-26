let socket;
let recognition;
let isRecording = false;

document.addEventListener('DOMContentLoaded', () => {
  connectWebSocket();
  setupSpeechRecognition();

  document.getElementById('startBtn').addEventListener('click', startRecording);
      document.getElementById('stopBtn').addEventListener('click', stopRecording);
  document.getElementById('closeNotesBtn').addEventListener('click', () => {
    document.getElementById('notesModal').style.display = 'none';
  });
});

function setupSpeechRecognition() {
  if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    // 設定為繁體中文 (台灣)
    recognition.lang = 'cmn-Hant-TW'; 

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
          sendTranscript(event.results[i][0].transcript);
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      
      const display = document.getElementById('transcriptInput');
      // Append new text instead of overwriting, to keep history
      if (finalTranscript) {
          display.value += finalTranscript + '\n';
      }
      display.scrollTop = display.scrollHeight;
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error", event.error);
      updateStatus(`錯誤: ${event.error}`);
    };

    recognition.onend = () => {
      if (isRecording) {
        recognition.start();
      } else {
        // updateStatus("已停止"); // Handled by stop button
      }
    };
  } else {
    alert("您的瀏覽器不支援 Web Speech API");
  }
}

function startRecording() {
  if (recognition && !isRecording) {
    recognition.start();
    isRecording = true;
    document.getElementById('startBtn').disabled = true;
    document.getElementById('stopBtn').disabled = false;
    updateStatus("正在聆聽中...");
  }
}

function stopRecording() {
    if (recognition && isRecording) {
      isRecording = false;
      recognition.stop();
      document.getElementById('startBtn').disabled = false;
      document.getElementById('stopBtn').disabled = true;
      updateStatus("已停止，正在生成講義...");
      
      generateLectureNotes(); // Call generation
    }
  }
  
  async function generateLectureNotes() {
    try {
      // Show Modal with Loading
      const modal = document.getElementById('notesModal');
      const body = document.getElementById('notesBody');
      modal.style.display = 'flex';
      body.innerHTML = '<div style="text-align:center; padding: 20px;">正在整理筆記，請稍候...<br>(AI 正在分析整堂課的內容)</div>';
  
      const response = await fetch('http://localhost:8000/generate_notes', {
        method: 'POST'
      });
      
      const data = await response.json();
      const markdown = data.notes;
      
          // Parse Markdown to HTML
          if (typeof SimpleMarkdown !== 'undefined') {
              body.innerHTML = SimpleMarkdown.parse(markdown);
          } else {
              // Fallback
              body.innerHTML = `<pre>${markdown}</pre>`;
          }      
      updateStatus("講義生成完畢");
      
    } catch (e) {
      console.error("Failed to generate notes:", e);
      document.getElementById('notesBody').innerHTML = "生成失敗，請檢查後端連線。";
      updateStatus("生成失敗");
    }
  }
  
function updateStatus(msg) {
  document.getElementById('statusIndicator').textContent = msg;
}

function connectWebSocket() {
  const statusEl = document.getElementById('connectionStatus');
  
  // Connect to local backend
  socket = new WebSocket('ws://localhost:8000/ws/transcription');

  socket.onopen = () => {
    statusEl.textContent = '已連線';
    statusEl.classList.add('connected');
  };

  socket.onclose = () => {
    statusEl.textContent = '未連線';
    statusEl.classList.remove('connected');
    setTimeout(connectWebSocket, 5000);
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleMessage(data);
  };
}

function sendTranscript(text) {
  const cleanText = text.trim();
  if (cleanText && socket && socket.readyState === WebSocket.OPEN) {
    console.log("Sending:", cleanText);
    updateStatus("🤖 AI 分析中..."); // Update status
    const payload = {
      text: cleanText,
      timestamp: new Date().toISOString()
    };
    socket.send(JSON.stringify(payload));
  }
}

function handleMessage(data) {
  const feed = document.getElementById('feed');
  console.log("Received from Backend:", data); // Debug log
  
  if (data.type === 'insight') {
    updateStatus("✨ 發現重點！");
    const card = document.createElement('div');
    card.className = 'card';
    
    const knowledge = data.knowledge.retrieval_results[0];
    const question = data.tutor.content;
    
    card.innerHTML = `
      <div class="card-title">主題: ${knowledge.keyword}</div>
      <div class="card-content">
        ${knowledge.info}
      </div>
      <div class="tutor-question">
        <strong>導師提問:</strong> ${question}
      </div>
    `;
    
    feed.prepend(card);
  } else if (data.type === 'ack') {
    updateStatus("✅ 已接收 (無新重點)");
    // Optional: Flash a small log
    console.log("Agent ignored this segment.");
  }
}