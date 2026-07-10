import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getTrial } from '../api/client'

function Field({ label, value }) {
  if (!value && value !== 0) return null
  return (
    <div style={{ display: 'flex', gap: '16px', padding: '7px 0', borderBottom: '1px solid var(--border)' }}>
      <div style={{ width: '180px', flexShrink: 0, fontSize: '13px', color: 'var(--text-3)' }}>{label}</div>
      <div style={{ fontSize: '13px', color: 'var(--text-1)' }}>{value}</div>
    </div>
  )
}

export default function TrialDetail() {
  const { nctId } = useParams()
  const nav = useNavigate()
  const [trial, setTrial] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getTrial(nctId).then(setTrial).finally(() => setLoading(false))
  }, [nctId])

  if (loading) return <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-3)' }}>Loading...</div>
  if (!trial) return <div style={{ padding: '48px', textAlign: 'center', color: 'var(--danger)' }}>Trial not found.</div>

  return (
    <div style={{ maxWidth: '780px' }}>
      <button onClick={() => nav(-1)} style={{ fontSize: '13px', color: 'var(--text-2)', marginBottom: '20px' }}>← Back to results</button>
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '11px', fontWeight: 600, fontFamily: 'var(--mono)', color: 'var(--accent)', background: 'var(--accent-bg)', padding: '3px 10px', borderRadius: '99px' }}>{trial.nct_id}</span>
          {trial.phase_numeric && <span style={{ fontSize: '11px', padding: '3px 10px', borderRadius: '99px', border: '1px solid var(--border-2)', color: 'var(--text-2)' }}>Phase {trial.phase_numeric}</span>}
          <span style={{ fontSize: '11px', padding: '3px 10px', borderRadius: '99px', border: '1px solid var(--border-2)', color: 'var(--text-2)' }}>{trial.overall_status?.replace(/_/g,' ')}</span>
        </div>
        <h1 style={{ fontSize: '20px', fontWeight: 600, lineHeight: 1.3, letterSpacing: '-0.3px' }}>{trial.brief_title}</h1>
      </div>
      <div style={{ marginBottom: '28px' }}>
        <Field label="Study type" value={trial.study_type} />
        <Field label="Phase" value={trial.phase_raw} />
        <Field label="Start date" value={trial.start_date} />
        <Field label="Completion" value={trial.completion_date} />
        <Field label="Enrollment" value={trial.enrollment_count?.toLocaleString()} />
        <Field label="Lead sponsor" value={trial.lead_sponsor_name} />
        <Field label="Sponsor class" value={trial.lead_sponsor_class} />
        <Field label="Gender" value={trial.sex} />
        <Field label="Age range" value={trial.minimum_age && trial.maximum_age ? `${trial.minimum_age} – ${trial.maximum_age}` : null} />
        <Field label="Why stopped" value={trial.why_stopped} />
      </div>
      {trial.eligibility_criteria_text && (
        <div style={{ marginBottom: '28px' }}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: '12px' }}>Eligibility criteria</div>
          <div style={{ fontSize: '13px', color: 'var(--text-1)', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '14px 16px', whiteSpace: 'pre-wrap', lineHeight: 1.7, maxHeight: '320px', overflowY: 'auto' }}>
            {trial.eligibility_criteria_text}
          </div>
        </div>
      )}
      <a href={`https://clinicaltrials.gov/study/${trial.nct_id}`} target="_blank" rel="noreferrer" style={{ fontSize: '13px', color: 'var(--accent)' }}>
        View on ClinicalTrials.gov →
      </a>
    </div>
  )
}
