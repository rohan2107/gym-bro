export default function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 safe-area-inset-bottom" aria-label="Main navigation">
      <div className="flex justify-around items-center h-16 max-w-lg mx-auto">
        <button 
          className="flex flex-col items-center justify-center w-16 h-16 text-gray-600 hover:text-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-inset transition-colors" 
          aria-label="Today's overview"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <span className="text-xs mt-1">Today</span>
        </button>

        <button 
          className="flex flex-col items-center justify-center w-16 h-16 text-gray-600 hover:text-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-inset transition-colors" 
          aria-label="Meal planning"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <span className="text-xs mt-1">Meals</span>
        </button>

        <button 
          className="flex flex-col items-center justify-center w-16 h-16 text-gray-600 hover:text-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-inset transition-colors" 
          aria-label="Workout routines"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span className="text-xs mt-1">Workout</span>
        </button>

        <button 
          className="flex flex-col items-center justify-center w-16 h-16 text-gray-600 hover:text-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-inset transition-colors" 
          aria-label="User profile"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <span className="text-xs mt-1">Profile</span>
        </button>
      </div>
    </nav>
  );
}
