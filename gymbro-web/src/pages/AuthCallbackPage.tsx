import { useEffect } from 'react'

export default function AuthCallbackPage() {

  useEffect(() => {
    // Get code/error once on mount only
    const code = new URLSearchParams(window.location.search).get('code')
    const error = new URLSearchParams(window.location.search).get('error')

    if (error) {
      console.error('OAuth error:', error)
      window.location.href = '/login?error=' + error
      return
    }

    if (!code) {
      console.error('No authorization code received')
      window.location.href = '/login?error=no_code'
      return
    }

    const handleCallback = async () => {
      try {
        // Call backend callback endpoint
        const res = await fetch(`/api/auth/google/callback?code=${code}`, {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        })

        if (res.ok) {
          // Full page reload to /profile - ensures clean state and no re-renders
          window.location.href = '/profile'
        } else {
          const error = await res.text()
          console.error('Callback failed:', error)
          window.location.href = '/login?error=callback_failed'
        }
      } catch (error) {
        console.error('Callback error:', error)
        window.location.href = '/login?error=network_error'
      }
    }

    handleCallback()
  }, [])

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
