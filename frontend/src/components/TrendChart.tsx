import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { ParameterTrend, MONTH_NAMES } from '../api/client'

interface TrendChartProps {
  trends: ParameterTrend[]
}

// Distinct palette that works on a white/off-white background
const COLORS = ['#2A9D8F', '#E76F51', '#264653', '#E9C46A', '#A8DADC']

interface ChartPoint {
  label: string
  [key: string]: number | string
}

export default function TrendChart({ trends }: TrendChartProps) {
  if (trends.length === 0 || trends.every((t) => t.monthly_scores.length === 0)) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📊</div>
        <h3>No trend data yet</h3>
        <p>Your performance trends will appear here once you've received feedback in multiple cycles.</p>
      </div>
    )
  }

  // Build unified time axis from all trends
  const allPoints = new Map<string, ChartPoint>()
  trends.forEach((trend) => {
    trend.monthly_scores.forEach(({ month, year, score }) => {
      const key = `${year}-${String(month).padStart(2, '0')}`
      const label = `${MONTH_NAMES[month]} ${year}`
      if (!allPoints.has(key)) {
        allPoints.set(key, { label })
      }
      allPoints.get(key)![trend.parameter_name] = score
    })
  })

  const data = Array.from(allPoints.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([, point]) => point)

  const activeParams = trends.filter((t) => t.monthly_scores.length > 0)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
      {/* Combined Line Chart */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Performance Trends</div>
            <div className="card-subtitle">Score over time per parameter (1 = poor, 5 = excellent)</div>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data} margin={{ top: 8, right: 24, left: -8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 12, fill: 'var(--text-secondary)' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[1, 5]}
              ticks={[1, 2, 3, 4, 5]}
              tick={{ fontSize: 12, fill: 'var(--text-secondary)' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: 'white',
                border: '1px solid var(--border)',
                borderRadius: 10,
                boxShadow: 'var(--shadow-md)',
                fontSize: 13,
              }}
              labelStyle={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}
            />
            <Legend
              wrapperStyle={{ fontSize: 13, paddingTop: 16 }}
              iconType="circle"
              iconSize={8}
            />
            {activeParams.map((trend, idx) => (
              <Line
                key={trend.parameter_id}
                type="monotone"
                dataKey={trend.parameter_name}
                stroke={COLORS[idx % COLORS.length]}
                strokeWidth={2.5}
                dot={{ r: 4, fill: COLORS[idx % COLORS.length], strokeWidth: 0 }}
                activeDot={{ r: 6 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Per-parameter score cards */}
      <div className="grid-3">
        {activeParams.map((trend, idx) => {
          const latest = trend.monthly_scores[trend.monthly_scores.length - 1]
          const prev = trend.monthly_scores[trend.monthly_scores.length - 2]
          const delta = latest && prev ? latest.score - prev.score : null
          return (
            <div key={trend.parameter_id} className="stat-card animate-fade-in-up" style={{ animationDelay: `${idx * 60}ms` }}>
              <div className="stat-label">{trend.parameter_name}</div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                <div className="stat-value" style={{ color: COLORS[idx % COLORS.length] }}>
                  {latest?.score ?? '—'}
                </div>
                <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>/5</span>
                {delta !== null && (
                  <span
                    style={{
                      fontSize: 12,
                      fontWeight: 600,
                      color: delta > 0 ? 'var(--success)' : delta < 0 ? 'var(--danger)' : 'var(--text-muted)',
                    }}
                  >
                    {delta > 0 ? `↑ +${delta}` : delta < 0 ? `↓ ${delta}` : '→ 0'}
                  </span>
                )}
              </div>
              <div className="stat-sub">
                Latest: {latest ? `${MONTH_NAMES[latest.month]} ${latest.year}` : 'N/A'}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
