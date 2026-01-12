export function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Gym Bro</h1>
          <p className="text-sm text-gray-600">Track your fitness journey</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Today's Stats Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Today</h2>
            <div className="space-y-2">
              <p className="text-sm text-gray-600">Weight: <span className="font-semibold">--</span></p>
              <p className="text-sm text-gray-600">Trained: <span className="font-semibold">No</span></p>
              <p className="text-sm text-gray-600">Protein: <span className="font-semibold">0g</span></p>
            </div>
            <button className="mt-4 w-full bg-blue-600 text-white px-4 py-2 rounded font-medium hover:bg-blue-700">
              Log Check-in
            </button>
          </div>

          {/* Food Logs Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Meals</h2>
            <p className="text-sm text-gray-600 text-center py-4">No meals logged yet</p>
            <button className="w-full bg-green-600 text-white px-4 py-2 rounded font-medium hover:bg-green-700">
              Log Meal
            </button>
          </div>

          {/* Workouts Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Workouts</h2>
            <p className="text-sm text-gray-600 text-center py-4">No workouts logged yet</p>
            <button className="w-full bg-purple-600 text-white px-4 py-2 rounded font-medium hover:bg-purple-700">
              Log Workout
            </button>
          </div>
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-sm text-gray-600">
          <p>&copy; 2026 Gym Bro. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

export default App
