import { useAuth } from '../contexts/AuthContext'

export default function ProfilePage() {
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    if (confirm('Are you sure you want to sign out?')) {
      await logout()
    }
  }

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Profile</h1>

      {/* User Info Card */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Account</h2>
        <div className="flex items-center gap-4 mb-6">
          {user?.picture_url ? (
            <img 
              src={user.picture_url} 
              alt={user.display_name || 'User'} 
              className="w-20 h-20 rounded-full border-2 border-blue-200"
            />
          ) : (
            <div className="w-20 h-20 rounded-full bg-blue-600 flex items-center justify-center text-white text-2xl font-bold">
              {user?.display_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || '?'}
            </div>
          )}
          <div className="flex-1">
            <h3 className="text-xl font-bold text-gray-900">
              {user?.display_name || 'User'}
            </h3>
            <p className="text-gray-600">{user?.email}</p>
            <p className="text-xs text-gray-500 mt-1">ID: {user?.id}</p>
          </div>
        </div>
        
        <button
          onClick={handleLogout}
          className="w-full bg-red-500 text-white py-3 px-4 rounded-lg hover:bg-red-600 transition-colors font-medium"
        >
          Sign Out
        </button>
      </div>

      {/* Stats Placeholder */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">User Stats</h2>
        <div className="space-y-4">
          <div className="flex justify-between items-center p-4 bg-blue-50 rounded-lg">
            <span className="text-gray-700">Total Check-ins</span>
            <span className="text-2xl font-bold text-blue-600">--</span>
          </div>
          <div className="flex justify-between items-center p-4 bg-green-50 rounded-lg">
            <span className="text-gray-700">Total Meals Logged</span>
            <span className="text-2xl font-bold text-green-600">--</span>
          </div>
          <div className="flex justify-between items-center p-4 bg-purple-50 rounded-lg">
            <span className="text-gray-700">Total Workouts</span>
            <span className="text-2xl font-bold text-purple-600">--</span>
          </div>
          <div className="flex justify-between items-center p-4 bg-orange-50 rounded-lg">
            <span className="text-gray-700">Current Streak</span>
            <span className="text-2xl font-bold text-orange-600">-- days</span>
          </div>
        </div>
      </div>

      {/* App Info */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">App Info</h2>
        <div className="space-y-3 text-sm text-gray-600">
          <div className="flex justify-between items-center py-2 border-b">
            <span>Version</span>
            <span className="font-mono text-gray-900">0.2.0 - Phase 2</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b">
            <span>Authentication</span>
            <span className="text-green-600 font-medium">✓ Google OAuth</span>
          </div>
          <div className="py-2">
            <p className="text-xs text-gray-500">
              Advanced stats and analytics will be available in Phase 3.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

