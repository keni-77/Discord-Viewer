import os
import random
import logging
import requests
from flask import Flask, jsonify, request, render_template_string

# 環境変数からトークンを読み込む（GitHubに晒さないための安全対策）
TOKEN = os.environ.get("DISCORD_TOKEN")
API_BASE = "https://discord.com/api/v10"

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)

# --- 前回の完璧なHTMLテンプレートをそのままここに移植 ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Discord Read-Only Viewer</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-primary: #313338; --bg-secondary: #2b2d31; --bg-tertiary: #1e1f22;
    --text-normal: #dbdee1; --text-muted: #949ba4; --header-primary: #f2f3f5;
    --brand: #5865f2; --embed-bg: #2b2d31;
  }
  body { margin: 0; font-family: 'Noto Sans JP', sans-serif; background: var(--bg-primary); color: var(--text-normal); display: flex; height: 100vh; overflow: hidden; }
  ::-webkit-scrollbar { width: 8px; }
  ::-webkit-scrollbar-thumb { background: #1a1b1e; border-radius: 4px; }
  #server-bar { width: 72px; background: var(--bg-tertiary); display: flex; flex-direction: column; align-items: center; padding-top: 12px; gap: 8px; overflow-y: auto; }
  .server-icon { width: 48px; height: 48px; border-radius: 50%; background: var(--bg-primary); color: var(--text-normal); display: flex; justify-content: center; align-items: center; font-weight: bold; cursor: pointer; transition: 0.2s; background-size: cover; background-position: center; position: relative; }
  .server-icon:hover { border-radius: 16px; background-color: var(--brand); color: #fff; }
  .server-icon.active { border-radius: 16px; background-color: var(--brand); }
  #channels { width: 240px; background: var(--bg-secondary); display: flex; flex-direction: column; }
  .header { height: 48px; padding: 0 16px; font-weight: 700; color: var(--header-primary); display: flex; align-items: center; border-bottom: 1px solid #1f2023; box-shadow: 0 1px 2px rgba(0,0,0,0.1); font-size: 15px;}
  .list { flex: 1; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 2px; }
  .channel-item { padding: 6px 8px; border-radius: 4px; cursor: pointer; color: var(--text-muted); font-size: 15px; font-weight: 500; display: flex; align-items: center; gap: 6px; }
  .channel-item:hover { background: rgba(78, 80, 88, 0.3); color: var(--text-normal); }
  .channel-item.active { background: rgba(78, 80, 88, 0.6); color: #fff; }
  .hash { color: #80848e; font-size: 18px; }
  #chat { flex: 1; display: flex; flex-direction: column; background: var(--bg-primary); min-width: 0; }
  .chat-header { border-bottom: 1px solid #2a2c30; justify-content: space-between; font-size: 16px; }
  #messages { flex: 1; overflow-y: auto; padding: 16px 0; display: flex; flex-direction: column; }
  .msg-container { display: flex; padding: 4px 16px; margin-top: 12px; }
  .msg-avatar { width: 40px; height: 40px; border-radius: 50%; background: #5865f2; flex-shrink: 0; margin-right: 16px; background-size: cover; background-position: center; }
  .msg-body { flex: 1; min-width: 0; }
  .msg-header { display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px; }
  .msg-author { font-weight: 500; color: var(--header-primary); font-size: 16px; }
  .msg-time { font-size: 12px; color: var(--text-muted); }
  .msg-bot-tag { background: var(--brand); color: white; font-size: 10px; padding: 1px 4px; border-radius: 3px; }
  .msg-content { color: var(--text-normal); font-size: 15px; line-height: 1.5; white-space: pre-wrap; word-break: break-word; }
  .attachment-img { max-width: 400px; max-height: 400px; border-radius: 8px; margin-top: 8px; display: block; object-fit: contain; }
  .embed { background: var(--embed-bg); border-radius: 4px; border-left: 4px solid var(--brand); padding: 12px 16px; margin-top: 8px; max-width: 520px; display: flex; flex-direction: column; gap: 8px; }
  .embed-title { font-weight: 700; color: #1e88e5; }
  .embed-desc { font-size: 14px; color: var(--text-normal); white-space: pre-wrap; }
  .embed-img { max-width: 100%; border-radius: 4px; margin-top: 8px; }
  .embed-footer { font-size: 11px; color: var(--text-muted); display: flex; align-items: center; gap: 8px;}
  .read-only-footer { background: var(--bg-primary); padding: 16px; border-top: 1px solid #2a2c30; }
  .read-only-box { background: var(--bg-secondary); border-radius: 8px; padding: 12px; text-align: center; color: var(--text-muted); font-size: 14px; }
  .btn-refresh { background: var(--brand); color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; }
</style>
</head>
<body>
<div id="server-bar"></div>
<div id="channels">
  <div class="header" id="server-name">サーバーを選択</div>
  <div id="channel-list" class="list"></div>
</div>
<div id="chat">
  <div class="header chat-header">
    <span id="current-channel-name"><span class="hash">#</span> チャンネル未選択</span>
    <button id="refresh-btn" class="btn-refresh" style="display:none;" onclick="loadMessages(currentChannelId)">ログを更新</button>
  </div>
  <div id="messages"></div>
  <div class="read-only-footer"><div class="read-only-box">🔒 閲覧専用モード</div></div>
</div>
<script>
  let currentGuildId = null; let currentChannelId = null;
  async function api(method, path) {
    const res = await fetch('/api' + path, { method });
    return res.json();
  }
  function getAvatarUrl(user) {
    if (user.avatar) return `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png?size=128`;
    return `https://cdn.discordapp.com/embed/avatars/${user.discriminator !== "0" ? parseInt(user.discriminator) % 5 : Number(BigInt(user.id) >> 22n) % 6}.png`;
  }
  function formatDate(isoString) {
    const d = new Date(isoString);
    return `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`;
  }
  function escapeHtml(text) {
    if(!text) return "";
    return text.replace(/[&<>"']/g, m => ({'&': '&amp;','<': '&lt;','>': '&gt;','"': '&quot;',"'": '&#39;'})[m]);
  }
  async function loadServers() {
    const bar = document.getElementById('server-bar'); bar.innerHTML = '';
    const servers = await api('GET', '/users/@me/guilds');
    if (servers.error) { alert("エラー: " + servers.error); return; }
    servers.forEach(s => {
      const div = document.createElement('div'); div.className = 'server-icon'; div.title = s.name;
      if (s.icon) div.style.backgroundImage = `url(https://cdn.discordapp.com/icons/${s.id}/${s.icon}.png?size=128)`;
      else div.textContent = s.name.charAt(0);
      div.onclick = () => {
        document.querySelectorAll('.server-icon').forEach(e => e.classList.remove('active'));
        div.classList.add('active'); currentGuildId = s.id;
        document.getElementById('server-name').textContent = s.name; loadChannels(s.id);
      };
      bar.appendChild(div);
    });
  }
  async function loadChannels(guildId) {
    const list = document.getElementById('channel-list'); list.innerHTML = '';
    const channels = await api('GET', `/guilds/${guildId}/channels`);
    channels.filter(c => c.type === 0 || c.type === 5).sort((a,b) => a.position - b.position).forEach(c => {
      const div = document.createElement('div'); div.className = 'channel-item';
      div.innerHTML = `<span class="hash">#</span> ${escapeHtml(c.name)}`;
      div.onclick = () => {
        document.querySelectorAll('.channel-item').forEach(e => e.classList.remove('active'));
        div.classList.add('active'); currentChannelId = c.id;
        document.getElementById('current-channel-name').innerHTML = `<span class="hash">#</span> ${escapeHtml(c.name)}`;
        document.getElementById('refresh-btn').style.display = 'block'; loadMessages(c.id);
      };
      list.appendChild(div);
    });
  }
  async function loadMessages(channelId) {
    if(!channelId) return;
    const list = document.getElementById('messages'); list.innerHTML = '';
    const msgs = await api('GET', `/channels/${channelId}/messages?limit=50`);
    if (!Array.isArray(msgs)) { list.innerHTML = '<div>権限がありません</div>'; return; }
    [...msgs].reverse().forEach(m => {
      const div = document.createElement('div'); div.className = 'msg-container';
      let attHtml = '';
      if(m.attachments) m.attachments.forEach(a => { if (a.content_type && a.content_type.startsWith('image/')) attHtml += `<img class="attachment-img" src="${a.url}">`; });
      let embHtml = '';
      if(m.embeds) m.embeds.forEach(e => {
        const color = e.color ? '#' + e.color.toString(16).padStart(6, '0') : '#1e1f22';
        let inner = '';
        if(e.title) inner += `<div class="embed-title">${escapeHtml(e.title)}</div>`;
        if(e.description) inner += `<div class="embed-desc">${escapeHtml(e.description)}</div>`;
        if(e.image) inner += `<img class="embed-img" src="${e.image.url}">`;
        embHtml += `<div class="embed" style="border-left-color: ${color}">${inner}</div>`;
      });
      div.innerHTML = `<div class="msg-avatar" style="background-image: url('${getAvatarUrl(m.author)}')"></div>
        <div class="msg-body">
          <div class="msg-header"><span class="msg-author">${escapeHtml(m.author.username)}</span>${m.author.bot ? '<span class="msg-bot-tag">BOT</span>':''} <span class="msg-time">${formatDate(m.timestamp)}</span></div>
          <div class="msg-content">${escapeHtml(m.content)}</div>${attHtml}${embHtml}
        </div>`;
      list.appendChild(div);
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
    # Render環境用のポート設定
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
