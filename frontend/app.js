const base = window.APP_CONFIG?.apiBaseUrl || 'http://localhost:8000';
const $ = (id) => document.getElementById(id);
let activeConversation = null;
let accessToken = sessionStorage.getItem('accessToken') || '';

function notice(message = '') { $('notice').textContent = message; }
async function api(path, options = {}) {
  const response = await fetch(`${base}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(accessToken ? { 'X-Access-Token': accessToken } : {}), ...options.headers },
  });
  if (!response.ok) {
    let detail = `요청 실패 (${response.status})`;
    try { detail = (await response.json()).detail || detail; } catch { /* keep status */ }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return response.status === 204 ? null : response.json();
}
function clear(element) { element.replaceChildren(); }
function appendMessage(role, content) {
  const box = $('messages');
  if (box.querySelector('.empty')) clear(box);
  const node = document.createElement('div');
  node.className = `message ${role}`;
  node.textContent = content;
  box.append(node);
  box.scrollTop = box.scrollHeight;
}
async function refreshSummary() {
  const summary = await api('/api/data/summary');
  $('period').textContent = summary.period || '자료 없음';
  $('count').textContent = `${summary.count}건`;
  $('average').textContent = summary.metrics.average == null ? '—' : `${summary.metrics.average}°C`;
  $('trend').textContent = summary.recent_change_c == null ? summary.trend : `${summary.trend} (${summary.recent_change_c > 0 ? '+' : ''}${summary.recent_change_c}°C)`;
}
async function refreshData() {
  const rows = await api('/api/data');
  const body = $('data-list'); clear(body);
  for (const row of rows) {
    const tr = document.createElement('tr');
    for (const value of [row.date, `${row.value}°C`, row.memo || '—']) {
      const td = document.createElement('td'); td.textContent = value; tr.append(td);
    }
    const td = document.createElement('td');
    const edit = document.createElement('button'); edit.type = 'button'; edit.textContent = '수정';
    edit.addEventListener('click', async () => {
      const input = prompt(`${row.date} 최고기온 (°C)`, row.value);
      if (input == null) return;
      const value = Number(input);
      if (!Number.isFinite(value) || value < -100 || value > 100 || input.trim() === '') return notice('−100~100 사이 숫자를 입력하세요.');
      try { await api(`/api/data/${encodeURIComponent(row.id)}`, { method: 'PUT', body: JSON.stringify({ date: row.date, value, memo: row.memo || '' }) }); await Promise.all([refreshData(), refreshSummary()]); notice('수정했습니다.'); }
      catch (error) { notice(error.message); }
    });
    const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = '삭제';
    remove.addEventListener('click', async () => {
      if (!confirm(`${row.date} 데이터를 삭제할까요?`)) return;
      try { await api(`/api/data/${encodeURIComponent(row.id)}`, { method: 'DELETE' }); await Promise.all([refreshData(), refreshSummary()]); notice('삭제했습니다.'); }
      catch (error) { notice(error.message); }
    });
    td.append(edit, ' ', remove); tr.append(td); body.append(tr);
  }
}
async function refreshConversations() {
  const rows = await api('/api/conversations');
  const list = $('conversations'); clear(list);
  if (!rows.length) { const p = document.createElement('p'); p.className = 'empty'; p.textContent = '저장된 대화가 없습니다.'; list.append(p); }
  for (const row of rows) {
    const button = document.createElement('button'); button.className = 'history-item'; button.type = 'button';
    button.textContent = row.title;
    const date = document.createElement('small'); date.textContent = row.updated_at?.slice(0, 16).replace('T', ' ') || ''; button.append(date);
    button.addEventListener('click', async () => {
      try { const detail = await api(`/api/conversations/${encodeURIComponent(row.id)}`); activeConversation = detail.id; clear($('messages')); detail.messages.forEach(msg => appendMessage(msg.role, msg.content)); notice('대화를 불러왔습니다.'); }
      catch (error) { notice(error.message); }
    });
    list.append(button);
  }
}
$('chat-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const input = $('question'); const message = input.value.trim(); if (!message) return;
  $('send').disabled = true; $('loading').hidden = false; notice(''); appendMessage('user', message);
  try {
    const result = await api('/api/chat', { method: 'POST', body: JSON.stringify({ message, conversation_id: activeConversation }) });
    activeConversation = result.conversation_id; appendMessage('assistant', result.answer); input.value = '';
    await refreshConversations();
  } catch (error) { appendMessage('assistant', `오류: ${error.message}`); notice('답변을 저장하지 못했습니다. 다시 시도할 수 있습니다.'); }
  finally { $('send').disabled = false; $('loading').hidden = true; }
});
$('data-form').addEventListener('submit', async (event) => {
  event.preventDefault(); const form = event.currentTarget; const fields = new FormData(form);
  try { await api('/api/data', { method: 'POST', body: JSON.stringify({ date: fields.get('date'), value: Number(fields.get('value')), memo: fields.get('memo') }) }); form.reset(); await Promise.all([refreshData(), refreshSummary()]); notice('데이터를 추가했습니다.'); }
  catch (error) { notice(error.message); }
});
$('new-chat').addEventListener('click', () => { activeConversation = null; clear($('messages')); notice('새 대화를 시작합니다.'); });
$('token-button').addEventListener('click', () => {
  const value = prompt('접근 토큰을 입력하세요. 이 브라우저 탭을 닫으면 지워집니다.', accessToken);
  if (value === null) return;
  accessToken = value; sessionStorage.setItem('accessToken', value); init();
});
async function init() { try { await Promise.all([refreshSummary(), refreshData(), refreshConversations()]); notice(''); } catch (error) { notice(`연결 오류: ${error.message}`); } }
init();
