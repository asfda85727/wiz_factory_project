import type { ReactNode } from "react"
import { NavLink } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

export function Layout({ children }: { children: ReactNode }) {
  const { logout } = useAuth()

  return (
    <div className="app-shell">
      <nav className="app-sidebar">
        <span className="app-sidebar-title">노무비 관리 시스템</span>
        <div className="app-sidebar-links">
          <NavLink to="/workers" className={({ isActive }) => (isActive ? "active" : "")}>
            근로자 입력
          </NavLink>
          <NavLink to="/attendance" className={({ isActive }) => (isActive ? "active" : "")}>
            일일 출역 입력
          </NavLink>
          <NavLink to="/payroll" className={({ isActive }) => (isActive ? "active" : "")}>
            명세서
          </NavLink>
          <NavLink to="/sites" className={({ isActive }) => (isActive ? "active" : "")}>
            현장 관리
          </NavLink>
        </div>
        <button type="button" className="logout-button" onClick={logout}>
          로그아웃
        </button>
      </nav>
      <main className="app-content">{children}</main>
    </div>
  )
}
