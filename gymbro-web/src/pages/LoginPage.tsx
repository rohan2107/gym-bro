import { useAuth } from '../contexts/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 space-y-8">
          {/* Logo and Title */}
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-4">
              <span className="text-3xl">💪</span>
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Gym Bro</h1>
            <p className="text-gray-600">Track your fitness journey with ease</p>
          </div>

          {/* Features */}
          <div className="space-y-3 py-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">📊</span>
              <div>
                <h3 className="font-semibold text-gray-900">Daily Check-ins</h3>
                <p className="text-sm text-gray-600">Track weight, steps, and training</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-2xl">🍽️</span>
              <div>
                <h3 className="font-semibold text-gray-900">Meal Logging</h3>
                <p className="text-sm text-gray-600">Monitor calories and macros</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-2xl">💪</span>
              <div>
                <h3 className="font-semibold text-gray-900">Workout Tracking</h3>
                <p className="text-sm text-gray-600">Record your training sessions</p>
              </div>
            </div>
          </div>

          {/* Sign in Button */}
          <div className="space-y-3">
            <button
              onClick={login}
              className="w-full flex items-center justify-center gap-3 bg-white border-2 border-gray-300 rounded-lg px-6 py-3 hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 shadow-sm hover:shadow"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              <span className="font-medium text-gray-700">Continue with Google</span>
            </button>
            
            <p className="text-xs text-center text-gray-500">
              By signing in, you agree to our Terms of Service and Privacy Policy
            </p>
          </div>
        </div>

        {/* Bottom Note */}
        <p className="text-center text-sm text-gray-600 mt-8">
          Built with ❤️ for fitness enthusiasts
        </p>
      </div>
    </div>
  )
}
