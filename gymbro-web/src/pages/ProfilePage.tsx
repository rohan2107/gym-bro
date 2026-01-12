export default function ProfilePage() {
  return (
    <div className="p-4 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Profile</h1>

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

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Settings</h2>
        <div className="space-y-3 text-sm text-gray-600">
          <div className="flex justify-between items-center py-2 border-b">
            <span>User ID</span>
            <span className="font-mono text-gray-900">1</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b">
            <span>Version</span>
            <span className="font-mono text-gray-900">0.1.0</span>
          </div>
          <div className="py-2">
            <p className="text-xs text-gray-500">
              Stats and settings functionality will be implemented in Phase 2-3.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

