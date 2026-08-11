import { useState, useEffect, useCallback } from 'react'
import { Users, TrendingUp, CheckCircle, Edit3, Clock } from 'lucide-react'
import Layout from '../components/Layout'
import FeedbackFormModal from '../components/FeedbackFormModal'
import TrendChart from '../components/TrendChart'
import StatusBadge from '../components/StatusBadge'
import Spinner from '../components/Spinner'
import { useAuth } from '../hooks/useAuth'
import {
  feedbackApi,
  usersApi,
  Cycle,
  SubmissionStatus,
  ReceivedFeedback,
  ParameterTrend,
  DirectReport,
  ScoreIn,
  MONTH_NAMES,
} from '../api/client'

type Tab = 'my-feedback' | 'my-team'

export default function DashboardPage() {
  const { user } = useAuth()

  // Tabs: show "My Team" only if user has_reports
  // We re-fetch user profile to get has_reports from server
  const [hasReports, setHasReports] = useState(user?.has_reports ?? false)
  const [activeTab, setActiveTab] = useState<Tab>('my-feedback')

  const [cycles, setCycles] = useState<Cycle[]>([])
  const [selectedCycleId, setSelectedCycleId] = useState<number | null>(null)

  // Manager state
  const [submissions, setSubmissions] = useState<SubmissionStatus[]>([])
  const [loadingSubmissions, setLoadingSubmissions] = useState(false)
  const [modalEmployee, setModalEmployee] = useState<DirectReport | null>(null)
  const [modalInitialStatus, setModalInitialStatus] = useState<'DRAFT' | 'SUBMITTED' | undefined>()
  const [modalInitialScores, setModalInitialScores] = useState<ScoreIn[]>([])

  // Employee state
  const [received, setReceived] = useState<ReceivedFeedback[]>([])
  const [trends, setTrends] = useState<ParameterTrend[]>([])
  const [loadingEmployee, setLoadingEmployee] = useState(false)
  const [expandedFeedback, setExpandedFeedback] = useState<number | null>(null)

  // Load user profile + cycles on mount
  useEffect(() => {
    usersApi.getMe().then(({ data }) => {
      setHasReports(data.has_reports ?? false)
    })
    feedbackApi.getCycles().then(({ data }) => {
      setCycles(data)
      if (data.length > 0) setSelectedCycleId(data[0].id)
    })
    // Load employee data
    setLoadingEmployee(true)
    Promise.all([feedbackApi.getReceived(), feedbackApi.getTrends()])
      .then(([r, t]) => {
        setReceived(r.data)
        setTrends(t.data)
      })
      .finally(() => setLoadingEmployee(false))
  }, [])

  // Load manager submissions when tab or cycle changes
  const loadSubmissions = useCallback(() => {
    if (activeTab !== 'my-team' || !selectedCycleId) return
    setLoadingSubmissions(true)
    feedbackApi
      .getMySubmissions(selectedCycleId)
      .then(({ data }) => setSubmissions(data))
      .finally(() => setLoadingSubmissions(false))
  }, [activeTab, selectedCycleId])

  useEffect(() => {
    loadSubmissions()
  }, [loadSubmissions])

  // Derived stats for manager view
  const submittedCount = submissions.filter((s) => s.status === 'SUBMITTED').length
  const draftCount = submissions.filter((s) => s.status === 'DRAFT').length
  const pendingCount = submissions.filter((s) => s.status === 'PENDING').length

  return (
    <Layout>
      {/* Page header */}
      <div className="page-header">
        <h1>
          {user?.has_reports ? `Welcome, ${user.name.split(' ')[0]}` : 'My Dashboard'}
        </h1>
        <p>
          {user?.title ?? user?.company_name} ·{' '}
          {hasReports ? 'Manager & Employee view' : 'Employee view'}
        </p>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button
          id="tab-my-feedback"
          className={`tab-btn ${activeTab === 'my-feedback' ? 'active' : ''}`}
          onClick={() => setActiveTab('my-feedback')}
        >
          <TrendingUp size={15} />
          My Feedback
        </button>
        {hasReports && (
          <button
            id="tab-my-team"
            className={`tab-btn ${activeTab === 'my-team' ? 'active' : ''}`}
            onClick={() => setActiveTab('my-team')}
          >
            <Users size={15} />
            My Team
          </button>
        )}
      </div>

      {/* ── MY FEEDBACK TAB ─────────────────────────────────────────────────── */}
      {activeTab === 'my-feedback' && (
        <div>
          {loadingEmployee ? (
            <Spinner center />
          ) : (
            <>
              {/* Trends */}
              <div style={{ marginBottom: 40 }}>
                <h2 style={{ marginBottom: 20 }}>Performance Trends</h2>
                <TrendChart trends={trends} />
              </div>

              {/* Received feedback list */}
              <div>
                <h2 style={{ marginBottom: 16 }}>Feedback Received</h2>
                {received.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-state-icon">📬</div>
                    <h3>No feedback yet</h3>
                    <p>Your submitted feedback from managers will appear here.</p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {received.map((fb, idx) => (
                      <div key={idx} className="card animate-fade-in-up" style={{ animationDelay: `${idx * 40}ms`, padding: 0, overflow: 'hidden' }}>
                        <button
                          id={`feedback-toggle-${idx}`}
                          onClick={() => setExpandedFeedback(expandedFeedback === idx ? null : idx)}
                          style={{
                            width: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '16px 20px',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            textAlign: 'left',
                          }}
                        >
                          <div>
                            <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>
                              {MONTH_NAMES[fb.month]} {fb.year}
                            </div>
                            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 3 }}>
                              From {fb.given_by_name}
                            </div>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                            {/* Average score */}
                            {fb.scores.length > 0 && (
                              <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--primary)', lineHeight: 1 }}>
                                  {(fb.scores.reduce((a, s) => a + s.score, 0) / fb.scores.length).toFixed(1)}
                                </div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>avg / 5</div>
                              </div>
                            )}
                            <span style={{ color: 'var(--text-muted)', transition: 'transform 0.2s', transform: expandedFeedback === idx ? 'rotate(180deg)' : 'none' }}>▾</span>
                          </div>
                        </button>

                        {expandedFeedback === idx && (
                          <div style={{ borderTop: '1px solid var(--border)', padding: '16px 20px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                              {fb.scores.map((score, si) => (
                                <div key={si}>
                                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                                    <span style={{ fontWeight: 600, fontSize: 14 }}>{score.parameter_name}</span>
                                    <div style={{ display: 'flex', gap: 3 }}>
                                      {[1,2,3,4,5].map(v => (
                                        <span key={v} style={{ fontSize: 16, color: v <= score.score ? '#F59E0B' : '#E5E7EB' }}>★</span>
                                      ))}
                                      <span style={{ fontSize: 13, color: 'var(--text-secondary)', marginLeft: 6, fontWeight: 600 }}>
                                        {score.score}/5
                                      </span>
                                    </div>
                                  </div>
                                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, padding: '8px 12px', background: 'var(--bg-surface-alt)', borderRadius: 'var(--radius)', borderLeft: '3px solid var(--primary-muted)' }}>
                                    {score.comment}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {/* ── MY TEAM TAB ─────────────────────────────────────────────────────── */}
      {activeTab === 'my-team' && hasReports && (
        <div>
          {/* Cycle selector + stats */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <label htmlFor="cycle-select" style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                Cycle:
              </label>
              <div className="select-wrapper">
                <select
                  id="cycle-select"
                  className="select-native"
                  value={selectedCycleId ?? ''}
                  onChange={(e) => setSelectedCycleId(Number(e.target.value))}
                  style={{ minWidth: 160 }}
                >
                  {cycles.map((c) => (
                    <option key={c.id} value={c.id}>
                      {MONTH_NAMES[c.month]} {c.year}
                    </option>
                  ))}
                </select>
                <span className="select-chevron">▾</span>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="stats-grid" style={{ marginBottom: 24 }}>
            <div className="stat-card">
              <div className="stat-label">Total Reports</div>
              <div className="stat-value">{submissions.length}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Submitted</div>
              <div className="stat-value" style={{ color: 'var(--success)' }}>{submittedCount}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Draft</div>
              <div className="stat-value" style={{ color: 'var(--warning)' }}>{draftCount}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Not Started</div>
              <div className="stat-value" style={{ color: 'var(--danger)' }}>{pendingCount}</div>
            </div>
          </div>

          {/* Progress bar */}
          {submissions.length > 0 && (
            <div style={{ marginBottom: 28 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)' }}>
                  Feedback progress
                </span>
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                  {submittedCount} / {submissions.length}
                </span>
              </div>
              <div className="progress-bar">
                <div
                  className={`progress-fill ${submittedCount === submissions.length ? 'complete' : ''}`}
                  style={{ width: `${submissions.length > 0 ? (submittedCount / submissions.length) * 100 : 0}%` }}
                />
              </div>
            </div>
          )}

          {/* Team table */}
          {loadingSubmissions ? (
            <Spinner center />
          ) : submissions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">👥</div>
              <h3>No direct reports</h3>
              <p>Your direct reports will appear here when added by HR.</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="table" id="team-feedback-table">
                <thead>
                  <tr>
                    <th>Team Member</th>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Submitted</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {submissions.map((sub) => (
                    <tr key={sub.employee.id}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <div
                            style={{
                              width: 34,
                              height: 34,
                              background: 'var(--primary-light)',
                              borderRadius: '50%',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontWeight: 600,
                              fontSize: 13,
                              color: 'var(--primary)',
                              flexShrink: 0,
                            }}
                          >
                            {sub.employee.name.charAt(0)}
                          </div>
                          <div>
                            <div style={{ fontWeight: 600, fontSize: 14 }}>{sub.employee.name}</div>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{sub.employee.email}</div>
                          </div>
                        </div>
                      </td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                        {sub.employee.title ?? '—'}
                      </td>
                      <td>
                        <StatusBadge status={sub.status} />
                      </td>
                      <td style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                        {sub.submitted_at
                          ? new Date(sub.submitted_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
                          : '—'}
                      </td>
                      <td>
                        {sub.status === 'SUBMITTED' ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--success)', fontSize: 13, fontWeight: 500 }}>
                            <CheckCircle size={15} />
                            Done
                          </div>
                        ) : (
                          <button
                            id={`give-feedback-${sub.employee.id}`}
                            className="btn btn-secondary btn-sm"
                            onClick={() => {
                              setModalEmployee(sub.employee)
                              setModalInitialStatus(sub.status === 'DRAFT' ? 'DRAFT' : undefined)
                              setModalInitialScores(sub.scores)
                            }}
                            style={{ gap: 6 }}
                          >
                            {sub.status === 'DRAFT' ? (
                              <><Edit3 size={13} /> Edit Draft</>
                            ) : (
                              <><Clock size={13} /> Give Feedback</>
                            )}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Feedback Form Modal */}
      {modalEmployee && selectedCycleId && (
        <FeedbackFormModal
          cycleId={selectedCycleId}
          employee={modalEmployee}
          initialStatus={modalInitialStatus}
          initialScores={modalInitialScores}
          onClose={() => {
            setModalEmployee(null)
            setModalInitialScores([])
          }}
          onSuccess={() => {
            setModalEmployee(null)
            setModalInitialScores([])
            loadSubmissions()
          }}
        />
      )}
    </Layout>
  )
}
