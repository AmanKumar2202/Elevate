import { useState, useEffect } from 'react'
import { AlertTriangle, CheckCircle, Users, ClipboardList } from 'lucide-react'
import Layout from '../components/Layout'
import Spinner from '../components/Spinner'
import { hrApi, Cycle, ManagerPendingReport, MONTH_NAMES } from '../api/client'

export default function HRDashboard() {
  const [cycles, setCycles] = useState<Cycle[]>([])
  const [selectedCycleId, setSelectedCycleId] = useState<number | null>(null)
  const [pending, setPending] = useState<ManagerPendingReport[]>([])
  const [loading, setLoading] = useState(false)
  const [expandedManager, setExpandedManager] = useState<number | null>(null)

  useEffect(() => {
    hrApi.getCycles().then(({ data }) => {
      setCycles(data)
      if (data.length > 0) setSelectedCycleId(data[0].id)
    })
  }, [])

  useEffect(() => {
    if (!selectedCycleId) return
    setLoading(true)
    hrApi
      .getPending(selectedCycleId)
      .then(({ data }) => setPending(data))
      .finally(() => setLoading(false))
  }, [selectedCycleId])

  const totalManagers = pending.length
  const fullySubmitted = pending.filter((p) => p.pending_employees.length === 0).length
  const hasAnyPending = pending.some((p) => p.pending_employees.length > 0)
  const totalPending = pending.reduce((acc, p) => acc + p.pending_employees.length, 0)
  const totalReports = pending.reduce((acc, p) => acc + p.total_reports, 0)
  const totalSubmitted = pending.reduce((acc, p) => acc + p.submitted_count, 0)

  const selectedCycle = cycles.find((c) => c.id === selectedCycleId)

  return (
    <Layout>
      <div className="page-header">
        <h1>HR — Submission Tracker</h1>
        <p>Monitor feedback submission status per manager for each cycle.</p>
      </div>

      {/* Cycle selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28, flexWrap: 'wrap' }}>
        <label htmlFor="hr-cycle-select" style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
          Cycle:
        </label>
        <div className="select-wrapper">
          <select
            id="hr-cycle-select"
            className="select-native"
            value={selectedCycleId ?? ''}
            onChange={(e) => setSelectedCycleId(Number(e.target.value))}
            style={{ minWidth: 180 }}
          >
            {cycles.map((c) => (
              <option key={c.id} value={c.id}>
                {MONTH_NAMES[c.month]} {c.year}
              </option>
            ))}
          </select>
          <span className="select-chevron">▾</span>
        </div>
        {selectedCycle && (
          <span style={{ fontSize: 13, color: 'var(--text-muted)', fontStyle: 'italic' }}>
            {MONTH_NAMES[selectedCycle.month]} {selectedCycle.year}
          </span>
        )}
      </div>

      {loading ? (
        <Spinner center />
      ) : (
        <>
          {/* Summary stats */}
          <div className="stats-grid" style={{ marginBottom: 28 }}>
            <div className="stat-card">
              <div className="stat-label">Managers</div>
              <div className="stat-value">{totalManagers}</div>
              <div className="stat-sub">with direct reports</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Fully Submitted</div>
              <div className="stat-value" style={{ color: 'var(--success)' }}>{fullySubmitted}</div>
              <div className="stat-sub">of {totalManagers} managers</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Total Pending</div>
              <div className="stat-value" style={{ color: 'var(--danger)' }}>{totalPending}</div>
              <div className="stat-sub">feedback submissions</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Completion</div>
              <div className="stat-value" style={{ color: 'var(--primary)' }}>
                {totalReports > 0 ? Math.round((totalSubmitted / totalReports) * 100) : 0}%
              </div>
              <div className="stat-sub">{totalSubmitted} / {totalReports} submitted</div>
            </div>
          </div>

          {/* Overall progress */}
          {totalReports > 0 && (
            <div className="card" style={{ marginBottom: 28, padding: '20px 24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <span style={{ fontWeight: 600, fontSize: 14 }}>Overall Progress</span>
                <span style={{ fontWeight: 700, fontSize: 15, color: 'var(--primary)' }}>
                  {totalSubmitted} / {totalReports}
                </span>
              </div>
              <div className="progress-bar" style={{ height: 8 }}>
                <div
                  className={`progress-fill ${totalSubmitted === totalReports ? 'complete' : ''}`}
                  style={{ width: `${totalReports > 0 ? (totalSubmitted / totalReports) * 100 : 0}%` }}
                />
              </div>
            </div>
          )}

          {/* Alert banner */}
          {hasAnyPending && (
            <div className="alert alert-warning" style={{ marginBottom: 24 }}>
              <AlertTriangle size={16} style={{ flexShrink: 0 }} />
              <span>
                <strong>{totalPending} feedback submission{totalPending !== 1 ? 's' : ''}</strong> are still pending for this cycle. Reach out to the managers listed below.
              </span>
            </div>
          )}
          {!hasAnyPending && pending.length > 0 && (
            <div className="alert alert-success" style={{ marginBottom: 24 }}>
              <CheckCircle size={16} style={{ flexShrink: 0 }} />
              <span>All feedback has been submitted for this cycle. 🎉</span>
            </div>
          )}

          {/* Manager rows */}
          {pending.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📋</div>
              <h3>No data for this cycle</h3>
              <p>Either this cycle has no managers with direct reports, or the cycle does not belong to your company.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {pending.map((item, idx) => {
                const isAllDone = item.pending_employees.length === 0
                const isExpanded = expandedManager === idx
                const pct = item.total_reports > 0 ? Math.round((item.submitted_count / item.total_reports) * 100) : 0

                return (
                  <div
                    key={item.manager.id}
                    className="card animate-fade-in-up"
                    style={{ padding: 0, overflow: 'hidden', animationDelay: `${idx * 40}ms` }}
                  >
                    {/* Manager row header */}
                    <button
                      id={`manager-row-${item.manager.id}`}
                      onClick={() => setExpandedManager(isExpanded ? null : idx)}
                      style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 16,
                        padding: '16px 20px',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        textAlign: 'left',
                      }}
                    >
                      {/* Avatar */}
                      <div
                        style={{
                          width: 40,
                          height: 40,
                          background: isAllDone ? 'var(--success-bg)' : 'var(--danger-bg)',
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 700,
                          fontSize: 15,
                          color: isAllDone ? 'var(--success-text)' : 'var(--danger-text)',
                          flexShrink: 0,
                        }}
                      >
                        {item.manager.name.charAt(0)}
                      </div>

                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                          <span style={{ fontWeight: 600, fontSize: 15 }}>{item.manager.name}</span>
                          {item.manager.title && (
                            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>· {item.manager.title}</span>
                          )}
                          {isAllDone ? (
                            <span className="badge badge-submitted">All submitted</span>
                          ) : (
                            <span className="badge badge-pending">{item.pending_employees.length} pending</span>
                          )}
                        </div>

                        {/* Mini progress bar */}
                        <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 10 }}>
                          <div className="progress-bar" style={{ flex: 1 }}>
                            <div
                              className={`progress-fill ${isAllDone ? 'complete' : ''}`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span style={{ fontSize: 12, color: 'var(--text-secondary)', whiteSpace: 'nowrap', fontWeight: 500 }}>
                            {item.submitted_count} / {item.total_reports}
                          </span>
                        </div>
                      </div>

                      <span style={{ color: 'var(--text-muted)', flexShrink: 0, transition: 'transform 0.2s', transform: isExpanded ? 'rotate(180deg)' : 'none' }}>
                        ▾
                      </span>
                    </button>

                    {/* Expanded: pending employees */}
                    {isExpanded && (
                      <div style={{ borderTop: '1px solid var(--border)', padding: '12px 20px 16px' }}>
                        {item.pending_employees.length === 0 ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--success)', fontSize: 14, padding: '4px 0' }}>
                            <CheckCircle size={16} />
                            All feedback submitted — nothing pending.
                          </div>
                        ) : (
                          <div>
                            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 10 }}>
                              Pending submissions
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                              {item.pending_employees.map((emp) => (
                                <div
                                  key={emp.id}
                                  style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 10,
                                    padding: '8px 12px',
                                    background: 'var(--danger-bg)',
                                    borderRadius: 'var(--radius)',
                                    border: '1px solid #FCA5A5',
                                  }}
                                >
                                  <AlertTriangle size={14} style={{ color: 'var(--danger)', flexShrink: 0 }} />
                                  <div>
                                    <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--danger-text)' }}>
                                      {emp.name}
                                    </span>
                                    {emp.title && (
                                      <span style={{ fontSize: 12, color: 'var(--danger-text)', opacity: 0.7, marginLeft: 6 }}>
                                        · {emp.title}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>

                            {/* Also show who's submitted */}
                            {item.submitted_count > 0 && (
                              <div style={{ marginTop: 12 }}>
                                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>
                                  Submitted ({item.submitted_count})
                                </div>
                                <div style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                                  <CheckCircle size={14} style={{ color: 'var(--success)' }} />
                                  {item.submitted_count} of {item.total_reports} reports have received feedback.
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}
    </Layout>
  )
}
