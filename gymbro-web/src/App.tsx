import { useEffect, useMemo, useState } from 'react'
import { api, DailyCheckIn, FoodLog, Workout } from './lib/api'
import { CheckInForm, CheckInFormState, FoodForm, FoodFormState, WorkoutForm, WorkoutFormState } from './components/Forms'

function toDateInputValue(d = new Date()) {
  return d.toISOString().slice(0, 10)
}

export function App() {
  const today = useMemo(() => toDateInputValue(), [])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [checkin, setCheckin] = useState<DailyCheckIn | null>(null)
  const [foodLogs, setFoodLogs] = useState<FoodLog[]>([])
  const [workouts, setWorkouts] = useState<Workout[]>([])

  const [savingCheckin, setSavingCheckin] = useState(false)
  const [savingFood, setSavingFood] = useState(false)
  const [savingWorkout, setSavingWorkout] = useState(false)

  const [checkInForm, setCheckInForm] = useState<CheckInFormState>({
    weight: '',
    trained: false,
    proteinMet: false,
    steps: '',
    notes: '',
  })

  const [foodForm, setFoodForm] = useState<FoodFormState>({
    description: '',
    calories: '',
  })

  const [workoutForm, setWorkoutForm] = useState<WorkoutFormState>({
    name: '',
    note: '',
  })

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const [todayCheckin, meals, wkts] = await Promise.all([
          api.getTodayCheckIn(),
          api.listFoodLogs(),
          api.listWorkouts(),
        ])
        setCheckin(todayCheckin)
        setFoodLogs(meals)
        setWorkouts(wkts)
        setCheckInForm({
          weight: todayCheckin.weight?.toString() ?? '',
          trained: todayCheckin.trained,
          proteinMet: todayCheckin.protein_met,
          steps: todayCheckin.steps?.toString() ?? '',
          notes: todayCheckin.notes ?? '',
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const submitCheckin = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingCheckin(true)
    setError(null)
    try {
      const payload = {
        weight: checkInForm.weight ? Number(checkInForm.weight) : null,
        trained: checkInForm.trained,
        protein_met: checkInForm.proteinMet,
        steps: checkInForm.steps ? Number(checkInForm.steps) : null,
        notes: checkInForm.notes || null,
      }
      const updated = await api.upsertCheckIn(today, payload)
      setCheckin(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save check-in')
    } finally {
      setSavingCheckin(false)
    }
  }

  const submitFood = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingFood(true)
    setError(null)
    try {
      const created = await api.createFoodLog({
        description: foodForm.description,
        calories: foodForm.calories ? Number(foodForm.calories) : null,
      })
      setFoodLogs((prev) => [created, ...prev])
      setFoodForm({ description: '', calories: '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save meal')
    } finally {
      setSavingFood(false)
    }
  }

  const submitWorkout = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingWorkout(true)
    setError(null)
    try {
      const created = await api.createWorkout({ name: workoutForm.name, note: workoutForm.note })
      setWorkouts((prev) => [created, ...prev])
      setWorkoutForm({ name: '', note: '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save workout')
    } finally {
      setSavingWorkout(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Gym Bro</h1>
            <p className="text-sm text-gray-600">Track your fitness journey</p>
          </div>
          <span className="text-sm text-gray-500">User: 1</span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-4">
        {error && <div className="rounded bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm">{error}</div>}
        {loading && <div className="text-sm text-gray-600">Loading…</div>}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Today</h2>
              <p className="text-xs text-gray-500">{today}</p>
            </div>
            <div className="space-y-1 text-sm text-gray-700">
              <div>Weight: <span className="font-semibold">{checkin?.weight ?? '--'} kg</span></div>
              <div>Trained: <span className="font-semibold">{checkin?.trained ? 'Yes' : 'No'}</span></div>
              <div>Protein met: <span className="font-semibold">{checkin?.protein_met ? 'Yes' : 'No'}</span></div>
              <div>Steps: <span className="font-semibold">{checkin?.steps ?? '--'}</span></div>
            </div>
            <CheckInForm
              state={checkInForm}
              onChange={(p) => setCheckInForm((s) => ({ ...s, ...p }))}
              onSubmit={submitCheckin}
              busy={savingCheckin}
            />
          </div>

          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Meals</h2>
            <FoodForm
              state={foodForm}
              onChange={(p) => setFoodForm((s) => ({ ...s, ...p }))}
              onSubmit={submitFood}
              busy={savingFood}
            />
            <div className="space-y-2 max-h-64 overflow-auto">
              {foodLogs.length === 0 && (
                <p className="text-sm text-gray-500">No meals logged yet</p>
              )}
              {foodLogs.map((m) => (
                <div key={m.id} className="border rounded p-3 text-sm flex justify-between">
                  <div>
                    <div className="font-medium text-gray-900">{m.description ?? 'Untitled meal'}</div>
                    <div className="text-gray-600">{m.calories ?? '--'} kcal</div>
                  </div>
                  <div className="text-xs text-gray-500">{new Date(m.logged_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Workouts</h2>
            <WorkoutForm
              state={workoutForm}
              onChange={(p) => setWorkoutForm((s) => ({ ...s, ...p }))}
              onSubmit={submitWorkout}
              busy={savingWorkout}
            />
            <div className="space-y-2 max-h-64 overflow-auto">
              {workouts.length === 0 && <p className="text-sm text-gray-500">No workouts yet</p>}
              {workouts.map((w) => (
                <div key={w.id} className="border rounded p-3 text-sm">
                  <div className="font-medium text-gray-900">{w.name}</div>
                  {w.note && <div className="text-gray-600">{w.note}</div>}
                  <div className="text-xs text-gray-500">{new Date(w.started_at).toLocaleString()}</div>
                </div>
              ))}
            </div>
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
