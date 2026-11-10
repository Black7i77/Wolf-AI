(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  let model = 'llama3.2:latest';
  let busy = false;
  let codingModel = '';
  let publicDemo = false;
  let chats = [];
  let activeId = null;
  let toastTimer;
  const storageKey='wolf-ai-open-chats-v1';
  try {
    const saved=JSON.parse(localStorage.getItem(storageKey)||'[]');
    if(Array.isArray(saved))chats=saved.filter(c=>c && typeof c.id==='string' && typeof c.title==='string' && Array.isArray(c.messages)).map(c=>({...c,messages:c.messages.filter(m=>m && ['user','assistant','system'].includes(m.role) && typeof m.text==='string')}));
  } catch {}
  const icon = name => {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
    use.setAttribute('href', '#i-' + name); svg.append(use); return svg;
  };
  function toast(text) {
    $('toast').textContent = text; $('toast').hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').hidden = true, 4000);
  }
  function save() {
    try{localStorage.setItem(storageKey,JSON.stringify(chats));}
    catch{toast('Browser storage is unavailable or full. This conversation may not survive a reload.');}
  }
  function closeNav() {
    $('sidebar').classList.remove('open'); $('scrim').hidden = true; $('menu').setAttribute('aria-expanded', 'false');
  }
  function renderHistory() {
    const query = $('search').value.toLowerCase().trim();
    const matching = chats.filter(c => c.title.toLowerCase().includes(query) || c.messages.some(m => m.text.toLowerCase().includes(query)));
    $('history').replaceChildren(); $('chat-count').textContent = chats.length || '';
    matching.forEach(chat => {
      const button = document.createElement('button'); button.className = 'history-chat' + (chat.id === activeId ? ' active' : '');
      if (chat.id === activeId) button.setAttribute('aria-current', 'page');
      const label = document.createElement('span'); label.textContent = chat.title;
      button.append(icon('chat'), label); button.title = chat.title;
      button.addEventListener('click', () => { activeId = chat.id; render(); closeNav(); });
      $('history').append(button);
    });
    if (!matching.length) {
      const hint = document.createElement('div'); hint.className = 'history-empty';
      hint.textContent = query ? 'No chats found. Try another search.' : 'Your next big idea belongs here. Start a conversation below.';
      $('history').append(hint);
    }
  }
  function render() {
    const chat = chats.find(c => c.id === activeId);
    $('welcome').hidden = !!chat; $('conversation').hidden = !chat;
    $('messages').replaceChildren();
    if (chat) chat.messages.forEach(message => {
      const row = document.createElement('div'); row.className = 'message ' + message.role;
      const avatar = document.createElement('div'); avatar.className = 'message-avatar'; avatar.setAttribute('aria-hidden', 'true');
      if (message.role === 'user') avatar.textContent = 'Y'; else avatar.append(icon('bolt'));
      const content = document.createElement('div'); content.className = 'message-content';
      const name = document.createElement('strong'); name.textContent = message.role === 'user' ? 'You' : message.role === 'assistant' ? 'Wolf AI' : 'Wolf AI · Notice';
      const text = message.role==='assistant' ? WolfFormat.render(message.text) : document.createElement('p');
      if(message.role!=='assistant')text.textContent=message.text;
      if(message.role==='assistant'){
        for(const check of Array.isArray(message.checks)?message.checks:[]){
          if(!check || typeof check.message!=='string')continue;
          const note=document.createElement('div');note.className='code-check '+(check.valid?'valid':'invalid');note.textContent=check.message;text.append(note);
        }
        if(message.truncated){const note=document.createElement('div');note.className='code-check invalid';note.textContent='Reply reached the output limit. Ask Wolf AI to continue before using unfinished code.';text.append(note);}
      }
      content.append(name, text); row.append(avatar, content); $('messages').append(row);
    });
    renderHistory();
  }
  function resizeInput() { $('prompt').style.height = 'auto'; $('prompt').style.height = Math.min($('prompt').scrollHeight, 150) + 'px'; }
  function newChat() { activeId = null; $('prompt').value = ''; resizeInput(); render(); closeNav(); $('prompt').focus(); }
  $('new-chat').addEventListener('click', newChat);
  $('search').addEventListener('input', renderHistory);
  $('prompt').addEventListener('input', resizeInput);
  document.querySelectorAll('[data-prompt]').forEach(button => button.addEventListener('click', () => {
    $('prompt').value = button.dataset.prompt; resizeInput(); $('prompt').focus();
  }));
  function setStatus(text) {
    const note = $('connection-note'); note.replaceChildren();
    const dot = document.createElement('span'); dot.className = 'status-dot';
    const label = document.createElement('span'); label.textContent = text; note.append(dot,label);
  }
  async function checkConnection() {
    try {
      const response = await fetch('/api/status');
      const data = await response.json();
      if (!response.ok) throw new Error('Local server unavailable.');
      publicDemo=!!data.public_demo;
      if(publicDemo){$('prompt').maxLength=2000;document.querySelector('.composer-footer').textContent='Public demo · 3 messages / 10 min · Replies run on the host computer';}
      codingModel = data.coding_model || '';
      model = ($('mode-select').value==='code' ? codingModel : '') || data.model || model;
      const selector = $('model-select'); selector.replaceChildren();
      (data.models.length ? data.models : [model]).forEach(name => {
        const option=document.createElement('option'); option.value=name; option.textContent=name; selector.append(option);
      });
      selector.value=model;
      setStatus(data.connected && data.models.length ? (publicDemo?'Demo online · ':'Local AI connected · ')+model : data.connected ? 'No models installed in Ollama' : (publicDemo?'The demo is currently offline. Please try again later.':'Ollama offline · Run ollama serve'));
    } catch { setStatus('Start this website with bash start.sh'); }
  }
  $('mode-select').addEventListener('change',()=>{if($('mode-select').value==='code' && codingModel){model=codingModel;$('model-select').value=model;}setStatus('Local AI · '+model);});
  $('model-select').addEventListener('change', event => { model=event.target.value; setStatus('Local AI · '+model); });
  $('refresh-connection').addEventListener('click',checkConnection);
  $('composer').addEventListener('submit', async event => {
    event.preventDefault(); const text = $('prompt').value.trim(); if (!text || busy) { $('prompt').focus(); return; }
    let chat = chats.find(c => c.id === activeId);
    if (!chat) { activeId = typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : String(Date.now()); chat = {id:activeId,title:text.slice(0,55),messages:[]}; chats.unshift(chat); }
    chat.messages.push({role:'user',text});
    $('prompt').value = ''; resizeInput(); save(); render();
    busy=true; $('send').disabled=true; $('model-select').disabled=true;$('mode-select').disabled=true;
    $('send').setAttribute('aria-label','Wolf AI is thinking'); setStatus('Wolf AI is thinking · '+model);
    requestAnimationFrame(() => $('composer').scrollIntoView({behavior:'smooth',block:'end'}));
    try {
      const messages=chat.messages.filter(m=>m.role==='user'||m.role==='assistant').slice(publicDemo?-10:-24).map(m=>({role:m.role,content:m.text}));
      const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model,messages,mode:$('mode-select').value})});
      const data=await response.json();
      if(!response.ok) throw new Error(data.error || 'The local AI could not reply.');
      if(typeof data.reply!=='string') throw new Error('The local AI returned an invalid reply.');
      chat.messages.push({role:'assistant',text:data.reply,checks:data.checks||[],truncated:!!data.truncated});
      setStatus('Local AI · '+model);
    } catch(error) {
      chat.messages.push({role:'system',text:error.message || 'Connection failed. Check that Ollama is running.'});
      setStatus('Connection needs attention · Check the message above');
    } finally {
      busy=false; $('send').disabled=false; $('model-select').disabled=false;$('mode-select').disabled=false;
      $('send').setAttribute('aria-label','Send message'); save(); render();
      requestAnimationFrame(() => $('composer').scrollIntoView({behavior:'smooth',block:'end'}));
    }
  });
  $('prompt').addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); $('composer').requestSubmit(); } });
  document.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k' && !$('membership').open) { event.preventDefault(); newChat(); }
    if (event.key === 'Escape') closeNav();
  });
  $('delete-chat').addEventListener('click', () => {
    if (!activeId) return;
    if(busy){toast('Wait for the current reply before deleting this conversation.');return;}
    if (!window.confirm('Delete this conversation from this browser?')) return;
    chats = chats.filter(c => c.id !== activeId); activeId = null; save(); render(); toast('Conversation deleted.');
  });
  $('menu').addEventListener('click', () => { const open = !$('sidebar').classList.contains('open'); $('sidebar').classList.toggle('open', open); $('scrim').hidden = !open; $('menu').setAttribute('aria-expanded', String(open)); if(open) $('new-chat').focus(); });
  $('scrim').addEventListener('click', closeNav);
  let membershipTrigger = null;
  document.querySelectorAll('[data-membership]').forEach(button => button.addEventListener('click', () => { membershipTrigger=button; closeNav(); $('billing-message').textContent='Payments are not enabled in this preview. No charges will be made.'; $('membership').showModal(); }));
  $('close-membership').addEventListener('click', () => $('membership').close());
  $('membership').addEventListener('click', event => { if (event.target === $('membership')) { const bounds=$('membership').getBoundingClientRect(); if(event.clientX<bounds.left||event.clientX>bounds.right||event.clientY<bounds.top||event.clientY>bounds.bottom) $('membership').close(); } });
  $('membership').addEventListener('close', () => membershipTrigger?.focus());
  $('subscribe').addEventListener('click', () => { $('billing-message').textContent='Subscriptions are coming soon. The price and secure checkout must be configured before anyone can subscribe. You have not been charged.'; });
  $('manage-billing').addEventListener('click', () => { $('billing-message').textContent='There is no active subscription in this preview. Billing management becomes available after payments are connected.'; });
  render();
  fetch('/api/site').then(r=>r.json()).then(site=>{
    publicDemo=!!site.public_demo;
    if(typeof site.github==='string' && /^https:\/\/github\.com\/[A-Za-z0-9_-]+\/[A-Za-z0-9_.-]+\/?$/.test(site.github)){$('github-source').href=site.github;$('github-source').hidden=false;}
  }).catch(()=>{});
  checkConnection();
})();
