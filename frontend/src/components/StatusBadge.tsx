type StatusType = 'SUBMITTED' | 'DRAFT' | 'PENDING' | 'HR' | 'EMPLOYEE'

interface StatusBadgeProps {
  status: StatusType | string
}

const MAP: Record<string, { cls: string; label: string }> = {
  SUBMITTED: { cls: 'badge badge-submitted', label: 'Submitted' },
  DRAFT:     { cls: 'badge badge-draft',     label: 'Draft' },
  PENDING:   { cls: 'badge badge-pending',   label: 'Pending' },
  HR:        { cls: 'badge badge-hr',        label: 'HR' },
  EMPLOYEE:  { cls: 'badge badge-employee',  label: 'Employee' },
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const cfg = MAP[status] ?? { cls: 'badge badge-employee', label: status }
  return <span className={cfg.cls}>{cfg.label}</span>
}
