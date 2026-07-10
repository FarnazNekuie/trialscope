import { Outlet, NavLink } from 'react-router-dom'
const s = {
  shell: { minHeight: '100vh', display: 'flex', flexDirection: 'column' },
  nav: { background: 'var(--surface)', borderBottom: '1px solid var(--border)', padding: '0 32px', display: 'flex', alignItems: 'center', gap: '32px', height: '52px', position: 'sticky', top: 0, zIndex: 100 },
  logo: { fontWeight: 600, fontSize: '15px', color: 'var(--text-1)', letterSpacing: '-0.3px', display: 'flex', alignItems: 'center', gap: '8px' },
  dot: { width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent)' },
  links: { display: 'flex', gap: '4px', marginLeft: '8px' },
  link: { fontSize: '13px', color: 'var(--text-2)', padding: '5px 10px', borderRadius: 'var(--radius)', transition: 'all .15s', textDecoration: 'none' },
  active: { color: 'var(--accent)', background: 'var(--accent-bg)', fontWeight: 500 },
  badge: { marginLeft: 'auto', fontSize: '11px', color: 'var(--text-3)', fontFamily: 'var(--mono)' },
  main: { flex: 1, padding: '32px', maxWidth: '1100px', margin: '0 auto', width: '100%' },
}
export default function Layout() {
  return (
    <div style={s.shell}>
      <nav style={s.nav}>
        <div style={s.logo}><div style={s.dot} />TrialScope</div>
        <div style={s.links}>
          <NavLink to="/" end style={({ isActive }) => ({ ...s.link, ...(isActive ? s.active : {}) })}>Search</NavLink>
          <NavLink to="/analytics" style={({ isActive }) => ({ ...s.link, ...(isActive ? s.active : {}) })}>Analytics</NavLink>
        </div>
        <div style={s.badge}>v1.0 · ClinicalTrials.gov</div>
      </nav>
      <main style={s.main}><Outlet /></main>
    </div>
  )
}
