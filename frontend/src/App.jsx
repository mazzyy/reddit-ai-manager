import React, { useState, useEffect, useCallback } from 'react'

// ═══════════════════════════════════════════════════
//  API HELPERS
// ═══════════════════════════════════════════════════

const api = async (path, options = {}) => {
  const res = await fetch(`/api${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (res.status === 401) throw new Error('UNAUTHORIZED')
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

const post = (path, body) => api(path, { method: 'POST', body: JSON.stringify(body) })
const patch = (path, body) => api(path, { method: 'PATCH', body: JSON.stringify(body) })
const del = (path) => api(path, { method: 'DELETE' })

// ═══════════════════════════════════════════════════
//  STYLES
// ═══════════════════════════════════════════════════

const globalStyles = `
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'DM Sans', -apple-system, sans-serif;
    background: #0a0b0d;
    color: #e4e6ea;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
  ::selection { background: #ff4500; color: #fff; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
  @keyframes spin { to { transform: rotate(360deg); } }
  .fade-in { animation: fadeIn 0.3s ease-out; }
`

const s = {
  container: {
    maxWidth: 1280,
    margin: '0 auto',
    padding: '0 24px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '20px 0',
    borderBottom: '1px solid #1a1b1e',
    marginBottom: 32,
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    fontSize: 20,
    fontWeight: 700,
    letterSpacing: '-0.02em',
  },
  logoIcon: {
    width: 36,
    height: 36,
    background: 'linear-gradient(135deg, #ff4500, #ff6b35)',
    borderRadius: 10,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 18,
  },
  nav: {
    display: 'flex',
    gap: 4,
    background: '#111214',
    borderRadius: 12,
    padding: 4,
  },
  navBtn: (active) => ({
    padding: '8px 16px',
    border: 'none',
    borderRadius: 8,
    background: active ? '#1f2023' : 'transparent',
    color: active ? '#ff4500' : '#888',
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
    fontFamily: 'inherit',
    transition: 'all 0.15s',
  }),
  card: {
    background: '#111214',
    borderRadius: 16,
    border: '1px solid #1a1b1e',
    padding: 24,
    marginBottom: 20,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: 600,
    marginBottom: 16,
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  input: {
    width: '100%',
    padding: '12px 16px',
    background: '#0a0b0d',
    border: '1px solid #222',
    borderRadius: 10,
    color: '#e4e6ea',
    fontSize: 14,
    fontFamily: 'inherit',
    outline: 'none',
    transition: 'border-color 0.15s',
  },
  textarea: {
    width: '100%',
    padding: '12px 16px',
    background: '#0a0b0d',
    border: '1px solid #222',
    borderRadius: 10,
    color: '#e4e6ea',
    fontSize: 14,
    fontFamily: 'inherit',
    outline: 'none',
    resize: 'vertical',
    minHeight: 120,
    lineHeight: 1.6,
  },
  btn: (variant = 'primary') => ({
    padding: '10px 20px',
    border: 'none',
    borderRadius: 10,
    fontSize: 13,
    fontWeight: 600,
    fontFamily: 'inherit',
    cursor: 'pointer',
    transition: 'all 0.15s',
    ...(variant === 'primary' && { background: '#ff4500', color: '#fff' }),
    ...(variant === 'secondary' && { background: '#1f2023', color: '#e4e6ea', border: '1px solid #333' }),
    ...(variant === 'ghost' && { background: 'transparent', color: '#888' }),
    ...(variant === 'danger' && { background: '#3a1515', color: '#ff5555', border: '1px solid #552222' }),
    ...(variant === 'success' && { background: '#0d3320', color: '#4ade80', border: '1px solid #155e32' }),
  }),
  badge: (color) => ({
    display: 'inline-flex',
    alignItems: 'center',
    padding: '3px 10px',
    borderRadius: 6,
    fontSize: 11,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
    ...(color === 'orange' && { background: '#2a1a0a', color: '#ff8c42' }),
    ...(color === 'green' && { background: '#0d2818', color: '#4ade80' }),
    ...(color === 'blue' && { background: '#0a1a2a', color: '#60a5fa' }),
    ...(color === 'red' && { background: '#2a0a0a', color: '#f87171' }),
    ...(color === 'gray' && { background: '#1a1a1a', color: '#888' }),
    ...(color === 'purple' && { background: '#1a0a2a', color: '#c084fc' }),
  }),
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: 16,
  },
  statusDot: (color) => ({
    width: 8,
    height: 8,
    borderRadius: '50%',
    background: color,
    display: 'inline-block',
  }),
  mono: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 12,
  },
  row: {
    display: 'flex',
    gap: 12,
    alignItems: 'center',
  },
  label: {
    fontSize: 12,
    fontWeight: 500,
    color: '#666',
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
  },
  divider: {
    borderTop: '1px solid #1a1b1e',
    margin: '16px 0',
  },
}

const STATUS_COLORS = {
  draft: 'gray', pending: 'orange', approved: 'blue',
  scheduled: 'purple', published: 'green', failed: 'red',
}

// ═══════════════════════════════════════════════════
//  LOGIN SCREEN
// ═══════════════════════════════════════════════════

function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await post('/auth/login', { username, password })
      onLogin()
    } catch (err) {
      setError('Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
      <div style={{ ...s.card, width: 400, textAlign: 'center' }} className="fade-in">
        <div style={{ ...s.logoIcon, margin: '0 auto 20px', width: 48, height: 48, fontSize: 22 }}>▲</div>
        <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>Reddit AI Manager</h2>
        <p style={{ color: '#666', fontSize: 14, marginBottom: 28 }}>Sign in to your local dashboard</p>
        <form onSubmit={handleLogin}>
          <input
            style={{ ...s.input, marginBottom: 12 }}
            placeholder="Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            autoFocus
          />
          <input
            style={{ ...s.input, marginBottom: 16 }}
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
          />
          {error && <p style={{ color: '#f87171', fontSize: 13, marginBottom: 12 }}>{error}</p>}
          <button style={{ ...s.btn('primary'), width: '100%', padding: '12px 20px' }} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════
//  DASHBOARD HEADER
// ═══════════════════════════════════════════════════

function Header({ view, setView, user, onLogout }) {
  const views = [
    { id: 'create', label: '✦ Create' },
    { id: 'posts', label: '📋 Posts' },
    { id: 'subreddits', label: '🔍 Communities' },
    { id: 'settings', label: '⚙ Settings' },
  ]

  return (
    <div style={s.header}>
      <div style={s.logo}>
        <div style={s.logoIcon}>▲</div>
        <span>Reddit<span style={{ color: '#ff4500' }}>AI</span></span>
      </div>
      <div style={s.nav}>
        {views.map(v => (
          <button key={v.id} style={s.navBtn(view === v.id)} onClick={() => setView(v.id)}>
            {v.label}
          </button>
        ))}
      </div>
      <div style={s.row}>
        <span style={{ ...s.mono, color: '#666' }}>{user}</span>
        <button style={s.btn('ghost')} onClick={onLogout}>Logout</button>
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════
//  CREATE VIEW — AI Content Generation
// ═══════════════════════════════════════════════════

function CreateView({ onPostCreated }) {
  const [idea, setIdea] = useState('')
  const [subreddits, setSubreddits] = useState('')
  const [context, setContext] = useState('')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState(null)
  const [editTitle, setEditTitle] = useState('')
  const [editBody, setEditBody] = useState('')
  const [feedback, setFeedback] = useState('')
  const [refining, setRefining] = useState(false)

  const handleGenerate = async () => {
    setGenerating(true)
    setResult(null)
    try {
      const subs = subreddits.split(',').map(s => s.trim().replace(/^r\//, '')).filter(Boolean)
      const data = await post('/ai/generate', {
        idea,
        target_subreddits: subs,
        extra_context: context,
      })
      setResult(data)
      setEditTitle(data.title)
      setEditBody(data.body)
    } catch (err) {
      alert('Generation failed: ' + err.message)
    } finally {
      setGenerating(false)
    }
  }

  const handleRefine = async () => {
    if (!result || !feedback.trim()) return
    setRefining(true)
    try {
      const data = await post('/ai/refine', { post_id: result.post_id, feedback })
      setResult(prev => ({ ...prev, ...data }))
      setEditTitle(data.title)
      setEditBody(data.body)
      setFeedback('')
    } catch (err) {
      alert('Refinement failed: ' + err.message)
    } finally {
      setRefining(false)
    }
  }

  const handleSaveEdits = async () => {
    if (!result) return
    await patch(`/posts/${result.post_id}`, { title: editTitle, body: editBody })
    alert('Draft saved!')
  }

  const handleApprove = async () => {
    if (!result) return
    try {
      await handleSaveEdits()
      const data = await post(`/posts/${result.post_id}/approve`, {})
      alert(`Post approved! ${data.jobs.length} publish job(s) scheduled.`)
      if (onPostCreated) onPostCreated()
    } catch (err) {
      alert('Approval failed: ' + err.message)
    }
  }

  return (
    <div className="fade-in">
      <div style={s.card}>
        <div style={s.cardTitle}>
          <span style={{ fontSize: 18 }}>✦</span> Create AI-Powered Content
        </div>
        <div style={{ marginBottom: 16 }}>
          <div style={s.label}>Your Idea / Draft</div>
          <textarea
            style={s.textarea}
            placeholder="Describe your content idea, paste a rough draft, or outline your key points..."
            value={idea}
            onChange={e => setIdea(e.target.value)}
            rows={5}
          />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
          <div>
            <div style={s.label}>Target Subreddits</div>
            <input
              style={s.input}
              placeholder="e.g. technology, webdev, startups"
              value={subreddits}
              onChange={e => setSubreddits(e.target.value)}
            />
          </div>
          <div>
            <div style={s.label}>Extra Context (optional)</div>
            <input
              style={s.input}
              placeholder="e.g. audience is beginners, casual tone"
              value={context}
              onChange={e => setContext(e.target.value)}
            />
          </div>
        </div>
        <button
          style={{ ...s.btn('primary'), opacity: generating ? 0.6 : 1 }}
          onClick={handleGenerate}
          disabled={generating || !idea.trim()}
        >
          {generating ? '⟳ Generating with Azure AI...' : '▶ Generate Content'}
        </button>
      </div>

      {result && (
        <div style={s.card} className="fade-in">
          <div style={{ ...s.cardTitle, justifyContent: 'space-between' }}>
            <span>📝 Generated Draft</span>
            <span style={s.badge('orange')}>Pending Review</span>
          </div>

          <div style={{ marginBottom: 12 }}>
            <div style={s.label}>Title</div>
            <input
              style={s.input}
              value={editTitle}
              onChange={e => setEditTitle(e.target.value)}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={s.label}>Body (Markdown)</div>
            <textarea
              style={{ ...s.textarea, minHeight: 200, fontFamily: "'JetBrains Mono', monospace", fontSize: 13 }}
              value={editBody}
              onChange={e => setEditBody(e.target.value)}
            />
          </div>

          <div style={s.divider} />

          <div style={{ marginBottom: 16 }}>
            <div style={s.label}>Refine with Feedback</div>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                style={{ ...s.input, flex: 1 }}
                placeholder="e.g. make it more casual, add a call to action..."
                value={feedback}
                onChange={e => setFeedback(e.target.value)}
              />
              <button
                style={s.btn('secondary')}
                onClick={handleRefine}
                disabled={refining || !feedback.trim()}
              >
                {refining ? '⟳' : '↻ Refine'}
              </button>
            </div>
          </div>

          <div style={{ ...s.row, justifyContent: 'flex-end' }}>
            <button style={s.btn('secondary')} onClick={handleSaveEdits}>💾 Save Draft</button>
            <button style={s.btn('success')} onClick={handleApprove}>✓ Approve & Schedule</button>
          </div>
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════
//  POSTS VIEW — List all posts with status
// ═══════════════════════════════════════════════════

function PostsView() {
  const [posts, setPosts] = useState([])
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState(null)
  const [editMode, setEditMode] = useState(null)
  const [editTitle, setEditTitle] = useState('')
  const [editBody, setEditBody] = useState('')

  const loadPosts = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api(`/posts${filter ? `?status=${filter}` : ''}`)
      setPosts(data.posts)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => { loadPosts() }, [loadPosts])

  const handleDelete = async (id) => {
    if (!confirm('Delete this post?')) return
    await del(`/posts/${id}`)
    loadPosts()
  }

  const handleApprove = async (id) => {
    try {
      const data = await post(`/posts/${id}/approve`, {})
      alert(`Scheduled ${data.jobs.length} job(s)!`)
      loadPosts()
    } catch (err) {
      alert(err.message)
    }
  }

  const startEdit = (p) => {
    setEditMode(p.id)
    setEditTitle(p.title)
    setEditBody(p.body)
  }

  const saveEdit = async (id) => {
    await patch(`/posts/${id}`, { title: editTitle, body: editBody })
    setEditMode(null)
    loadPosts()
  }

  const filters = ['', 'draft', 'pending', 'approved', 'scheduled', 'published', 'failed']

  return (
    <div className="fade-in">
      <div style={{ ...s.row, marginBottom: 20, flexWrap: 'wrap' }}>
        {filters.map(f => (
          <button
            key={f}
            style={s.navBtn(filter === f)}
            onClick={() => setFilter(f)}
          >
            {f || 'All'}
          </button>
        ))}
        <button style={{ ...s.btn('ghost'), marginLeft: 'auto' }} onClick={loadPosts}>↻ Refresh</button>
      </div>

      {loading ? (
        <p style={{ color: '#666', textAlign: 'center', padding: 40 }}>Loading...</p>
      ) : posts.length === 0 ? (
        <div style={{ ...s.card, textAlign: 'center', color: '#666', padding: 60 }}>
          <p style={{ fontSize: 32, marginBottom: 8 }}>∅</p>
          <p>No posts {filter ? `with status "${filter}"` : 'yet'}.</p>
        </div>
      ) : (
        posts.map(p => {
          const isExpanded = expandedId === p.id
          const isEditing = editMode === p.id
          let subs = []
          try { subs = JSON.parse(p.target_subreddits || '[]') } catch {}

          return (
            <div key={p.id} style={{ ...s.card, cursor: 'pointer' }} onClick={() => !isEditing && setExpandedId(isExpanded ? null : p.id)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ ...s.row, marginBottom: 8 }}>
                    <span style={s.badge(STATUS_COLORS[p.status] || 'gray')}>{p.status}</span>
                    <span style={{ ...s.mono, color: '#444' }}>#{p.id}</span>
                    {subs.map(sub => (
                      <span key={sub} style={{ ...s.badge('blue'), fontSize: 10 }}>r/{sub}</span>
                    ))}
                  </div>
                  {isEditing ? (
                    <input style={{ ...s.input, fontSize: 16, fontWeight: 600 }} value={editTitle} onChange={e => setEditTitle(e.target.value)} onClick={e => e.stopPropagation()} />
                  ) : (
                    <h3 style={{ fontSize: 16, fontWeight: 600, color: '#fff' }}>{p.title}</h3>
                  )}
                </div>
                <span style={{ color: '#444', fontSize: 12 }}>
                  {new Date(p.created_at).toLocaleDateString()}
                </span>
              </div>

              {isExpanded && (
                <div style={{ marginTop: 16 }} className="fade-in" onClick={e => e.stopPropagation()}>
                  <div style={s.divider} />
                  {isEditing ? (
                    <textarea style={{ ...s.textarea, minHeight: 160 }} value={editBody} onChange={e => setEditBody(e.target.value)} />
                  ) : (
                    <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.7, color: '#bbb', fontFamily: 'inherit' }}>
                      {p.body}
                    </pre>
                  )}
                  <div style={{ ...s.divider }} />
                  <div style={{ ...s.row, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                    {isEditing ? (
                      <>
                        <button style={s.btn('ghost')} onClick={() => setEditMode(null)}>Cancel</button>
                        <button style={s.btn('primary')} onClick={() => saveEdit(p.id)}>Save</button>
                      </>
                    ) : (
                      <>
                        <button style={s.btn('ghost')} onClick={() => startEdit(p)}>✎ Edit</button>
                        {(p.status === 'pending' || p.status === 'draft') && (
                          <button style={s.btn('success')} onClick={() => handleApprove(p.id)}>✓ Approve</button>
                        )}
                        <button style={s.btn('danger')} onClick={() => handleDelete(p.id)}>✕ Delete</button>
                      </>
                    )}
                  </div>
                  {p.published_urls && (
                    <div style={{ marginTop: 12 }}>
                      <div style={s.label}>Published URLs</div>
                      {JSON.parse(p.published_urls || '[]').map((url, i) => (
                        <a key={i} href={url} target="_blank" rel="noopener noreferrer"
                          style={{ color: '#60a5fa', fontSize: 13, display: 'block', marginBottom: 4 }}>{url}</a>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════
//  SUBREDDITS VIEW — Search, discover, join
// ═══════════════════════════════════════════════════

function SubredditsView() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [saved, setSaved] = useState([])
  const [searching, setSearching] = useState(false)
  const [tab, setTab] = useState('search')

  const loadSaved = async () => {
    try {
      const data = await api('/subreddits/saved')
      setSaved(data.subreddits)
    } catch {}
  }

  useEffect(() => { loadSaved() }, [])

  const handleSearch = async () => {
    if (!query.trim()) return
    setSearching(true)
    try {
      const data = await api(`/subreddits/search?q=${encodeURIComponent(query)}`)
      setResults(data.subreddits)
    } catch (err) {
      alert(err.message)
    } finally {
      setSearching(false)
    }
  }

  const handleJoin = async (name) => {
    try {
      await post(`/subreddits/${name}/join`, {})
      loadSaved()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleLeave = async (name) => {
    try {
      await post(`/subreddits/${name}/leave`, {})
      loadSaved()
    } catch (err) {
      alert(err.message)
    }
  }

  const SubCard = ({ sub, showJoin }) => (
    <div style={{ ...s.card, padding: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 600, color: '#ff4500', marginBottom: 4 }}>
            r/{sub.name}
          </div>
          <div style={{ ...s.mono, color: '#666', marginBottom: 6 }}>
            {(sub.subscribers || 0).toLocaleString()} members
          </div>
          {sub.description && (
            <p style={{ fontSize: 13, color: '#888', lineHeight: 1.5 }}>
              {sub.description.slice(0, 140)}{sub.description.length > 140 ? '…' : ''}
            </p>
          )}
        </div>
        {showJoin && (
          <button style={s.btn(sub.is_joined ? 'danger' : 'success')} onClick={() => sub.is_joined ? handleLeave(sub.name) : handleJoin(sub.name)}>
            {sub.is_joined ? 'Leave' : 'Join'}
          </button>
        )}
      </div>
    </div>
  )

  return (
    <div className="fade-in">
      <div style={s.card}>
        <div style={s.cardTitle}>🔍 Discover Communities</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            style={{ ...s.input, flex: 1 }}
            placeholder="Search subreddits by keyword (e.g. AI, webdev, startups)..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
          />
          <button style={s.btn('primary')} onClick={handleSearch} disabled={searching}>
            {searching ? '⟳' : 'Search'}
          </button>
        </div>
      </div>

      <div style={{ ...s.row, marginBottom: 16 }}>
        <button style={s.navBtn(tab === 'search')} onClick={() => setTab('search')}>
          Search Results ({results.length})
        </button>
        <button style={s.navBtn(tab === 'saved')} onClick={() => setTab('saved')}>
          Saved ({saved.length})
        </button>
      </div>

      <div style={s.grid}>
        {(tab === 'search' ? results : saved).map(sub => (
          <SubCard key={sub.name} sub={sub} showJoin={true} />
        ))}
      </div>

      {(tab === 'search' ? results : saved).length === 0 && (
        <div style={{ ...s.card, textAlign: 'center', color: '#666', padding: 40 }}>
          {tab === 'search' ? 'Search for communities above' : 'No saved communities yet'}
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════
//  SETTINGS VIEW — Connection status & config
// ═══════════════════════════════════════════════════

function SettingsView() {
  const [redditStatus, setRedditStatus] = useState(null)
  const [aiStatus, setAiStatus] = useState(null)
  const [testingAi, setTestingAi] = useState(false)

  useEffect(() => {
    api('/auth/reddit/status').then(setRedditStatus).catch(() => {})
  }, [])

  const connectReddit = async () => {
    try {
      const data = await api('/auth/reddit/start')
      window.location.href = data.auth_url
    } catch (err) {
      alert(err.message)
    }
  }

  const testAi = async () => {
    setTestingAi(true)
    try {
      const data = await api('/ai/test')
      setAiStatus(data)
    } catch (err) {
      setAiStatus({ status: 'error', error: err.message })
    } finally {
      setTestingAi(false)
    }
  }

  return (
    <div className="fade-in">
      <div style={s.grid}>
        <div style={s.card}>
          <div style={s.cardTitle}>
            <span style={s.statusDot(redditStatus?.connected ? '#4ade80' : '#666')} />
            Reddit Connection
          </div>
          {redditStatus?.connected ? (
            <>
              <p style={{ color: '#4ade80', fontSize: 14, marginBottom: 8 }}>
                ✓ Connected as <strong>u/{redditStatus.username}</strong>
              </p>
              <p style={{ ...s.mono, color: '#666' }}>Scope: {redditStatus.scope}</p>
            </>
          ) : (
            <>
              <p style={{ color: '#888', fontSize: 14, marginBottom: 16 }}>Not connected to Reddit</p>
              <button style={s.btn('primary')} onClick={connectReddit}>
                Connect Reddit Account
              </button>
            </>
          )}
        </div>

        <div style={s.card}>
          <div style={s.cardTitle}>
            <span style={s.statusDot(aiStatus?.status === 'ok' ? '#4ade80' : '#666')} />
            Azure OpenAI
          </div>
          {aiStatus ? (
            aiStatus.status === 'ok' ? (
              <p style={{ color: '#4ade80', fontSize: 14 }}>✓ Connected — Model responded: "{aiStatus.response}"</p>
            ) : (
              <p style={{ color: '#f87171', fontSize: 14 }}>✗ Error: {aiStatus.error}</p>
            )
          ) : (
            <p style={{ color: '#888', fontSize: 14, marginBottom: 16 }}>Click to test Azure connectivity</p>
          )}
          <button style={{ ...s.btn('secondary'), marginTop: 12 }} onClick={testAi} disabled={testingAi}>
            {testingAi ? '⟳ Testing...' : '🧪 Test Connection'}
          </button>
        </div>
      </div>

      <div style={s.card}>
        <div style={s.cardTitle}>📖 Configuration Guide</div>
        <div style={{ fontSize: 14, lineHeight: 1.8, color: '#aaa' }}>
          <p style={{ marginBottom: 12 }}>
            <strong style={{ color: '#fff' }}>1. Reddit App:</strong> Register at{' '}
            <span style={{ color: '#60a5fa' }}>reddit.com/prefs/apps</span> → "web app" →
            redirect URI: <code style={{ ...s.mono, color: '#ff4500' }}>http://localhost:8000/api/auth/reddit/callback</code>
          </p>
          <p style={{ marginBottom: 12 }}>
            <strong style={{ color: '#fff' }}>2. Azure OpenAI:</strong> Deploy your model in Azure Portal →
            copy endpoint, key, and deployment name to <code style={{ ...s.mono, color: '#ff4500' }}>.env</code>
          </p>
          <p style={{ marginBottom: 12 }}>
            <strong style={{ color: '#fff' }}>3. Post Spacing:</strong> Configured via{' '}
            <code style={{ ...s.mono, color: '#ff4500' }}>POST_DELAY_MINUTES</code> in .env (default: 12 min).
            Posts are spaced automatically to avoid Reddit spam filters.
          </p>
          <p>
            <strong style={{ color: '#fff' }}>4. Keep Alive:</strong> Your computer must be awake and the server running
            for scheduled posts to publish. Consider using a process manager like PM2 or systemd.
          </p>
        </div>
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════
//  MAIN APP
// ═══════════════════════════════════════════════════

export default function App() {
  const [authenticated, setAuthenticated] = useState(false)
  const [checking, setChecking] = useState(true)
  const [view, setView] = useState('create')
  const [user, setUser] = useState('')

  useEffect(() => {
    api('/auth/me')
      .then(data => {
        setAuthenticated(true)
        setUser(data.user)
      })
      .catch(() => setAuthenticated(false))
      .finally(() => setChecking(false))
  }, [])

  const handleLogout = async () => {
    await post('/auth/logout', {})
    setAuthenticated(false)
  }

  if (checking) return null

  return (
    <>
      <style>{globalStyles}</style>
      {!authenticated ? (
        <LoginScreen onLogin={() => {
          setAuthenticated(true)
          setUser(APP_USERNAME)
          api('/auth/me').then(d => setUser(d.user)).catch(() => {})
        }} />
      ) : (
        <div style={s.container}>
          <Header view={view} setView={setView} user={user} onLogout={handleLogout} />
          {view === 'create' && <CreateView onPostCreated={() => setView('posts')} />}
          {view === 'posts' && <PostsView />}
          {view === 'subreddits' && <SubredditsView />}
          {view === 'settings' && <SettingsView />}
        </div>
      )}
    </>
  )
}
