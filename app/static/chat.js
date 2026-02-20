const socket = io();

const chatBox = document.getElementById("chat-box");

let currentBotDiv = null;

socket.on("connect", () => {
    console.log("Connected to server");
});

socket.on("chat_token", (token) => {
    if (!currentBotDiv) {
        currentBotDiv = document.createElement("div");
        currentBotDiv.className = "chat-bot";
        chatBox.appendChild(currentBotDiv);
    }
    currentBotDiv.innerHTML += token;
    chatBox.scrollTop = chatBox.scrollHeight;
});

socket.on("chat_complete", () => {
    currentBotDiv = null;
});

function sendMessage() {
    const input = document.getElementById("message");
    const message = input.value;
    if (!message) return;

    const userDiv = document.createElement("div");
    userDiv.className = "chat-user";
    userDiv.innerText = message;
    chatBox.appendChild(userDiv);

    socket.emit("chat_message", { question: message });

    input.value = "";
}
