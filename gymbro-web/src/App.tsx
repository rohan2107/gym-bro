import { BrowserRouter, Routes, Route } from 'react-router-dom'
import BottomNav from './components/BottomNav'
import TodayPage from './pages/TodayPage'
import MealsPage from './pages/MealsPage'
import WorkoutPage from './pages/WorkoutPage'
import ProfilePage from './pages/ProfilePage'

export function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 pb-16">
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
          </Routes>
        </main>

        <BottomNav />
      </div>
    </BrowserRouter>
  )
}

export default App
