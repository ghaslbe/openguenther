const BASE = '';

export async function fetchChats() {
  const res = await fetch(`${BASE}/api/chats`);
  return res.json();
}

export async function fetchChat(chatId) {
  const res = await fetch(`${BASE}/api/chats/${chatId}`);
  return res.json();
}

export async function createChat(title = 'Neuer Chat') {
  const res = await fetch(`${BASE}/api/chats`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  });
  return res.json();
}

export async function deleteChat(chatId) {
  await fetch(`${BASE}/api/chats/${chatId}`, { method: 'DELETE' });
}

export async function fetchSettings() {
  const res = await fetch(`${BASE}/api/settings`);
  return res.json();
}

export async function updateSettings(data) {
  const res = await fetch(`${BASE}/api/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function fetchMcpServers() {
  const res = await fetch(`${BASE}/api/mcp-servers`);
  return res.json();
}

export async function addMcpServer(server) {
  const res = await fetch(`${BASE}/api/mcp-servers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(server)
  });
  return res.json();
}

export async function deleteMcpServer(serverId) {
  await fetch(`${BASE}/api/mcp-servers/${serverId}`, { method: 'DELETE' });
}

export async function reloadMcpTools() {
  const res = await fetch(`${BASE}/api/mcp/reload`, { method: 'POST' });
  return res.json();
}

export async function fetchMcpTools() {
  const res = await fetch(`${BASE}/api/mcp/tools`);
  return res.json();
}

export async function fetchToolSettings(toolName) {
  const res = await fetch(`${BASE}/api/mcp/tools/${toolName}/settings`);
  return res.json();
}

export async function updateToolSettings(toolName, data) {
  const res = await fetch(`${BASE}/api/mcp/tools/${toolName}/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}
