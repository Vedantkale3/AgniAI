import React, { useEffect, useState } from 'react'
import { Routes, Route, NavLink, Outlet } from 'react-router-dom'
import {
  ShieldCheck,
  ShieldAlert,
  MessageSquare,
  Boxes,
  Database,
  TerminalSquare,
  FileStack,
  LogOut,
} from 'lucide-react'

import ChatWorkbench from './pages/ChatWorkbench.jsx'
import ModelRegistryPage from './pages/ModelRegistryPage.jsx'
import KnowledgeBasePage from './pages/KnowledgeBasePage.jsx'
import SandboxPage from './pages/SandboxPage.jsx'
import DeliverablesPage from './pages/DeliverablesPage.jsx'
import LoginPage from './pages/LoginPage.jsx'

import NetworkMonitor from './components/NetworkMonitor.jsx'
import RoutingPreview from './components/RoutingPreview.jsx'

import ProtectedRoute from './auth/ProtectedRoute.jsx'
import { useAuth } from './auth/AuthContext.jsx'
import { networkStatus } from './api/client.js'


function WorkbenchLayout() {
  const [sealed, setSealed] = useState(null)
  const { user, logout } = useAuth()

  useEffect(() => {
    let mounted = true

    const poll = async () => {
      try {
        const res = await networkStatus()

        if (mounted) {
          setSealed(res.data.sovereignty_status === 'SEALED')
        }
      } catch (error) {
        if (mounted) {
          setSealed(null)
        }
      }
    }

    poll()

    const interval = setInterval(poll, 4000)

    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  const badgeClass =
      sealed === true
          ? 'sovereignty-badge'
          : 'sovereignty-badge breach'

  const badgeText =
      sealed === true
          ? 'SEALED — 0 external calls'
          : sealed === false
              ? 'BREACH DETECTED — check Network Sentinel'
              : 'Checking network status...'

  async function handleLogout() {
    await logout()
  }

  return (
      <div className="app-shell">
        <aside className="sidebar">
          <div className="brand">
            <ShieldCheck size={22} color="#2dd4bf" />

            <div>
              <div className="brand-title">
                Agni AI
                <br />
                Workbench
              </div>

              <div className="brand-sub">
                AIR-GAPPED &middot; MULTI-MODEL
              </div>
            </div>
          </div>

          <nav className="sidebar-navigation">
            <NavLink
                to="/"
                end
                className={({ isActive }) =>
                    `nav-item${isActive ? ' active' : ''}`
                }
            >
              <MessageSquare size={16} />
              Agent Workbench
            </NavLink>

            <NavLink
                to="/models"
                className={({ isActive }) =>
                    `nav-item${isActive ? ' active' : ''}`
                }
            >
              <Boxes size={16} />
              Model Registry
            </NavLink>

            <NavLink
                to="/knowledge"
                className={({ isActive }) =>
                    `nav-item${isActive ? ' active' : ''}`
                }
            >
              <Database size={16} />
              Knowledge Base
            </NavLink>

            <NavLink
                to="/sandbox"
                className={({ isActive }) =>
                    `nav-item${isActive ? ' active' : ''}`
                }
            >
              <TerminalSquare size={16} />
              Code Sandbox
            </NavLink>

            <NavLink
                to="/deliverables"
                className={({ isActive }) =>
                    `nav-item${isActive ? ' active' : ''}`
                }
            >
              <FileStack size={16} />
              Deliverables
            </NavLink>
          </nav>

          <div className="sidebar-bottom">
            <div className="account-panel">
              <div className="account-name">
                <span>Signed in as</span>
                <strong>{user?.username || 'Operator'}</strong>
              </div>

              <button
                  type="button"
                  className="logout-button"
                  onClick={handleLogout}
              >
                <LogOut size={15} />
                Log out
              </button>
            </div>

            <div className={badgeClass}>
              {sealed === true ? (
                  <ShieldCheck size={13} style={{ marginRight: '6px' }} />
              ) : (
                  <ShieldAlert size={13} style={{ marginRight: '6px' }} />
              )}

              {badgeText}
            </div>
          </div>
        </aside>

        <main className="main-content">
          <Outlet />
        </main>

        <aside className="right-rail">
          <NetworkMonitor />
          <RoutingPreview />
        </aside>
      </div>
  )
}


export default function App() {
  return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<WorkbenchLayout />}>
            <Route path="/" element={<ChatWorkbench />} />
            <Route path="/models" element={<ModelRegistryPage />} />
            <Route path="/knowledge" element={<KnowledgeBasePage />} />
            <Route path="/sandbox" element={<SandboxPage />} />
            <Route path="/deliverables" element={<DeliverablesPage />} />
          </Route>
        </Route>
      </Routes>
  )
}