import os
import requests
from flask import Flask, jsonify, render_template_string, request

TOKEN = os.environ.get("DISCORD_TOKEN")
API_BASE = "https://discord.com/api/v10"

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Discord Web Client</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-primary: #313338;
    --bg-secondary: #2b2d31;
    --bg-tertiary: #1e1f22;
    --text-normal: #dbdee1;
    --text-muted: #949ba4;
    --header-primary: #f2f3f5;
    --brand: #5865f2;
    --embed-bg: #2b2d31;
    --divider: #4e50587a;
    --danger: #da373c;
  }
  * { box-sizing: border-box; scrollbar-width: thin; scrollbar-color: #1a1b1e transparent; }
  body { margin: 0; font-family: 'Noto Sans JP', sans-serif; background: var(--bg-primary); color: var(--text-normal); display: flex; height: 100vh; overflow: hidden; font-size: 16px; }
  
  ::-webkit-scrollbar { width: 8px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #1a1b1e; border-radius: 4px; }

  #server-bar { width: 72px; background: var(--bg-tertiary); display: flex; flex-direction: column; align-items: center; padding: 12px 0; gap: 8px; flex-shrink: 0; z-index: 2; }
  .server-icon { width: 48px; height: 48px; border-radius: 50%; background-color: var(--bg-primary); color: var(--text-normal); display: flex; justify-content: center; align-items: center; font-weight: bold; cursor: pointer; transition: 0.2s ease; background-size: cover; background-position: center; }
  .server-icon:hover, .server-icon.active { border-radius: 16px; background-color: var(--brand); color: #fff; }
  
  #channels { width: 240px; background: var(--bg-secondary); display: flex; flex-direction: column; flex-shrink: 0; }
  .header { height: 48px; padding: 0 16px; font-weight: 700; color: var(--header-primary); display: flex; align-items: center; border-bottom: 1px solid var(--bg-tertiary); font-size: 15px; flex-shrink: 0; justify-content: space-between; }
  
  .btn-icon { background: transparent; border: none; color: var(--text-muted); cursor: pointer; font-size: 14px; padding: 4px; border-radius: 4px; }
  .btn-icon:hover { color: var(--text-normal); background: rgba(255,255,255,0.1); }
  .btn-danger:hover { color: var(--danger); }

  .list { flex: 1; overflow-y: auto; padding: 12px 8px; display: flex; flex-direction: column; gap: 2px; }
  .channel-item { padding: 6px 8px; border-radius: 4px; cursor: pointer; color: var(--text-muted); font-size: 15px; font-weight: 500; display: flex; align-items: center; justify-content: space-between; }
  .channel-item:hover { background: rgba(78, 80, 88, 0.3); color: var(--text-normal); }
  .channel-item.active { background: rgba(78, 80, 88, 0.6); color: #fff; }
  
  #chat { flex: 1; display: flex; flex-direction: column; background: var(--bg-primary); min-width: 0; }
  #messages { flex: 1; overflow-y: auto; padding: 16px 0 16px 0; display: flex; flex-direction: column; }
  
  .msg-wrapper { display: flex; padding: 2px 16px 2px 72px; position: relative; margin-top: 0; group; }
  .msg-wrapper.first { margin-top: 17px; }
  .msg-wrapper:hover { background: rgba(2, 2, 2, 0.06); }
  
  .msg-avatar { position: absolute; left: 16px; top: 2px; width: 40px; height: 40px; border-radius: 50%; background-size: cover; background-position: center; }
  .msg-body { flex: 1; min-width: 0; }
  .msg-header { display: flex; align-items: baseline; gap: 8px; margin-bottom: 2px; }
  .msg-author { font-weight: 500; color: var(--header-primary); font-size: 16px; }
  .msg-time { font-size: 12px; color: var(--text-muted); }
  .msg-content { color: var(--text-normal); font-size: 15px; line-height: 1.375rem; white-space: pre-wrap; word-break: break-word; }
  
  /* メッセージのホバーメニュー */
  .msg-actions { position: absolute; right: 16px; top: -10px; background: var(--bg-primary); border: 1px solid var(--bg-tertiary); border-radius: 4px; display: none; padding: 2px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
  .msg-wrapper:hover .msg-actions { display: flex; gap: 4px; }
  .msg-action-btn { background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 4px 8px; border-radius: 2px; font-size: 12px; }
  .msg-action-btn:hover { background: var(--brand); color: white; }
  .msg-action-btn.delete:hover { background: var(--danger); }

  /* 入力エリア */
  .chat-input-container { padding: 0 16px 24px; position: relative; }
  .chat-input-wrapper { background: #383a40; border-radius: 8px; display: flex; align-items: center; padding: 10px 16px; }
  .chat-input-wrapper input { flex: 1; background: transparent; border: none; color: var(--text-normal); font-size: 15px; outline: none; }
  .chat-input-wrapper input::placeholder { color: var(--text-muted); }
  
  #members { width: 240px; background: var(--bg-secondary); display: flex; flex-direction: column; flex-shrink: 0; border-left: 1px solid var(--bg-tertiary); }
  .member-item { display: flex; align-items: center; gap: 12px; padding: 6px 8px; margin: 0 8px; border-radius: 4px; color: var(--text-normal); }
</style>
</head>
<body>
<div id="server-bar"></div>
<div id="channels">
  <div class="header">
    <span id="server-name">サーバーを選択</span>
    <button class="btn-icon btn-danger" onclick="leaveServer()" title="このサーバーからBotを退出させる">🚪</button>
  </div>
  <div id="channel-list" class="list"></div>
</div>
<div id="chat">
  <div class="header">
    <span id="current-channel-name"># チャンネル未選択</span>
    <button class="btn-icon" onclick="loadMessages(currentChannelId)" title="ログを手動更新">🔄 更新</button>
  </div>
  <div id="messages"></div>
  <div class="chat-input-container">
    <div class="chat-input-wrapper">
      <input type="text" id="chat-input" placeholder="メッセージを送信 (Enterで送信)" onkeypress="handleEnter(event)">
    </div>
  </div>
</div>
<div id="members">
  <div class="header">メンバー</div>
  <div id="member-list-container" class="list"></div>
</div>

<script>
  let currentGuildId = null;
  let currentChannelId = null;
  let botUserId = null;

  async function api(method, path, body = null) {
    const options = { method };
    if (body) {
      options.headers = { 'Content-Type': 'application/json' };
      options.body = JSON.stringify(body);
    }
    try {
      const res = await fetch('/api' + path, options);
      if (res.status === 204) return { success: true };
      return await res.json();
    } catch(e) {
      return { error: e.message };
    }
  }

  // 初期化：Bot自身のIDを取得
  async function init() {
    const me = await api('GET', '/users/@me');
    if(!me.error) botUserId = me.id;
    loadServers();
  }

  function getAvatarUrl(user) {
    if (user.avatar) return `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png?size=128`;
    const index = user.discriminator !== "0" ? parseInt(user.discriminator) % 5 : Number(BigInt(user.id) >> 22n) % 6;
    return `https://cdn.discordapp.com/embed/avatars/${index}.png`;
  }

  function escapeHtml(text) {
    if(!text) return "";
    return text.replace(/[&<>"']/g, m => ({'&': '&amp;','<': '&lt;','>': '&gt;','"': '&quot;',"'": '&#39;'})[m]);
  }

  async function loadServers() {
    const bar = document.getElementById('server-bar');
    bar.innerHTML = '';
    const servers = await api('GET', '/users/@me/guilds');
    if (servers.error) return;
    
    servers.forEach(s => {
      const div = document.createElement('div');
      div.className = 'server-icon';
      div.title = s.name;
      if (s.icon) div.style.backgroundImage = `url(https://cdn.discordapp.com/icons/${s.id}/${s.icon}.png?size=128)`;
      else div.textContent = s.name.charAt(0);
      
      div.onclick = () => {
        document.querySelectorAll('.server-icon').forEach(e => e.classList.remove('active'));
        div.classList.add('active');
        currentGuildId = s.id;
        document.getElementById('server-name').textContent = s.name;
        loadChannels(s.id);
        loadMembers(s.id);
      };
      bar.appendChild(div);
    });
  }

  async function loadChannels(guildId) {
    const list = document.getElementById('channel-list');
    list.innerHTML = '';
    const channels = await api('GET', `/guilds/${guildId}/channels`);
    if(channels.error || !Array.isArray(channels)) return;
    
    channels.filter(c => c.type === 0 || c.type === 5).sort((a,b) => a.position - b.position).forEach(c => {
      const div = document.createElement('div');
      div.className = 'channel-item';
      div.innerHTML = `
        <span># ${escapeHtml(c.name)}</span>
        <button class="btn-icon" onclick="createInvite('${c.id}', event)" title="招待リンクを作成">🔗</button>
      `;
      div.onclick = (e) => {
        if(e.target.tagName === 'BUTTON') return; // ボタン押下時は切り替えない
        document.querySelectorAll('.channel-item').forEach(e => e.classList.remove('active'));
        div.classList.add('active');
        currentChannelId = c.id;
        document.getElementById('current-channel-name').textContent = `# ${c.name}`;
        loadMessages(c.id);
      };
      list.appendChild(div);
    });
  }

  async function loadMembers(guildId) {
    const list = document.getElementById('member-list-container');
    list.innerHTML = '';
    const members = await api('GET', `/guilds/${guildId}/members?limit=1000`);
    if (members.error || !Array.isArray(members)) return;
    
    members.forEach(m => {
      const div = document.createElement('div');
      div.className = 'member-item';
      div.innerHTML = `
        <img src="${getAvatarUrl(m.user)}" style="width:32px; height:32px; border-radius:50%;">
        <span style="font-size:15px;">${escapeHtml(m.nick || m.user.global_name || m.user.username)}</span>
      `;
      list.appendChild(div);
    });
  }

  async function loadMessages(channelId) {
    if(!channelId) return;
    const list = document.getElementById('messages');
    const msgs = await api('GET', `/channels/${channelId}/messages?limit=50`);
    list.innerHTML = '';
    if (!Array.isArray(msgs)) return;
    
    const reversedMsgs = [...msgs].reverse();
    let prevAuthorId = null;

    reversedMsgs.forEach(m => {
      const isConsecutive = (prevAuthorId === m.author.id);
      const div = document.createElement('div');
      div.className = `msg-wrapper ${isConsecutive ? 'consecutive' : 'first'}`;
      
      const content = `<div class="msg-content">${escapeHtml(m.content)}</div>`;
      
      // 編集はBot自身のメッセージのみ、削除は権限があれば可能（ここではUI上両方表示）
      const actions = `
        <div class="msg-actions">
          ${m.author.id === botUserId ? `<button class="msg-action-btn" onclick="editMessage('${m.id}', \`${escapeHtml(m.content)}\`)">編集</button>` : ''}
          <button class="msg-action-btn delete" onclick="deleteMessage('${m.id}')">削除</button>
        </div>
      `;

      if (isConsecutive) {
        div.innerHTML = `<div class="msg-body">${content}</div>${actions}`;
      } else {
        div.innerHTML = `
          <div class="msg-avatar" style="background-image: url('${getAvatarUrl(m.author)}')"></div>
          <div class="msg-body">
            <div class="msg-header">
              <span class="msg-author">${escapeHtml(m.author.global_name || m.author.username)}</span>
            </div>
            ${content}
          </div>
          ${actions}
        `;
      }
      list.appendChild(div);
      prevAuthorId = m.author.id;
    });
    list.scrollTop = list.scrollHeight;
  }

  // --- 新機能のアクション群 ---

  async function handleEnter(e) {
    if(e.key === 'Enter') {
      const input = document.getElementById('chat-input');
      const content = input.value.trim();
      if(!content || !currentChannelId) return;
      
      input.value = ''; // 先に入力欄をクリア
      await api('POST', `/channels/${currentChannelId}/messages`, { content });
      loadMessages(currentChannelId);
    }
  }

  async function deleteMessage(msgId) {
    if(!confirm("このメッセージを削除しますか？")) return;
    await api('DELETE', `/channels/${currentChannelId}/messages/${msgId}`);
    loadMessages(currentChannelId);
  }

  async function editMessage(msgId, oldContent) {
    const newContent = prompt("メッセージを編集:", oldContent);
    if(newContent === null || newContent === oldContent || newContent.trim() === "") return;
    await api('PATCH', `/channels/${currentChannelId}/messages/${msgId}`, { content: newContent });
    loadMessages(currentChannelId);
  }

  async function createInvite(channelId, event) {
    event.stopPropagation(); // チャンネル切り替えを防ぐ
    const res = await api('POST', `/channels/${channelId}/invites`, { max_age: 86400 }); // 24時間有効
    if(res.code) {
      prompt("招待リンクが作成されました (24時間有効):", `https://discord.gg/${res.code}`);
    } else {
      alert("招待リンクの作成に失敗しました（権限がありません）。");
    }
  }

  async function leaveServer() {
    if(!currentGuildId) return;
    if(!confirm("⚠️ 本当にこのサーバーからBotを退出させますか？（二度とアクセスできなくなります）")) return;
    
    await api('DELETE', `/users/@me/guilds/${currentGuildId}`);
    alert("サーバーから退出しました。");
    loadServers();
    document.getElementById('channel-list').innerHTML = '';
    document.getElementById('messages').innerHTML = '';
  }

  init();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/<path:subpath>", methods=["GET", "POST", "DELETE", "PATCH"])
def proxy(subpath):
    if not TOKEN:
        return jsonify({"error": "Token not configured"}), 500
    url = f"{API_BASE}/{subpath}"
    headers = {"Authorization": f"Bot {TOKEN}"}
    
    kwargs = {"headers": headers}
    if request.is_json:
        kwargs["json"] = request.get_json()
        
    try:
        if request.method == "GET":
            res = requests.get(url, **kwargs)
        elif request.method == "POST":
            res = requests.post(url, **kwargs)
        elif request.method == "DELETE":
            res = requests.delete(url, **kwargs)
        elif request.method == "PATCH":
            res = requests.patch(url, **kwargs)
            
        # 削除成功時などは中身のない204が返ってくるため分岐
        if res.status_code == 204:
            return jsonify({"success": True}), 204
            
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
