let socket;

document.addEventListener('DOMContentLoaded', () => {
  connectWebSocket();

  document.getElementById('sendBtn').addEventListener('click', sendTranscript);
});

function connectWebSocket() {
  const statusEl = document.getElementById('connectionStatus');
  
  // Connect to local backend
  socket = new WebSocket('ws://localhost:8000/ws/transcription');

  socket.onopen = () => {
    statusEl.textContent = 'Connected';
    statusEl.classList.add('connected');
  };

  socket.onclose = () => {
    statusEl.textContent = 'Disconnected';
    statusEl.classList.remove('connected');
    setTimeout(connectWebSocket, 3000); // Auto reconnect
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleMessage(data);
  };
}

function sendTranscript() {
  const input = document.getElementById('transcriptInput');
  const text = input.value.trim();
  
  if (text && socket && socket.readyState === WebSocket.OPEN) {
    const payload = {
      text: text,
      timestamp: new Date().toISOString()
    };
    socket.send(JSON.stringify(payload));
    input.value = ''; // Clear input
  }
}

function handleMessage(data) {
  const feed = document.getElementById('feed');
  
  if (data.type === 'insight') {
    const card = document.createElement('div');
    card.className = 'card';
    
    const knowledge = data.knowledge.retrieval_results[0];
    const question = data.tutor.content;
    
    card.innerHTML = `
      <div class="card-title">💡 Topic: ${knowledge.keyword}</div>
      <div class="card-content">
        ${knowledge.info}
      </div>
      <div class="tutor-question">
        <strong>Tutor asks:</strong> ${question}
      </div>
    `;
    
    feed.prepend(card); // Add to top
  }
}
