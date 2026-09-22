import { useState } from 'react'
import { PhotoNutrition, PhotoPrediction } from '../lib/api'

export type ReviewedMeal = {
  description: string
  calories: number | null
  protein_g: number | null
  carbs_g: number | null
  fat_g: number | null
}

// The basis when a prediction carries no portion_g (older responses; the values are per 100g).
const DEFAULT_PORTION_G = 100
// A sanity limit on manual entry, matching the backend's plausibility bound on a model's own
// portion estimate (GeminiRecognizer.MAX_PORTION_GRAMS).
const MAX_PORTION_G = 3000

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

const roundCalories = (value: number) => Math.round(value)
const roundMacro = (value: number) => Math.round(value * 10) / 10

/**
 * A value scaled from its basis portion to a new one, always re-derived from the basis the API
 * returned rather than from whatever is currently on screen — so editing the portion twice
 * does not compound rounding error.
 */
function scale(
  value: number | null,
  basisPortionG: number,
  newPortionG: number,
  round: (n: number) => number
): number | null {
  return value === null ? null : round((value / basisPortionG) * newPortionG)
}

/**
 * What the numbers are, in words. An AI estimate is not from a nutrition database and a USDA
 * figure may be per 100g rather than the portion eaten, so the screen says which it is instead
 * of implying the values are authoritative. Reflects the portion currently in the field, not
 * just the one the API returned, so editing it does not leave a stale claim on screen.
 */
function basisNote(
  nutrition: PhotoNutrition,
  portionG: number | null
): { text: string; estimate: boolean } {
  const portion = portionG !== null ? `${portionG}g` : nutrition.serving_size ?? 'the portion shown'
  if (nutrition.source === 'ai_estimate') {
    return {
      text: `AI estimate for about ${portion}, not from a nutrition database. Check these numbers before saving.`,
      estimate: true,
    }
  }
  if (portion !== '100g') {
    return {
      text: `Estimated for about ${portion}, from USDA values scaled to the portion. Adjust anything before saving.`,
      estimate: false,
    }
  }
  return { text: 'Nutrition is per 100g from USDA. Adjust anything before saving.', estimate: false }
}

/**
 * Review step for AI photo predictions.
 *
 * Every value the model produced is editable before it is saved, so the numbers are a starting
 * point rather than an answer.
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
  const [portionG, setPortionG] = useState<number | null>(
    () => predictions[0].nutrition.portion_g ?? DEFAULT_PORTION_G
  )

  const selectPrediction = (index: number) => {
    setSelectedIndex(index)
    setMeal(toEditable(predictions[index]))
    setPortionG(predictions[index].nutrition.portion_g ?? DEFAULT_PORTION_G)
  }

  const updateNumber = (field: keyof Omit<ReviewedMeal, 'description'>, value: string) => {
    setMeal((prev) => ({ ...prev, [field]: value === '' ? null : Number(value) }))
  }

  const updatePortion = (value: string) => {
    if (value === '') {
      // Waiting for a usable number; leave the macros as they last were rather than blanking them.
      setPortionG(null)
      return
    }
    const newPortionG = Number(value)
    setPortionG(newPortionG)
    if (!(newPortionG > 0)) return

    const { nutrition } = predictions[selectedIndex]
    const basisPortionG = nutrition.portion_g ?? DEFAULT_PORTION_G
    setMeal((prev) => ({
      ...prev,
      calories: scale(nutrition.calories, basisPortionG, newPortionG, roundCalories),
      protein_g: scale(nutrition.protein_g, basisPortionG, newPortionG, roundMacro),
      carbs_g: scale(nutrition.carbs_g, basisPortionG, newPortionG, roundMacro),
      fat_g: scale(nutrition.fat_g, basisPortionG, newPortionG, roundMacro),
    }))
  }

  const basis = basisNote(predictions[selectedIndex].nutrition, portionG)

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
      <p
        className={`text-xs mb-3 ${basis.estimate ? 'text-amber-800 bg-amber-50 rounded px-2 py-1' : 'text-gray-600'}`}
        data-testid="basis-note"
      >
        {basis.text}
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

      <label className="text-sm text-gray-700 flex flex-col gap-1 mb-3">
        Portion (g)
        <input
          type="number"
          min="1"
          max={MAX_PORTION_G}
          step="1"
          value={portionG ?? ''}
          onChange={(e) => updatePortion(e.target.value)}
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
