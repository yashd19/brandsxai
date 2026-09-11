import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  MessageCircle, Send, Sparkles, Search, Plus, Calendar, X, Image as ImageIcon,
  Bot, User, CheckCheck, Phone, TrendingUp, FileText, ChevronRight
} from 'lucide-react';
import './WhatsAppAI.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const getToken = () => localStorage.getItem('token');
const authHeaders = () => ({ Authorization: `Bearer ${getToken()}` });

const tempColor = { hot: '#ef4444', warm: '#f59e0b', cold: '#3b82f6' };

function fmtTime(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch { return ''; }
}
function fmtDay(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const today = new Date();
  const yest = new Date(); yest.setDate(today.getDate() - 1);
  if (d.toDateString() === today.toDateString()) return 'Today';
  if (d.toDateString() === yest.toDateString()) return 'Yesterday';
  return d.toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' });
}
function initials(name = '') {
  return name.trim().split(/\s+/).slice(0, 2).map(w => w[0] || '').join('').toUpperCase() || '?';
}

const WhatsAppAI = () => {
  const [conversations, setConversations] = useState([]);
  const [liveMode, setLiveMode] = useState(false);
  const [activeId, setActiveId] = useState(null);
  const [activeConv, setActiveConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [search, setSearch] = useState('');
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  // AI suggestions
  const [suggestions, setSuggestions] = useState([]);
  const [suggestLoading, setSuggestLoading] = useState(false);
  const [suggestShown, setSuggestShown] = useState(false);
  const suggestedForRef = useRef(null); // last inbound msg id we auto-suggested for

  // modals / panels
  const [showNew, setShowNew] = useState(false);
  const [showVisit, setShowVisit] = useState(false);
  const [showSim, setShowSim] = useState(false);
  const [simText, setSimText] = useState('');
  const [contextOpen, setContextOpen] = useState(true);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  const msgEndRef = useRef(null);
  const lastTsRef = useRef(null);

  // ---------- data loaders ----------
  const loadConversations = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/whatsapp/conversations`, { headers: authHeaders() });
      if (!res.ok) return;
      const data = await res.json();
      setConversations(data.conversations || []);
      setLiveMode(!!data.live_mode);
    } catch (e) { /* ignore */ }
  }, []);

  const loadConversation = useCallback(async (id) => {
    try {
      const res = await fetch(`${API_URL}/api/whatsapp/conversations/${id}`, { headers: authHeaders() });
      if (!res.ok) return;
      const data = await res.json();
      setActiveConv(data.conversation);
      setMessages(data.messages || []);
      setAppointments(data.appointments || []);
      const msgs = data.messages || [];
      lastTsRef.current = msgs.length ? msgs[msgs.length - 1].created_at : null;
    } catch (e) { /* ignore */ }
  }, []);

  const pollActive = useCallback(async () => {
    if (!activeId) return;
    try {
      const q = lastTsRef.current ? `?after=${encodeURIComponent(lastTsRef.current)}` : '';
      const res = await fetch(`${API_URL}/api/whatsapp/conversations/${activeId}/messages${q}`, { headers: authHeaders() });
      if (!res.ok) return;
      const data = await res.json();
      const fresh = data.messages || [];
      if (fresh.length) {
        setMessages(prev => {
          const ids = new Set(prev.map(m => m.id));
          const merged = [...prev, ...fresh.filter(m => !ids.has(m.id))];
          return merged;
        });
        lastTsRef.current = fresh[fresh.length - 1].created_at;
      }
    } catch (e) { /* ignore */ }
  }, [activeId]);

  useEffect(() => { loadConversations(); }, [loadConversations]);

  // poll conversation list every 4s
  useEffect(() => {
    const t = setInterval(loadConversations, 4000);
    return () => clearInterval(t);
  }, [loadConversations]);

  // poll active thread every 2.5s
  useEffect(() => {
    if (!activeId) return;
    const t = setInterval(pollActive, 2500);
    return () => clearInterval(t);
  }, [activeId, pollActive]);

  useEffect(() => {
    if (msgEndRef.current) msgEndRef.current.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const openConversation = async (c) => {
    setActiveId(c.id);
    setSuggestions([]); setSuggestShown(false); suggestedForRef.current = null;
    setSummary(null);
    await loadConversation(c.id);
    // reflect read locally
    setConversations(prev => prev.map(x => x.id === c.id ? { ...x, unread_count: 0 } : x));
  };

  // auto-suggest (non-intrusive): only once when latest message is from customer
  useEffect(() => {
    if (!activeId || !messages.length) return;
    const last = messages[messages.length - 1];
    if (last.direction === 'inbound' && suggestedForRef.current !== last.id) {
      suggestedForRef.current = last.id;
      fetchSuggestions(true);
    }
  }, [messages, activeId]);

  const fetchSuggestions = async (auto = false) => {
    if (!activeId) return;
    setSuggestLoading(true);
    if (!auto) setSuggestShown(true);
    try {
      const res = await fetch(`${API_URL}/api/whatsapp/conversations/${activeId}/suggestions`, {
        method: 'POST', headers: authHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data.suggestions || []);
        setSuggestShown(true);
        if (data.temperature) {
          setActiveConv(prev => prev ? { ...prev, temperature: data.temperature, intent: data.intent } : prev);
        }
      }
    } catch (e) { /* ignore */ } finally { setSuggestLoading(false); }
  };

  const sendMessage = async (text) => {
    const content = (text ?? input).trim();
    if (!content || !activeId) return;
    setSending(true);
    const optimistic = {
      id: `tmp-${Date.now()}`, conversation_id: activeId, direction: 'outbound',
      sender_type: 'human', content, msg_type: 'text', status: 'sending',
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, optimistic]);
    setInput('');
    setSuggestions([]); setSuggestShown(false);
    try {
      const res = await fetch(`${API_URL}/api/whatsapp/conversations/${activeId}/messages`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, msg_type: 'text' })
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(prev => prev.map(m => m.id === optimistic.id ? data.message : m));
        lastTsRef.current = data.message.created_at;
        loadConversations();
      }
    } catch (e) { /* ignore */ } finally { setSending(false); }
  };

  const simulateInbound = async () => {
    if (!simText.trim() || !activeId) return;
    try {
      const res = await fetch(`${API_URL}/api/whatsapp/conversations/${activeId}/simulate-inbound`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: simText.trim() })
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, data.message]);
        lastTsRef.current = data.message.created_at;
        setSimText(''); setShowSim(false);
        loadConversations();
      }
    } catch (e) { /* ignore */ }
  };

  const loadSummary = async () => {
    if (!activeId) return;
    setSummaryLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/whatsapp/conversations/${activeId}/summary`, { headers: authHeaders() });
      if (res.ok) setSummary(await res.json());
    } catch (e) { /* ignore */ } finally { setSummaryLoading(false); }
  };

  const filtered = conversations.filter(c =>
    !search ||
    (c.lead_name || '').toLowerCase().includes(search.toLowerCase()) ||
    (c.lead_phone || '').includes(search)
  );

  // group messages by day
  const grouped = [];
  let lastDay = null;
  messages.forEach(m => {
    const day = fmtDay(m.created_at);
    if (day !== lastDay) { grouped.push({ type: 'day', day }); lastDay = day; }
    grouped.push({ type: 'msg', m });
  });

  return (
    <div className="wa-root">
      {/* ============ LEFT: conversation list ============ */}
      <aside className="wa-list">
        <div className="wa-list-head">
          <div className="wa-list-title">
            <MessageCircle size={20} /> <span>Chats</span>
            <span className={`wa-mode ${liveMode ? 'live' : 'sim'}`}>{liveMode ? 'LIVE' : 'DEMO'}</span>
          </div>
          <button className="wa-new-btn" onClick={() => setShowNew(true)} title="Start new conversation">
            <Plus size={18} />
          </button>
        </div>
        <div className="wa-search">
          <Search size={16} />
          <input placeholder="Search leads or number" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="wa-threads">
          {filtered.length === 0 && (
            <div className="wa-empty-list">
              <p>No conversations yet.</p>
              <button onClick={() => setShowNew(true)}>Start your first chat</button>
            </div>
          )}
          {filtered.map(c => (
            <button key={c.id} className={`wa-thread ${activeId === c.id ? 'active' : ''}`} onClick={() => openConversation(c)}>
              <div className="wa-avatar" style={{ background: tempColor[c.temperature] || '#25D366' }}>{initials(c.lead_name)}</div>
              <div className="wa-thread-body">
                <div className="wa-thread-top">
                  <span className="wa-thread-name">{c.lead_name}</span>
                  <span className="wa-thread-time">{fmtTime(c.last_message_at)}</span>
                </div>
                <div className="wa-thread-bottom">
                  <span className="wa-thread-preview">{c.last_message || 'No messages'}</span>
                  {c.unread_count > 0 && <span className="wa-badge">{c.unread_count}</span>}
                </div>
                <div className="wa-thread-tags">
                  {c.temperature && <span className="wa-temp" style={{ color: tempColor[c.temperature] }}>● {c.temperature}</span>}
                  {c.stage && <span className="wa-stage">{c.stage}</span>}
                </div>
              </div>
            </button>
          ))}
        </div>
      </aside>

      {/* ============ MIDDLE: chat ============ */}
      <main className="wa-chat">
        {!activeConv ? (
          <div className="wa-placeholder">
            <MessageCircle size={64} />
            <h2>WhatsApp AI</h2>
            <p>Select a conversation or start a new one to chat with your warm leads — with AI suggesting the best next reply.</p>
          </div>
        ) : (
          <>
            <header className="wa-chat-head">
              <div className="wa-avatar sm" style={{ background: tempColor[activeConv.temperature] || '#25D366' }}>{initials(activeConv.lead_name)}</div>
              <div className="wa-chat-head-info">
                <span className="wa-chat-name">{activeConv.lead_name}</span>
                <span className="wa-chat-sub">
                  <Phone size={11} /> {activeConv.lead_phone}
                  {activeConv.intent ? ` · ${activeConv.intent}` : ''}
                </span>
              </div>
              <div className="wa-chat-actions">
                <button className="wa-action" onClick={() => setShowVisit(true)} title="Book showroom visit">
                  <Calendar size={16} /> <span>Book Visit</span>
                </button>
                {!liveMode && (
                  <button className="wa-action ghost" onClick={() => setShowSim(true)} title="Simulate a customer reply (demo)">
                    <User size={16} /> <span>Customer reply</span>
                  </button>
                )}
                <button className="wa-action ghost icon" onClick={() => setContextOpen(o => !o)} title="Toggle details">
                  <ChevronRight size={16} style={{ transform: contextOpen ? 'rotate(0deg)' : 'rotate(180deg)' }} />
                </button>
              </div>
            </header>

            <div className="wa-messages">
              {grouped.map((g, i) => g.type === 'day' ? (
                <div key={`day-${i}`} className="wa-day"><span>{g.day}</span></div>
              ) : (
                <div key={g.m.id} className={`wa-msg ${g.m.direction === 'outbound' ? 'out' : 'in'}`}>
                  <div className="wa-bubble">
                    {g.m.direction === 'outbound' && (
                      <span className="wa-sender">{g.m.sender_type === 'bot' ? <><Bot size={11} /> AI Template</> : <><User size={11} /> {activeConv.assigned_agent || 'You'}</>}</span>
                    )}
                    {g.m.msg_type === 'image' && g.m.media_url && (
                      <img className="wa-media" src={g.m.media_url} alt="attachment" />
                    )}
                    <span className="wa-text">{g.m.content}</span>
                    <span className="wa-meta">
                      {fmtTime(g.m.created_at)}
                      {g.m.direction === 'outbound' && <CheckCheck size={13} className={g.m.status === 'read' ? 'read' : ''} />}
                    </span>
                  </div>
                </div>
              ))}
              <div ref={msgEndRef} />
            </div>

            {/* AI suggestions bar — appears contextually, dismissible, never crowds */}
            {(suggestShown && (suggestions.length > 0 || suggestLoading)) && (
              <div className="wa-suggest">
                <div className="wa-suggest-head">
                  <span><Sparkles size={13} /> Suggested replies</span>
                  <button onClick={() => { setSuggestShown(false); }} title="Hide"><X size={14} /></button>
                </div>
                <div className="wa-suggest-chips">
                  {suggestLoading && <span className="wa-chip loading">Thinking…</span>}
                  {!suggestLoading && suggestions.map((s, i) => (
                    <button key={i} className="wa-chip" onClick={() => setInput(s)} title="Click to use (you can edit before sending)">
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="wa-composer">
              <button
                className={`wa-sparkle ${suggestShown ? 'on' : ''}`}
                onClick={() => (suggestShown ? setSuggestShown(false) : fetchSuggestions(false))}
                title="AI suggest a reply"
              >
                <Sparkles size={18} />
              </button>
              <input
                className="wa-input"
                placeholder="Type a message…"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
              />
              <button className="wa-send" disabled={sending || !input.trim()} onClick={() => sendMessage()}>
                <Send size={18} />
              </button>
            </div>
          </>
        )}
      </main>

      {/* ============ RIGHT: context / details ============ */}
      {activeConv && contextOpen && (
        <aside className="wa-context">
          <div className="wa-ctx-avatar" style={{ background: tempColor[activeConv.temperature] || '#25D366' }}>{initials(activeConv.lead_name)}</div>
          <h3>{activeConv.lead_name}</h3>
          <p className="wa-ctx-phone"><Phone size={12} /> {activeConv.lead_phone}</p>
          {activeConv.temperature && (
            <span className="wa-ctx-temp" style={{ background: `${tempColor[activeConv.temperature]}22`, color: tempColor[activeConv.temperature] }}>
              <TrendingUp size={12} /> {activeConv.temperature.toUpperCase()} lead
            </span>
          )}

          <div className="wa-ctx-block">
            <div className="wa-ctx-row"><span>Campaign</span><b>{activeConv.campaign_name || '—'}</b></div>
            <div className="wa-ctx-row"><span>Interested in</span><b>{activeConv.product_interest || '—'}</b></div>
            <div className="wa-ctx-row"><span>Stage</span><b>{activeConv.stage || '—'}</b></div>
            {activeConv.intent && <div className="wa-ctx-row"><span>Intent</span><b>{activeConv.intent}</b></div>}
          </div>

          <div className="wa-ctx-block">
            <div className="wa-ctx-head">
              <span><FileText size={14} /> AI Summary</span>
              <button onClick={loadSummary} disabled={summaryLoading}>{summaryLoading ? '…' : 'Generate'}</button>
            </div>
            {summary ? (
              <div className="wa-summary">
                <p>{summary.summary}</p>
                {summary.next_step && <p className="wa-nextstep"><b>Next step:</b> {summary.next_step}</p>}
              </div>
            ) : <p className="wa-ctx-hint">Get an AI recap of this chat and the recommended next step.</p>}
          </div>

          {appointments.length > 0 && (
            <div className="wa-ctx-block">
              <div className="wa-ctx-head"><span><Calendar size={14} /> Showroom Visit</span></div>
              {appointments.map(a => (
                <div key={a.id} className="wa-appt"><b>{a.date}</b> at {a.time} <span className={`wa-appt-status ${a.status}`}>{a.status}</span></div>
              ))}
            </div>
          )}
        </aside>
      )}

      {/* ============ New conversation modal ============ */}
      {showNew && <NewConversationModal onClose={() => setShowNew(false)} onCreated={async (conv) => { setShowNew(false); await loadConversations(); openConversation(conv); }} />}

      {/* ============ Book visit modal ============ */}
      {showVisit && (
        <BookVisitModal
          onClose={() => setShowVisit(false)}
          onBooked={async () => { setShowVisit(false); await loadConversation(activeId); loadConversations(); }}
          convId={activeId}
        />
      )}

      {/* ============ Simulate inbound (demo) ============ */}
      {showSim && (
        <div className="wa-modal-overlay" onClick={() => setShowSim(false)}>
          <div className="wa-modal sm" onClick={e => e.stopPropagation()}>
            <div className="wa-modal-head"><h3>Simulate customer reply</h3><button onClick={() => setShowSim(false)}><X size={18} /></button></div>
            <p className="wa-modal-hint">Demo only — mimics an incoming WhatsApp message from the customer so you can see AI suggestions in action.</p>
            <textarea autoFocus value={simText} onChange={e => setSimText(e.target.value)} placeholder='e.g. "Y" or "Yes, tell me more about the offer"' />
            <div className="wa-modal-actions">
              <button className="wa-btn ghost" onClick={() => setShowSim(false)}>Cancel</button>
              <button className="wa-btn primary" onClick={simulateInbound} disabled={!simText.trim()}>Receive message</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/* ---------------- New conversation modal ---------------- */
const NewConversationModal = ({ onClose, onCreated }) => {
  const [templates, setTemplates] = useState([]);
  const [tplName, setTplName] = useState('');
  const [leadName, setLeadName] = useState('');
  const [phone, setPhone] = useState('');
  const [campaign, setCampaign] = useState('');
  const [product, setProduct] = useState('');
  const [vars, setVars] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    (async () => {
      const res = await fetch(`${API_URL}/api/whatsapp/templates`, { headers: authHeaders() });
      if (res.ok) {
        const d = await res.json();
        setTemplates(d.templates || []);
        if (d.templates?.length) { setTplName(d.templates[0].name); }
      }
    })();
  }, []);

  const tpl = templates.find(t => t.name === tplName);
  useEffect(() => { setVars((tpl?.variables || []).map(() => '')); }, [tplName]);

  // auto fill first variable with lead name if it looks like customer name
  useEffect(() => {
    if (tpl && (tpl.variables || []).length && leadName) {
      setVars(prev => { const n = [...prev]; if (!n[0]) n[0] = leadName; return n; });
    }
  }, [leadName]);

  const rendered = () => {
    let b = tpl?.body || '';
    (vars || []).forEach((v, i) => { b = b.replace(new RegExp(`\\{\\{${i + 1}\\}\\}`, 'g'), v || `{{${i + 1}}}`); });
    return b;
  };

  const submit = async () => {
    setErr('');
    const digits = phone.replace(/[^0-9]/g, '');
    if (!leadName.trim()) return setErr('Enter the lead name');
    if (digits.length < 10) return setErr('Enter a valid phone number with country code');
    if (!tpl) return setErr('Select a template');
    setBusy(true);
    try {
      const res = await fetch(`${API_URL}/api/whatsapp/conversations`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lead_name: leadName.trim(), lead_phone: digits, campaign_name: campaign || null,
          product_interest: product || null, template_name: tpl.name,
          template_body_rendered: rendered(), body_variables: vars, language: tpl.language || 'en'
        })
      });
      if (res.ok) { const d = await res.json(); onCreated(d.conversation); }
      else { const e = await res.json().catch(() => ({})); setErr(e.detail?.meta_error?.message || 'Failed to start conversation'); }
    } catch (e) { setErr('Network error'); } finally { setBusy(false); }
  };

  return (
    <div className="wa-modal-overlay" onClick={onClose}>
      <div className="wa-modal" onClick={e => e.stopPropagation()}>
        <div className="wa-modal-head"><h3>Start a WhatsApp conversation</h3><button onClick={onClose}><X size={18} /></button></div>
        <div className="wa-modal-body">
          <div className="wa-field-row">
            <div className="wa-field"><label>Lead name</label><input value={leadName} onChange={e => setLeadName(e.target.value)} placeholder="e.g. Rahul Sharma" /></div>
            <div className="wa-field"><label>Phone (with country code)</label><input value={phone} onChange={e => setPhone(e.target.value)} placeholder="e.g. 919876543210" /></div>
          </div>
          <div className="wa-field-row">
            <div className="wa-field"><label>Campaign (optional)</label><input value={campaign} onChange={e => setCampaign(e.target.value)} placeholder="e.g. Diwali Offer 2026" /></div>
            <div className="wa-field"><label>Product of interest (optional)</label><input value={product} onChange={e => setProduct(e.target.value)} placeholder="e.g. BrandX SUV X7" /></div>
          </div>
          <div className="wa-field">
            <label>Template message (first message must be an approved template)</label>
            <select value={tplName} onChange={e => setTplName(e.target.value)}>
              {templates.map(t => <option key={t.id} value={t.name}>{t.name} · {t.category}</option>)}
            </select>
          </div>
          {(tpl?.variables || []).length > 0 && (
            <div className="wa-vars">
              {tpl.variables.map((label, i) => (
                <div className="wa-field" key={i}>
                  <label>{`{{${i + 1}}} ${label}`}</label>
                  <input value={vars[i] || ''} onChange={e => setVars(prev => { const n = [...prev]; n[i] = e.target.value; return n; })} placeholder={label} />
                </div>
              ))}
            </div>
          )}
          <div className="wa-preview">
            <span className="wa-preview-label">Preview</span>
            <div className="wa-preview-bubble">{rendered() || 'Select a template…'}</div>
          </div>
          {err && <div className="wa-err">{err}</div>}
        </div>
        <div className="wa-modal-actions">
          <button className="wa-btn ghost" onClick={onClose}>Cancel</button>
          <button className="wa-btn primary" onClick={submit} disabled={busy}>{busy ? 'Sending…' : 'Send & start chat'}</button>
        </div>
      </div>
    </div>
  );
};

/* ---------------- Book visit modal ---------------- */
const BookVisitModal = ({ onClose, onBooked, convId }) => {
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [notes, setNotes] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!date || !time) return;
    setBusy(true);
    try {
      const res = await fetch(`${API_URL}/api/whatsapp/conversations/${convId}/appointment`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ date, time, notes })
      });
      if (res.ok) onBooked();
    } catch (e) { /* ignore */ } finally { setBusy(false); }
  };

  return (
    <div className="wa-modal-overlay" onClick={onClose}>
      <div className="wa-modal sm" onClick={e => e.stopPropagation()}>
        <div className="wa-modal-head"><h3><Calendar size={18} /> Book showroom visit</h3><button onClick={onClose}><X size={18} /></button></div>
        <p className="wa-modal-hint">This confirms the visit, sends a confirmation message to the customer, and moves the lead to “Visit Booked”.</p>
        <div className="wa-field-row">
          <div className="wa-field"><label>Date</label><input type="date" value={date} onChange={e => setDate(e.target.value)} /></div>
          <div className="wa-field"><label>Time</label><input type="time" value={time} onChange={e => setTime(e.target.value)} /></div>
        </div>
        <div className="wa-field"><label>Notes (optional)</label><input value={notes} onChange={e => setNotes(e.target.value)} placeholder="e.g. Interested in test drive" /></div>
        <div className="wa-modal-actions">
          <button className="wa-btn ghost" onClick={onClose}>Cancel</button>
          <button className="wa-btn primary" onClick={submit} disabled={busy || !date || !time}>{busy ? 'Booking…' : 'Confirm visit'}</button>
        </div>
      </div>
    </div>
  );
};

export default WhatsAppAI;
