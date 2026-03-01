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

export async function updateMcpServer(serverId, data) {
  const res = await fetch(`${BASE}/api/mcp-servers/${serverId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
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

export async function fetchTelegramSettings() {
  const res = await fetch(`${BASE}/api/telegram/settings`);
  return res.json();
}

export async function updateTelegramSettings(data) {
  const res = await fetch(`${BASE}/api/telegram/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function fetchTelegramStatus() {
  const res = await fetch(`${BASE}/api/telegram/status`);
  return res.json();
}

export async function restartTelegram() {
  const res = await fetch(`${BASE}/api/telegram/restart`, { method: 'POST' });
  return res.json();
}

export async function stopTelegram() {
  const res = await fetch(`${BASE}/api/telegram/stop`, { method: 'POST' });
  return res.json();
}

export async function fetchAgents() {
  const res = await fetch(`${BASE}/api/agents`);
  return res.json();
}

export async function createAgent(data) {
  const res = await fetch(`${BASE}/api/agents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function updateAgent(id, data) {
  const res = await fetch(`${BASE}/api/agents/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function deleteAgent(id) {
  await fetch(`${BASE}/api/agents/${id}`, { method: 'DELETE' });
}

export async function fetchServerTime() {
  const res = await fetch(`/api/server-time`);
  return res.json();
}

export async function fetchAutoprompts() {
  const res = await fetch(`${BASE}/api/autoprompts`);
  return res.json();
}

export async function createAutoprompt(data) {
  const res = await fetch(`${BASE}/api/autoprompts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function updateAutoprompt(id, data) {
  const res = await fetch(`${BASE}/api/autoprompts/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function deleteAutoprompt(id) {
  await fetch(`${BASE}/api/autoprompts/${id}`, { method: 'DELETE' });
}

export async function runAutopromptNow(id) {
  const res = await fetch(`${BASE}/api/autoprompts/${id}/run`, { method: 'POST' });
  return res.json();
}

export async function fetchProviders() {
  const res = await fetch(`${BASE}/api/providers`);
  return res.json();
}

export async function testProvider(base_url, api_key = '', provider_id = '') {
  const res = await fetch(`${BASE}/api/providers/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ base_url, api_key, provider_id })
  });
  return res.json();
}

export async function fetchProviderModels(providerId) {
  const res = await fetch(`${BASE}/api/providers/${providerId}/models`);
  return res.json();
}

export async function updateProvider(providerId, data) {
  const res = await fetch(`${BASE}/api/providers/${providerId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function fetchUsageStats(period = 'today') {
  const res = await fetch(`${BASE}/api/usage/stats?period=${period}`);
  return res.json();
}

export async function resetUsageStats() {
  await fetch(`${BASE}/api/usage/stats`, { method: 'DELETE' });
}

export async function fetchWebhooks() {
  const res = await fetch(`${BASE}/api/webhooks`);
  return res.json();
}

export async function createWebhook(data) {
  const res = await fetch(`${BASE}/api/webhooks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function updateWebhook(id, data) {
  const res = await fetch(`${BASE}/api/webhooks/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function deleteWebhook(id) {
  await fetch(`${BASE}/api/webhooks/${id}`, { method: 'DELETE' });
}
