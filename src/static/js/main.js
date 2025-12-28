const messagesContainer = document.getElementById('messages');
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');

// メッセージを追加
function addMessage(content, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);

    // 最新メッセージまでスクロール
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ローディングインジケーター表示
function showLoading() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = 'loading-message';

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.innerHTML = '<span></span><span></span><span></span>';

    messageDiv.appendChild(loadingDiv);
    messagesContainer.appendChild(messageDiv);

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ローディングインジケーター削除
function hideLoading() {
    const loadingMessage = document.getElementById('loading-message');
    if (loadingMessage) {
        loadingMessage.remove();
    }
}

// チャット送信処理
async function sendMessage(message) {
    try {
        sendButton.disabled = true;

        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'エラーが発生しました');
        }

        hideLoading();
        addMessage(data.response, false);

    } catch (error) {
        hideLoading();
        addMessage(`エラー: ${error.message}`, false);
    } finally {
        sendButton.disabled = false;
    }
}

// フォーム送信イベント
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const message = userInput.value.trim();
    if (!message) return;

    // ユーザーメッセージを表示
    addMessage(message, true);
    userInput.value = '';

    // ローディング表示
    showLoading();

    // メッセージ送信
    await sendMessage(message);
});

// Enterキーで送信（Shift+Enterで改行）
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});
