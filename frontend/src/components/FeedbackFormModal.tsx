import { useState, useEffect } from 'react'
import { X, Star } from 'lucide-react'
import { feedbackApi, FeedbackParameter, DirectReport, ScoreIn } from '../api/client'
import Spinner from './Spinner'

interface FeedbackFormModalProps {
  cycleId: number
  employee: DirectReport
  onClose: () => void
  onSuccess: () => void
  initialScores?: ScoreIn[]
  initialStatus?: 'DRAFT' | 'SUBMITTED'
}

export default function FeedbackFormModal({
  cycleId,
  employee,
  onClose,
  onSuccess,
  initialScores = [],
  initialStatus,
}: FeedbackFormModalProps) {
  const [parameters, setParameters] = useState<FeedbackParameter[]>([])
  const [scores, setScores] = useState<Record<number, { score: number; comment: string }>>({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    feedbackApi.getParameters().then(({ data }) => {
      setParameters(data)
      // Pre-fill from initial scores
      const initial: Record<number, { score: number; comment: string }> = {}
      data.forEach((p) => {
        const existing = initialScores.find((s) => s.parameter_id === p.id)
        initial[p.id] = existing
          ? { score: existing.score, comment: existing.comment }
          : { score: 0, comment: '' }
      })
      setScores(initial)
      setLoading(false)
    })
  }, [])

  const setScore = (paramId: number, score: number) =>
    setScores((prev) => ({ ...prev, [paramId]: { ...prev[paramId], score } }))

  const setComment = (paramId: number, comment: string) =>
    setScores((prev) => ({ ...prev, [paramId]: { ...prev[paramId], comment } }))

  const isValid = () =>
    parameters.every(
      (p) => scores[p.id]?.score > 0
    )

  const handleSubmit = async (status: 'DRAFT' | 'SUBMITTED') => {
    if (status === 'SUBMITTED' && !isValid()) {
      setError('Please give a score for all parameters before submitting.')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      await feedbackApi.submitFeedback({
        cycle_id: cycleId,
        given_to_id: employee.id,
        scores: parameters
          .filter((p) => status === 'SUBMITTED' || scores[p.id]?.score > 0)
          .map((p) => ({
          parameter_id: p.id,
          score: scores[p.id].score,
          comment: scores[p.id]?.comment.trim() ?? '',
        })),
        status,
      })
      onSuccess()
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'An error occurred. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        {/* Header */}
        <div className="modal-header">
          <div>
            <h2 id="modal-title" style={{ fontSize: 18 }}>
              Feedback for {employee.name}
            </h2>
            {employee.title && (
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>
                {employee.title}
              </p>
            )}
          </div>
          <button id="modal-close-btn" className="btn btn-ghost btn-icon" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {loading ? (
            <Spinner center />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
              {parameters.map((param, idx) => (
                <div key={param.id} className="animate-fade-in-up" style={{ animationDelay: `${idx * 40}ms` }}>
                  <div style={{ marginBottom: 10 }}>
                    <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)', marginBottom: 3 }}>
                      {param.name}
                    </div>
                    {param.description && (
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>
                        {param.description}
                      </div>
                    )}
                  </div>

                  {/* Star Rating */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
                    <div className="star-row">
                      {[1, 2, 3, 4, 5].map((v) => (
                        <button
                          key={v}
                          id={`star-${param.id}-${v}`}
                          className={`star-btn ${(scores[param.id]?.score ?? 0) >= v ? 'active' : 'inactive'}`}
                          onClick={() => setScore(param.id, v)}
                          aria-label={`Rate ${param.name} ${v} out of 5`}
                        >
                          <Star
                            size={22}
                            fill={(scores[param.id]?.score ?? 0) >= v ? '#F59E0B' : 'none'}
                            strokeWidth={1.5}
                          />
                        </button>
                      ))}
                    </div>
                    {scores[param.id]?.score > 0 && (
                      <span
                        style={{
                          fontSize: 13,
                          fontWeight: 600,
                          color: 'var(--primary)',
                          minWidth: 20,
                        }}
                      >
                        {scores[param.id].score}/5
                      </span>
                    )}
                  </div>

                  {/* Comment */}
                  <textarea
                    id={`comment-${param.id}`}
                    className="form-input form-textarea"
                    placeholder={`Add a comment about ${param.name.toLowerCase()}…`}
                    value={scores[param.id]?.comment ?? ''}
                    onChange={(e) => setComment(param.id, e.target.value)}
                    style={{ minHeight: 72 }}
                  />

                  {idx < parameters.length - 1 && <div className="divider" style={{ marginTop: 18, marginBottom: 0 }} />}
                </div>
              ))}

              {error && (
                <div className="alert alert-error" style={{ marginTop: 4 }}>
                  {error}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        {!loading && (
          <div className="modal-footer">
            <button id="cancel-feedback-btn" className="btn btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button
              id="save-draft-btn"
              className="btn btn-secondary"
              onClick={() => handleSubmit('DRAFT')}
              disabled={submitting || initialStatus === 'SUBMITTED'}
            >
              {submitting ? <Spinner size="sm" /> : 'Save Draft'}
            </button>
            <button
              id="submit-feedback-btn"
              className="btn btn-primary"
              onClick={() => handleSubmit('SUBMITTED')}
              disabled={submitting || initialStatus === 'SUBMITTED' || !isValid()}
            >
              {submitting ? <Spinner size="sm" /> : 'Submit Feedback'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
