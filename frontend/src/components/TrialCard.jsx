import { useNavigate } from 'react-router-dom'
const STATUS = { RECRUITING: { bg: 'var(--accent-bg)', text: 'var(--accent)' }, COMPLETED: { bg: '#eaf0fb', text: 'var(--info)' }, TERMINATED: { bg: 'var(--danger-bg)', text: 'var(--danger)' } }
export default function TrialCard({ trial }) {
  const nav = useNavigate()
  const sc = STATUS[trial.overall_status] || { bg: 'var(--bg)', text: 'var(--text-2)' }
  return (
    <div onClick={() => nav(`/trials/${trial.nct_id}`)}
      style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '16px 20px', cursor: 'pointer', transition: 'border-color .15s' }}
      onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-2)'}
      onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}>
      <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', marginBottom: '10px' }}>
        <div style={{ flex: 1, fontSize: '14px', fontWeight: 500, lineHeight: 1.4 }}>{trial.brief_title}</div>
        <div style={{ display: 'flex', gap: '6px', flexShrink: 0 }}>
          {trial.phase_numeric && <span style={{ fontSize: '11px', fontWeight: 600, padding: '2px 8px', borderRadius: '99px', background: 'var(--bg)', border: '1px solid var(--border-2)', color: 'var(--text-2)', fontFamily: 'var(--mono)' }}>Phase {trial.phase_numeric}</span>}
          <span style={{ fontSize: '11px', fontWeight: 500, padding: '2px 8px', borderRadius: '99px', background: sc.bg, color: sc.text }}>{trial.overall_status?.replace(/_/g,' ')}</span>
        </div>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px' }}>
        {trial.lead_sponsor_name && <span style={{ fontSize: '12px', color: 'var(--text-2)' }}><span style={{ color: 'var(--text-3)' }}>Sponsor: </span>{trial.lead_sponsor_name}</span>}
        {trial.enrollment_count && <span style={{ fontSize: '12px', color: 'var(--text-2)' }}><span style={{ color: 'var(--text-3)' }}>Enrollment: </span>{trial.enrollment_count.toLocaleString()}</span>}
        {trial.start_date && <span style={{ fontSize: '12px', color: 'var(--text-2)' }}><span style={{ color: 'var(--text-3)' }}>Start: </span>{trial.start_date}</span>}
      </div>
      <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--text-3)', fontFamily: 'var(--mono)' }}>{trial.nct_id}</div>
    </div>
  )
}
