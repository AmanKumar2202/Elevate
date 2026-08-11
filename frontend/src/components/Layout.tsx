import { ReactNode } from 'react'
import Navbar from './Navbar'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="page-wrapper">
      <Navbar />
      <main className="page-content">{children}</main>
    </div>
  )
}
