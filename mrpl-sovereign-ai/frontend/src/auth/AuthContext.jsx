import {
    createContext,
    useContext,
    useEffect,
    useMemo,
    useState,
} from 'react'


const AuthContext = createContext(null)

const TOKEN_KEY = 'mrpl_access_token'
const USER_KEY = 'mrpl_authenticated_user'


export function AuthProvider({ children }) {
    const [token, setToken] = useState(
        () => localStorage.getItem(TOKEN_KEY),
    )

    const [user, setUser] = useState(() => {
        const savedUser = localStorage.getItem(USER_KEY)

        if (!savedUser) {
            return null
        }

        try {
            return JSON.parse(savedUser)
        } catch {
            localStorage.removeItem(USER_KEY)
            return null
        }
    })

    const [loading, setLoading] = useState(true)


    useEffect(() => {
        let mounted = true

        async function verifySession() {
            if (!token) {
                if (mounted) {
                    setLoading(false)
                }
                return
            }

            try {
                const response = await fetch(
                    'http://127.0.0.1:8000/api/auth/me',
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    },
                )

                if (!response.ok) {
                    throw new Error('Session expired')
                }

                const verifiedUser = await response.json()

                if (mounted) {
                    setUser(verifiedUser)
                    localStorage.setItem(
                        USER_KEY,
                        JSON.stringify(verifiedUser),
                    )
                }
            } catch {
                localStorage.removeItem(TOKEN_KEY)
                localStorage.removeItem(USER_KEY)

                if (mounted) {
                    setToken(null)
                    setUser(null)
                }
            } finally {
                if (mounted) {
                    setLoading(false)
                }
            }
        }

        verifySession()

        return () => {
            mounted = false
        }
    }, [token])


    async function login(username, password) {
        const response = await fetch(
            'http://127.0.0.1:8000/api/auth/login',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    password,
                }),
            },
        )

        const data = await response.json()

        if (!response.ok) {
            throw new Error(data.detail || 'Login failed')
        }

        localStorage.setItem(TOKEN_KEY, data.access_token)
        localStorage.setItem(USER_KEY, JSON.stringify(data.user))

        setToken(data.access_token)
        setUser(data.user)

        return data.user
    }


    async function logout() {
        try {
            if (token) {
                await fetch(
                    'http://127.0.0.1:8000/api/auth/logout',
                    {
                        method: 'POST',
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    },
                )
            }
        } finally {
            localStorage.removeItem(TOKEN_KEY)
            localStorage.removeItem(USER_KEY)
            setToken(null)
            setUser(null)
        }
    }


    const value = useMemo(
        () => ({
            token,
            user,
            loading,
            isAuthenticated: Boolean(token && user),
            login,
            logout,
        }),
        [token, user, loading],
    )

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}


export function useAuth() {
    const context = useContext(AuthContext)

    if (!context) {
        throw new Error(
            'useAuth must be used inside AuthProvider',
        )
    }

    return context
}