import { BrowserRouter, Routes, Route } from 'react-router-dom'
import BottomNav from './components/BottomNav'
import { OfflineIndicator } from './components/OfflineIndicator'
import { useAuth } from './contexts/AuthContext'
import TodayPage from './pages/TodayPage'
import MealsPage from './pages/MealsPage'
import WorkoutPage from './pages/WorkoutPage'
import ProfilePage from './pages/ProfilePage'
import LoginPage from './pages/LoginPage'
import AuthCallbackPage from './pages/AuthCallbackPage'

export function App() {
  const { user, isLoading } = useAuth()

  // Show loading spinner while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900">Loading...</h2>
        </div>
      </div>
    )
  }

  // Show login page if not authenticated
  if (!user) {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth/callback" element={<AuthCallbackPage />} />
          <Route path="*" element={<LoginPage />} />
        </Routes>
      </BrowserRouter>
    )
  }

  // User is authenticated - show main app
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 pb-16">
        <OfflineIndicator />
        
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <h1 className="text-3xl font-bold text-gray-900">Gym Bro</h1>
            <p className="text-sm text-gray-600">Track your fitness journey</p>
          </div>
        </header>

        <main className="max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<TodayPage />} />
            <Route path="/meals" element={<MealsPage />} />
            <Route path="/workout" element={<WorkoutPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/auth/callback" element={<AuthCallbackPage />} />
          </Routes>
        </main>

        <BottomNav />
      </div>
    </BrowserRouter>
  )
}

export default App
