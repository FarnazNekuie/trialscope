import { useState, useCallback, useEffect } from 'react'
import { searchTrials } from '../api/client'
import TrialCard from '../components/TrialCard'

export default function Search() {
  const [query, setQuery] = useState('')
  const [phase, setPhase] = useState('')
  const [status, setStatus] = useState('')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)

  const fetch = useCallback(async (p = 1) => {
    setLoading(true); setError(null)
    try {
      const params = { page: p, page_size: 20, sort_by: 'enrollment_count' }
      if (query) params.condition = query
      if (phase) params.phase = phase
      if (status) params.status = status
      const res = await searchTrials(params)
      setData(res); setPage(p)
    } catch (e) {
      setError('Could not reach the API — is the backend running?')
      console.error(e)
    } finally { setLoading(false) }
  }, [query, phase, status])

  useEffect(() => { fetch(1) }, [])

  const handleSearch = e => { e.preventDefault(); fetch(1) }
  const totalPages = data ? Math.ceil(data.total / 20) : 0

  return (
    <div>
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 600, marginBottom: '4px', letterSpacing: '-0.4px' }}>Clinical trial explorer</h1>
        <p style={{ color: 'var(--text-2)' }}>Search and filter registered trials from ClinicalTrials.gov</p>
      </div>
      <form onSubmit={handleSearch}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search by condition, sponsor, or keyword..." style={{ flex: 1 }} />
          <button type="submit" style={{ padding: '8px 20px', background: 'var(--accent)', color: '#fff', borderRadius: 'var(--radius)', fontWeight: 500, border: 'none', cursor: 'pointer', whiteSpace: 'nowrap' }}>Search</button>
        </div>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
          <select value={phase} onChange={e => setPhase(e.target.value)} style={{ width: 'auto', minWidth: '130px' }}>
            <option value="">All phases</option>
            {[1,2,3,4].map(p => <option key={p} value={p}>Phase {p}</option>)}
          </select>
          <select value={status} onChange={e => setStatus(e.target.value)} style={{ width: 'auto', minWidth: '180px' }}>
            <option value="">All statuses</option>
            {['RECRUITING','COMPLETED','TERMINATED','ACTIVE_NOT_RECRUITING','NOT_YET_RECRUITING'].map(s => <option key={s} value={s}>{s.replace(/_/g,' ')}</option>)}
          </select>
        </div>
      </form>
      {data && <p style={{ fontSize: '13px', color: 'var(--text-3)', marginBottom: '16px' }}>{data.total.toLocaleString()} trials found</p>}
      {loading && <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-3)' }}>Loading trials...</div>}
      {error && <div style={{ background: 'var(--danger-bg)', borderRadius: 'var(--radius-lg)', padding: '16px', color: 'var(--danger)', marginBottom: '16px' }}>{error}</div>}
      {!loading && data && (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
            {data.results.length === 0
              ? <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-3)' }}>No trials found. Try a different search.</div>
              : data.results.map(t => <TrialCard key={t.nct_id} trial={t} />)}
          </div>
          {totalPages > 1 && (
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', alignItems: 'center' }}>
              <button onClick={() => fetch(page - 1)} disabled={page <= 1} style={{ padding: '7px 16px', borderRadius: 'var(--radius)', border: '1px solid var(--border-2)', background: 'var(--surface)', cursor: page <= 1 ? 'default' : 'pointer', color: page <= 1 ? 'var(--text-3)' : 'var(--text-1)' }}>← Previous</button>
              <span style={{ fontSize: '13px', color: 'var(--text-2)', padding: '0 12px' }}>Page {page} of {totalPages}</span>
              <button onClick={() => fetch(page + 1)} disabled={page >= totalPages} style={{ padding: '7px 16px', borderRadius: 'var(--radius)', border: '1px solid var(--border-2)', background: 'var(--surface)', cursor: page >= totalPages ? 'default' : 'pointer', color: page >= totalPages ? 'var(--text-3)' : 'var(--text-1)' }}>Next →</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
