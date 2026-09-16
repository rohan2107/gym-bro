import { useState } from 'react'
import { PhotoPrediction } from '../lib/api'

export type ReviewedMeal = {
  description: string
  calories: number | null
  protein_g: number | null
  carbs_g: number | null
  fat_g: number | null
}

function toEditable(prediction: PhotoPrediction): ReviewedMeal {
  const { nutrition } = prediction
  return {
    description: nutrition.name || prediction.label,
    calories: nutrition.calories,
    protein_g: nutrition.protein_g,
    carbs_g: nutrition.carbs_g,
    fat_g: nutrition.fat_g,
  }
}

/**
 * Review step for AI photo predictions.
 *
 * Every value the model produced is editable before it is saved. The USDA
 * figures are per 100g, which is rarely the portion actually eaten, so the
 * numbers are a starting point rather than an answer — the UI says so instead
 * of implying the estimate is authoritative.
 */
export default function MealReview({
  predictions,
  onConfirm,
  onCancel,
  busy,
}: {
  predictions: PhotoPrediction[]
  onConfirm: (meal: ReviewedMeal) => void
  onCancel: () => void
  busy?: boolean
}) {
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [meal, setMeal] = useState<ReviewedMeal>(() => toEditable(predictions[0]))

  const selectPrediction = (index: number) => {
    setSelectedIndex(index)
    setMeal(toEditable(predictions[index]))
  }

  const updateNumber = (field: keyof Omit<ReviewedMeal, 'description'>, value: string) => {
    setMeal((prev) => ({ ...prev, [field]: value === '' ? null : Number(value) }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onConfirm(meal)
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border border-green-200 bg-green-50 rounded-lg p-4"
      aria-label="Review AI meal predictions"
    >
      <h3 className="font-semibold text-gray-900 mb-1">Is this right?</h3>
      <p className="text-xs text-gray-600 mb-3">
        Nutrition is per 100g from USDA. Adjust anything before saving.
      </p>

      {predictions.length > 1 && (
        <fieldset className="mb-3">
          <legend className="text-sm text-gray-700 mb-2">Detected foods</legend>
          <div className="flex flex-wrap gap-2">
            {predictions.map((prediction, index) => (
              <button
                key={`${prediction.label}-${index}`}
                type="button"
                onClick={() => selectPrediction(index)}
                aria-pressed={index === selectedIndex}
                className={`text-sm px-3 py-1.5 rounded border transition-colors ${
                  index === selectedIndex
                    ? 'bg-green-600 text-white border-green-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-green-400'
                }`}
              >
                {prediction.label}{' '}
                <span className="opacity-75">{Math.round(prediction.confidence * 100)}%</span>
              </button>
            ))}
          </div>
        </fieldset>
      )}

      <label className="text-sm text-gray-700 flex flex-col gap-1 mb-3">
        Description
        <input
          type="text"
          value={meal.description}
          onChange={(e) => setMeal((prev) => ({ ...prev, description: e.target.value }))}
          required
          className="rounded border-gray-300 focus:border-green-500 focus:ring-green-500"
          disabled={busy}
        />
      </label>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <label className="text-sm text-gray-700 flex flex-col gap-1">
          Calories
          <input
            type="number"
            min="0"
            max="10000"
            step="1"
            value={meal.calories ?? ''}
            onChange={(e) => updateNumber('calories', e.target.value)}
            className="rounded border-gray-300 focus:border-green-500 focus:ring-green-500"
            disabled={busy}
          />
        </label>
        <label className="text-sm text-gray-700 flex flex-col gap-1">
          Protein (g)
          <input
            type="number"
            min="0"
            max="500"
            step="0.1"
            value={meal.protein_g ?? ''}
            onChange={(e) => updateNumber('protein_g', e.target.value)}
            className="rounded border-gray-300 focus:border-green-500 focus:ring-green-500"
            disabled={busy}
          />
        </label>
        <label className="text-sm text-gray-700 flex flex-col gap-1">
          Carbs (g)
          <input
            type="number"
            min="0"
            max="500"
            step="0.1"
            value={meal.carbs_g ?? ''}
            onChange={(e) => updateNumber('carbs_g', e.target.value)}
            className="rounded border-gray-300 focus:border-green-500 focus:ring-green-500"
            disabled={busy}
          />
        </label>
        <label className="text-sm text-gray-700 flex flex-col gap-1">
          Fat (g)
          <input
            type="number"
            min="0"
            max="500"
            step="0.1"
            value={meal.fat_g ?? ''}
            onChange={(e) => updateNumber('fat_g', e.target.value)}
            className="rounded border-gray-300 focus:border-green-500 focus:ring-green-500"
            disabled={busy}
          />
        </label>
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={busy}
          className="flex-1 bg-green-600 text-white px-4 py-2 rounded font-medium hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {busy ? 'Saving…' : 'Save meal'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={busy}
          className="flex-1 bg-white text-gray-700 border border-gray-300 px-4 py-2 rounded font-medium hover:bg-gray-100 disabled:cursor-not-allowed transition-colors"
        >
          Discard
        </button>
      </div>
    </form>
  )
}
