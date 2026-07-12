import os
import requests
from flask import Flask, jsonify, render_template_string

TOKEN = os.environ.get("DISCORD_TOKEN")
API_BASE = "https://discord.com/api/v10"

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Discord Read-Only Viewer</title>
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
  }
  * { box-sizing: border-box; scrollbar-width: thin; scrollbar-color: #1a1b1e transparent; }
  body { margin: 0; font-family: 'Noto Sans JP', sans-serif; background: var(--bg-primary); color: var(--text-normal); display: flex; height: 100vh; overflow: hidden; font-size: 16px; }
  
  /* スクロールバー */
  ::-webkit-scrollbar { width: 8px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #1a1b1e; border-radius: 4px; }

  /* 左端：サーバー一覧 */
  #server-bar { width: 72px; background: var(--bg-tertiary); display: flex; flex-direction: column; align-items: center; padding: 12px 0; gap: 8px; flex-shrink: 0; z-index: 2; }
  .server-icon { width: 48px; height: 48px; border-radius: 50%; background-color: var(--bg-primary); color: var(--text-normal); display: flex; justify-content: center; align-items: center; font-weight: bold; cursor: pointer; transition: 0.2s ease; background-size: cover; background-position: center; position: relative; }
  .server-icon:hover { border-radius: 16px; background-color: var(--brand); color: #fff; }
  .server-icon.active { border-radius: 16px; background-color: var(--brand); }

  /* 左から2番目：チャンネル一覧 */
  #channels { width: 240px; background: var(--bg-secondary); display: flex; flex-direction: column; flex-shrink: 0; }
  .header { height: 48px; padding: 0 16px; font-weight: 700; color: var(--header-primary); display: flex; align-items: center; border-bottom: 1px solid var(--bg-tertiary); box-shadow: 0 1px 2px rgba(0,0,0,0.1); font-size: 15px; flex-shrink: 0; justify-content: space-between; }
  
  /* イベントパネル */
  #events-container { padding: 16px 8px 8px; display: none; border-bottom: 1px solid var(--divider); }
  .event-header { font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px; padding-left: 8px; }
  .event-card { background: var(--bg-primary); border-radius: 4px; padding: 8px; font-size: 13px; margin-bottom: 4px; cursor: pointer; border-left: 2px solid #23a559; }
  .event-title { font-weight: bold; color: var(--header-primary); margin-bottom: 4px; }
  .event-time { color: #23a559; font-size: 12px; }

  /* チャンネルリスト */
  .list { flex: 1; overflow-y: auto; padding: 12px 8px; display: flex; flex-direction: column; gap: 2px; }
  .channel-item { padding: 6px 8px; border-radius: 4px; cursor: pointer; color: var(--text-muted); font-size: 15px; font-weight: 500; display: flex; align-items: center; gap: 6px; }
  .channel-item:hover { background: rgba(78, 80, 88, 0.3); color: var(--text-normal); }
  .channel-item.active { background: rgba(78, 80, 88, 0.6); color: #fff; }
  .hash { color: #80848e; font-size: 18px; font-weight: normal; }

  /* メイン：チャット画面 */
  #chat { flex: 1; display: flex; flex-direction: column; background: var(--bg-primary); min-width: 0; }
  .chat-header { border-bottom: 1px solid var(--bg-tertiary); font-size: 16px; }
  #messages { flex: 1; overflow-y: auto; padding: 16px 0 32px 0; display: flex; flex-direction: column; }
  
  /* メッセージのスタイリング（重なり修正済み！） */
  .msg-wrapper { display: flex; padding: 2px 16px 2px 72px; position: relative; margin-top: 0; }
  .msg-wrapper.first { margin-top: 17px; } /* ここにあった padding-left を削除しました */
  .msg-wrapper:hover { background: rgba(2, 2, 2, 0.06); }
  
  .msg-avatar { position: absolute; left: 16px; top: 2px; width: 40px; height: 40px; border-radius: 50%; background-color: transparent; background-size: cover; background-position: center; cursor: pointer; }
  
  .msg-body { flex: 1; min-width: 0; }
  .msg-header { display: flex; align-items: baseline; gap: 8px; margin-bottom: 2px; line-height: 1.2; }
  .msg-author { font-weight: 500; color: var(--header-primary); font-size: 16px; }
  .msg-time { font-size: 12px; color: var(--text-muted); }
  .msg-bot-tag { background: var(--brand); color: white; font-size: 10px; padding: 2px 4px; border-radius: 3px; font-weight: bold; }
  
  .msg-content { color: var(--text-normal); font-size: 15px; line-height: 1.375rem; white-space: pre-wrap; word-break: break-word; }
  
  /* 添付ファイルと埋め込み */
  .attachment-img { max-width: 400px; max-height: 400px; border-radius: 8px; margin-top: 4px; display: block; object-fit: contain; cursor: pointer; }
  .embed { background: var(--embed-bg); border-radius: 4px; border-left: 4px solid var(--brand); padding: 12px 16px; margin-top: 4px; max-width: 520px; display: flex; flex-direction: column; gap: 8px; }
  .embed-title { font-weight: 700; color: #1e88e5; }
  .embed-desc { font-size: 14px; color: var(--text-normal); white-space: pre-wrap; }
  
  /* フッター */
  .read-only-footer { padding: 0 16px 24px; }
  .read-only-box { background: var(--bg-tertiary); border-radius: 8px; padding: 12px 16px; color: var(--text-muted); font-size: 14px; font-weight: 500; display: flex; justify-content: space-between; align-items: center; }
  .btn-refresh { background: var(--brand); color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; transition: 0.2s; }
  .btn-refresh:hover { background: #4752c4; }

  /* 右端：メンバー一覧 */
  #members { width: 240px; background: var(--bg-secondary); display: flex; flex-direction: column; flex-shrink: 0; border-left: 1px solid var(--bg-tertiary); }
  @media (max-width: 800px) { #members { display: none; } }
  .member-list-inner { padding: 16px 8px; overflow-y: auto; flex: 1; }
  .member-role-header { font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin: 16px 0 4px 8px; }
  .member-item { display: flex; align-items: center; gap: 12px; padding: 6px 8px; border-radius: 4px; cursor: pointer; opacity: 0.8; }
  .member-item:hover { background: rgba(78, 80, 88, 0.3); opacity: 1; }
  .member-avatar { width: 32px; height: 32px; border-radius: 50%; background-size: cover; background-position: center; }
  .member-name { color: var(--text-normal); font-size: 15px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
</head>
<body>
<div id="server-bar"></div>
<div id="channels">
  <div class="header" id="server-name">サーバーを選択</div>
  <div id="events-container">
    <div class="event-header">イベント (<span id="event-count">0</span>)</div>
    <div id="event-list"></div>
  </div>
  <div id="channel-list" class="list"></div>
</div>
<div id="chat">
  <div class="header chat-header">
    <span id="current-channel-name"><span class="hash">#</span> チャンネル未選択</span>
  </div>
  <div id="messages"></div>
  <div class="read-only-footer">
    <div class="read-only-box">
      <span>🔒 閲覧専用モード (メッセージの送信はできません)</span>
      <button id="refresh-btn" class="btn-refresh" style="display:none;" onclick="loadMessages(currentChannelId)">ログを最新にする</button>
    </div>
  </div>
</div>
<div id="members">
  <div class="header">メンバー</div>
  <div id="member-list-container" class="member-list-inner"></div>
</div>

<script>
  let currentGuildId = null;
  let currentChannelId = null;

  async function api(method, path) {
    try {
      const res = await fetch('/api' + path, { method });
      return res.json();
    } catch(e) {
      return { error: e.message };
    }
  }

  function getAvatarUrl(user) {
    if (user.avatar) return `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png?size=128`;
    const index = user.discriminator !== "0" ? parseInt(user.discriminator) % 5 : Number(BigInt(user.id) >> 22n) % 6;
    return `https://cdn.discordapp.com/embed/avatars/${index}.png`;
  }

  function formatDate(isoString) {
    const d = new Date(isoString);
    const today = new Date();
    const isToday = d.getDate() === today.getDate() && d.getMonth() === today.getMonth() && d.getFullYear() === today.getFullYear();
    const time = `${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`;
    return isToday ? `今日 ${time}` : `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()} ${time}`;
  }

  function formatEventDate(isoString) {
    const d = new Date(isoString);
    return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')} 開始`;
  }

  function escapeHtml(text) {
    if(!text) return "";
    return text.replace(/[&<>"']/g, m => ({'&': '&amp;','<': '&lt;','>': '&gt;','"': '&quot;',"'": '&#39;'})[m]);
  }

  async function loadServers() {
    const bar = document.getElementById('server-bar');
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
        loadEvents(s.id);
        loadChannels(s.id);
        loadMembers(s.id);
      };
      bar.appendChild(div);
    });
  }

  async function loadEvents(guildId) {
    const evContainer = document.getElementById('events-container');
    const evList = document.getElementById('event-list');
    evList.innerHTML = '';
    
    const events = await api('GET', `/guilds/${guildId}/scheduled-events`);
    if(events.error || !Array.isArray(events) || events.length === 0) {
      evContainer.style.display = 'none';
      return;
    }
    
    evContainer.style.display = 'block';
    document.getElementById('event-count').textContent = events.length;
    events.forEach(ev => {
      const div = document.createElement('div');
      div.className = 'event-card';
      div.innerHTML = `
        <div class="event-title">${escapeHtml(ev.name)}</div>
        <div class="event-time">📅 ${formatEventDate(ev.scheduled_start_time)}</div>
      `;
      evList.appendChild(div);
    });
  }

  async function loadChannels(guildId) {
    const list = document.getElementById('channel-list');
    list.innerHTML = '';
    const channels = await api('GET', `/guilds/${guildId}/channels`);
    if(channels.error || !Array.isArray(channels)) return;
    
    channels.filter(c => c.type === 0 || c.type === 5)
            .sort((a,b) => a.position - b.position)
            .forEach(c => {
      const div = document.createElement('div');
      div.className = 'channel-item';
      div.innerHTML = `<span class="hash">#</span> ${escapeHtml(c.name)}`;
      div.onclick = () => {
        document.querySelectorAll('.channel-item').forEach(e => e.classList.remove('active'));
        div.classList.add('active');
        currentChannelId = c.id;
        document.getElementById('current-channel-name').innerHTML = `<span class="hash">#</span> ${escapeHtml(c.name)}`;
        document.getElementById('refresh-btn').style.display = 'block';
        loadMessages(c.id);
      };
      list.appendChild(div);
    });
  }

  async function loadMembers(guildId) {
    const list = document.getElementById('member-list-container');
    list.innerHTML = '';
    // ここを limit=1000 に修正しました
    const members = await api('GET', `/guilds/${guildId}/members?limit=1000`);
    
    if (members.error || !Array.isArray(members)) {
      list.innerHTML = '<div style="padding:8px; font-size:13px; color:var(--text-muted);">メンバー情報が取得できませんでした（BotのIntent設定を確認してください）。</div>';
      return;
    }
    
    list.innerHTML = `<div class="member-role-header">サーバーメンバー — ${members.length}</div>`;
    members.forEach(m => {
      const user = m.user;
      const div = document.createElement('div');
      div.className = 'member-item';
      div.innerHTML = `
        <div class="member-avatar" style="background-image: url('${getAvatarUrl(user)}')"></div>
        <div class="member-name">${escapeHtml(m.nick || user.global_name || user.username)}</div>
      `;
      list.appendChild(div);
    });
  }

  async function loadMessages(channelId) {
    if(!channelId) return;
    const list = document.getElementById('messages');
    list.innerHTML = '<div style="text-align:center; padding: 20px; color: var(--text-muted);">読み込み中...</div>';
    
    const msgs = await api('GET', `/channels/${channelId}/messages?limit=50`);
    list.innerHTML = '';
    
    if (!Array.isArray(msgs)) { 
      list.innerHTML = '<div style="padding:16px;">権限がないか、チャンネルが見つかりません。</div>'; 
      return; 
    }
    
    const reversedMsgs = [...msgs].reverse();
    let prevAuthorId = null;
    let prevTimestamp = null;

    reversedMsgs.forEach(m => {
      const currTime = new Date(m.timestamp);
      const isConsecutive = (prevAuthorId === m.author.id) && 
                            (prevTimestamp && (currTime - prevTimestamp) < 5 * 60 * 1000);

      const div = document.createElement('div');
      div.className = `msg-wrapper ${isConsecutive ? 'consecutive' : 'first'}`;
      
      let attHtml = '';
      if(m.attachments) m.attachments.forEach(a => { 
        if (a.content_type && a.content_type.startsWith('image/')) {
          attHtml += `<a href="${a.url}" target="_blank"><img class="attachment-img" src="${a.url}"></a>`; 
        }
      });
      
      let embHtml = '';
      if(m.embeds) m.embeds.forEach(e => {
        const color = e.color ? '#' + e.color.toString(16).padStart(6, '0') : '#1e1f22';
        let inner = '';
        if(e.title) inner += `<div class="embed-title">${escapeHtml(e.title)}</div>`;
        if(e.description) inner += `<div class="embed-desc">${escapeHtml(e.description)}</div>`;
        embHtml += `<div class="embed" style="border-left-color: ${color}">${inner}</div>`;
      });

      let contentHtml = `<div class="msg-content">${escapeHtml(m.content)}</div>${attHtml}${embHtml}`;

      if (isConsecutive) {
        div.innerHTML = `<div class="msg-body">${contentHtml}</div>`;
      } else {
        div.innerHTML = `
          <div class="msg-avatar" style="background-image: url('${getAvatarUrl(m.author)}')"></div>
          <div class="msg-body">
            <div class="msg-header">
              <span class="msg-author">${escapeHtml(m.author.global_name || m.author.username)}</span>
              ${m.author.bot ? '<span class="msg-bot-tag">BOT</span>':''} 
              <span class="msg-time">${formatDate(m.timestamp)}</span>
            </div>
            ${contentHtml}
          </div>
        `;
      }
      
      list.appendChild(div);
      
      prevAuthorId = m.author.id;
      prevTimestamp = currTime;
    });
    
    list.scrollTop = list.scrollHeight;
  }

  loadServers();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/<path:subpath>", methods=["GET"])
def proxy(subpath):
    if not TOKEN:
        return jsonify({"error": "Token not configured"}), 500
    url = f"{API_BASE}/{subpath}"
    headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
    try:
        res = requests.get(url, headers=headers)
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
