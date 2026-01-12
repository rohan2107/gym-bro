import { FormEvent } from 'react'

export type CheckInFormState = {
  weight: string
  trained: boolean
  proteinMet: boolean
  steps: string
  notes: string
}

export function CheckInForm({ state, onChange, onSubmit, busy }: {
  state: CheckInFormState
  onChange: (partial: Partial<CheckInFormState>) => void
  onSubmit: (e: FormEvent) => void
  busy?: boolean
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <label className="text-sm text-gray-700 flex flex-col gap-1">
          Weight (kg)
          <input
            type="number"
            step="0.1"
            min="0"
            value={state.weight}
            onChange={(e) => onChange({ weight: e.target.value })}
            className="rounded border-gray-300 focus:border-blue-500 focus:ring-blue-500"
          />
        </label>
        <label className="text-sm text-gray-700 flex flex-col gap-1">
          Steps
          <input
            type="number"
            min="0"
            value={state.steps}
            onChange={(e) => onChange({ steps: e.target.value })}
            className="rounded border-gray-300 focus:border-blue-500 focus:ring-blue-500"
          />
        </label>
      </div>
      <div className="flex items-center gap-4">
        <label className="inline-flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={state.trained}
            onChange={(e) => onChange({ trained: e.target.checked })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          Trained
        </label>
        <label className="inline-flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={state.proteinMet}
            onChange={(e) => onChange({ proteinMet: e.target.checked })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          Protein met
        </label>
      </div>
      <label className="text-sm text-gray-700 flex flex-col gap-1">
        Notes
        <textarea
          value={state.notes}
          onChange={(e) => onChange({ notes: e.target.value })}
          className="rounded border-gray-300 focus:border-blue-500 focus:ring-blue-500"
          rows={2}
        />
      </label>
      <button
        type="submit"
        disabled={busy}
        className="w-full bg-blue-600 text-white px-4 py-2 rounded font-medium hover:bg-blue-700 disabled:opacity-60"
      >
        {busy ? 'Saving…' : 'Save Check-in'}
      </button>
    </form>
  )
}

export type FoodFormState = {
  description: string
  calories: string
  protein: string
  carbs: string
  fat: string
}

export function FoodForm({ state, onChange, onSubmit, busy }: {
  state: FoodFormState
  onChange: (partial: Partial<FoodFormState>) => void
  onSubmit: (e: FormEvent) => void
  busy?: boolean
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <label className="text-sm text-gray-700 flex flex-col gap-1">
        Description
        <input
          type="text"
          required
          minLength={1}
          value={state.description}
          onChange={(e) => onChange({ description: e.target.value })}
          className="rounded border-gray-300 focus:border-green-500 focus:ring-green-500"
          placeholder="e.g., Chicken breast with rice"
        />
      </label>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <label className="text-sm text-gray-700 flex flex-col gap-1">
          Calories
          <input
            type="number"
            min="0"
            step="1"
            value={state.calories}
            onChange={(e) => onChange({ calories: e.target.value })}
            className="rounded border-gray-300 focus:border-green-500 focus:ring-green-500"
            placeholder="kcal"
          />
        </label>
        <label className="text-sm text-gray-700 flex flex-col gap-1">
          Protein (g)
          <input
            type="number"
            min="0"
            step="0.1"
            value={state.protein}
            onChange={(e) => onChange({ protein: e.target.value })}
            className="rounded border-gray-300 focus:border-green-500 focus:ring-green-500"
            placeholder="g"
          />
        </label>
        <label className="text-sm text-gray-700 flex flex-col gap-1">
          Carbs (g)
          <input
            type="number"
            min="0"
            step="0.1"
            value={state.carbs}
            onChange={(e) => onChange({ carbs: e.target.value })}
            className="rounded border-gray-300 focus:border-green-500 focus:ring-green-500"
            placeholder="g"
          />
        </label>
        <label className="text-sm text-gray-700 flex flex-col gap-1">
          Fat (g)
          <input
            type="number"
            min="0"
            step="0.1"
            value={state.fat}
            onChange={(e) => onChange({ fat: e.target.value })}
            className="rounded border-gray-300 focus:border-green-500 focus:ring-green-500"
            placeholder="g"
          />
        </label>
      </div>
      <button
        type="submit"
        disabled={busy}
        className="w-full bg-green-600 text-white px-4 py-2 rounded font-medium hover:bg-green-700 disabled:opacity-60"
      >
        {busy ? 'Saving…' : 'Log Meal'}
      </button>
    </form>
  )
}

export type WorkoutFormState = {
  name: string
  note: string
}

export function WorkoutForm({ state, onChange, onSubmit, busy }: {
  state: WorkoutFormState
  onChange: (partial: Partial<WorkoutFormState>) => void
  onSubmit: (e: FormEvent) => void
  busy?: boolean
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <label className="text-sm text-gray-700 flex flex-col gap-1">
        Name
        <input
          type="text"
          required
          minLength={1}
          value={state.name}
          onChange={(e) => onChange({ name: e.target.value })}
          className="rounded border-gray-300 focus:border-purple-500 focus:ring-purple-500"
        />
      </label>
      <label className="text-sm text-gray-700 flex flex-col gap-1">
        Note
        <textarea
          value={state.note}
          onChange={(e) => onChange({ note: e.target.value })}
          rows={2}
          className="rounded border-gray-300 focus:border-purple-500 focus:ring-purple-500"
        />
      </label>
      <button
        type="submit"
        disabled={busy}
        className="w-full bg-purple-600 text-white px-4 py-2 rounded font-medium hover:bg-purple-700 disabled:opacity-60"
      >
        {busy ? 'Saving…' : 'Log Workout'}
      </button>
    </form>
  )
}
