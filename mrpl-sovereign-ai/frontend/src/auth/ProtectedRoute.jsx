import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from './AuthContext.jsx'


export default function ProtectedRoute() {
    const {
        isAuthenticated,
        loading,
    } = useAuth()

    const location = useLocation()

    if (loading) {
        return (
            <div className="auth-loading">
                Verifying secure local session…
            </div>
        )
    }

    if (!isAuthenticated) {
        return (
            <Navigate
                to="/login"
                replace
                state={{ from: location }}
            />
        )
    }

    return <Outlet />
}