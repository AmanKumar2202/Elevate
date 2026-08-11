interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  center?: boolean
}

export default function Spinner({ size = 'md', center = false }: SpinnerProps) {
  const cls = `spinner ${size === 'sm' ? 'spinner-sm' : size === 'lg' ? 'spinner-lg' : ''}`
  if (center) {
    return (
      <div className="spinner-center">
        <div className={cls} />
      </div>
    )
  }
  return <div className={cls} />
}
