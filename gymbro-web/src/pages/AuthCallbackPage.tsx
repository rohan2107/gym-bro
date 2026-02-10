import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function AuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { checkAuth } = useAuth()

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code')
      const error = searchParams.get('error')

      if (error) {
        console.error('OAuth error:', error)
        navigate('/login?error=' + error)
        return
      }

      if (!code) {
        console.error('No authorization code received')
        navigate('/login?error=no_code')
        return
      }

      try {
        // Call backend callback endpoint
        const res = await fetch(`/api/auth/google/callback?code=${code}`, {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        })

        if (res.ok) {
          // Refresh auth state
          await checkAuth()
          // Redirect to home
          navigate('/')
        } else {
          const error = await res.text()
          console.error('Callback failed:', error)
          navigate('/login?error=callback_failed')
        }
      } catch (error) {
        console.error('Callback error:', error)
        navigate('/login?error=network_error')
      }
    }

    handleCallback()
  }, [searchParams, navigate, checkAuth])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
        <h2 className="text-xl font-semibold text-gray-900">Signing you in...</h2>
        <p className="text-gray-600 mt-2">Please wait while we complete authentication</p>
      </div>
    </div>
  )
}
