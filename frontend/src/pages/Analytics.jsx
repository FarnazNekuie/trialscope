import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid, Legend } from 'recharts'
import { getStatsByPhase, getStatsByStatus, getTrends, getStatsBySponsors } from '../api/client'

const TT = { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '6px', fontSize: '12px' }

function Card({ title, children, wide }) {
  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '20px 24px', gridColumn: wide ? 'span 2' : undefined }}>
      <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: '18px' }}>{title}</div>
      {children}
    </div>
  )
}

export default function Analytics() {
  const [phases, setPhases] = useState([])
  const [statuses, setStatuses] = useState([])
  const [trends, setTrends] = useState([])
  const [sponsors, setSponsors] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getStatsByPhase(), getStatsByStatus(), getTrends(), getStatsBySponsors()])
      .then(([p, s, t, sp]) => {
        setPhases(p.map(r => ({ name: `Phase ${r.phase_numeric}`, count: r.count, rate: Number(r.completion_rate || 0) })))
        setStatuses(s.slice(0,8).map(r => ({ name: r.overall_status.replace(/_/g,' '), count: r.count })))
        setTrends(t.filter(r => r.year >= 2005))
        setSponsors(sp.slice(0,6).map(r => ({ name: r.lead_sponsor_class || 'UNKNOWN', count: r.count })))
      }).finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-3)' }}>Loading analytics...</div>

  return (
    <div>
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 600, marginBottom: '4px', letterSpacing: '-0.4px' }}>Analytics</h1>
        <p style={{ color: 'var(--text-2)' }}>Distribution and trends across the trial dataset</p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
        <Card title="Trials by phase">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={phases} barSize={32}>
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: 'var(--text-2)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-3)' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={TT} cursor={{ fill: 'var(--bg)' }} />
              <Bar dataKey="count" fill="#1a6b4a" radius={[4,4,0,0]} name="Trials" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Completion rate by phase (%)">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={phases} barSize={32}>
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: 'var(--text-2)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-3)' }} axisLine={false} tickLine={false} domain={[0,100]} />
              <Tooltip contentStyle={TT} cursor={{ fill: 'var(--bg)' }} formatter={v => `${v}%`} />
              <Bar dataKey="rate" fill="#1a4b8a" radius={[4,4,0,0]} name="Completion %" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Trial registrations over time" wide>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="year" tick={{ fontSize: 11, fill: 'var(--text-3)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-3)' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={TT} />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '12px' }} />
              <Line type="monotone" dataKey="count" stroke="#1a6b4a" strokeWidth={2} dot={false} name="Registered" />
              <Line type="monotone" dataKey="completed" stroke="#1a4b8a" strokeWidth={2} dot={false} name="Completed" />
              <Line type="monotone" dataKey="terminated" stroke="#8a1a1a" strokeWidth={1.5} dot={false} strokeDasharray="4 2" name="Terminated" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
        <Card title="By status">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={statuses} layout="vertical" barSize={14}>
              <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--text-3)' }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: 'var(--text-2)' }} axisLine={false} tickLine={false} width={155} />
              <Tooltip contentStyle={TT} cursor={{ fill: 'var(--bg)' }} />
              <Bar dataKey="count" fill="#92540a" radius={[0,4,4,0]} name="Trials" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="By sponsor class">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={sponsors} barSize={28}>
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--text-2)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-3)' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={TT} cursor={{ fill: 'var(--bg)' }} />
              <Bar dataKey="count" fill="#4a1a6b" radius={[4,4,0,0]} name="Trials" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  )
}
