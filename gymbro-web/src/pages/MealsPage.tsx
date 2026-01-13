import { useEffect, useState } from 'react';
import { api, FoodLog } from '../lib/api';
import { FoodForm, FoodFormState } from '../components/Forms';
import { formatRelativeDateTime, handleRequestError } from '../lib/utils';

// Validation helper for numeric inputs
function parseAndValidate(value: string, name: string, min: number, max: number): number | null {
  if (!value) return null;
  const num = Number(value);
  if (!Number.isFinite(num) || num < min || num > max) {
    throw new Error(`${name} must be between ${min} and ${max}`);
  }
  return num;
}

export default function MealsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [foodLogs, setFoodLogs] = useState<FoodLog[]>([]);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [foodForm, setFoodForm] = useState<FoodFormState>({
    description: '',
    calories: '',
    protein: '',
    carbs: '',
    fat: '',
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const meals = await api.listFoodLogs();
        if (!cancelled) {
          setFoodLogs(meals);
        }
      } catch (err) {
        if (!cancelled) {
          setError(handleRequestError(err));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  const submitFood = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const foodData = {
        description: foodForm.description,
        calories: parseAndValidate(foodForm.calories, 'Calories', 0, 10000),
        protein_g: parseAndValidate(foodForm.protein, 'Protein', 0, 500),
        carbs_g: parseAndValidate(foodForm.carbs, 'Carbs', 0, 500),
        fat_g: parseAndValidate(foodForm.fat, 'Fat', 0, 500),
      };

      if (editingId !== null) {
        // Update existing meal
        const updated = await api.updateFoodLog(editingId, foodData);
        setFoodLogs((prev) => prev.map((m) => (m.id === editingId ? updated : m)));
        setEditingId(null);
      } else {
        // Create new meal
        const created = await api.createFoodLog(foodData);
        setFoodLogs((prev) => [created, ...prev]);
      }
      
      setFoodForm({ description: '', calories: '', protein: '', carbs: '', fat: '' });
    } catch (err) {
      setError(handleRequestError(err));
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (meal: FoodLog) => {
    setEditingId(meal.id);
    setFoodForm({
      description: meal.description || '',
      calories: meal.calories?.toString() || '',
      protein: meal.protein_g?.toString() || '',
      carbs: meal.carbs_g?.toString() || '',
      fat: meal.fat_g?.toString() || '',
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setFoodForm({ description: '', calories: '', protein: '', carbs: '', fat: '' });
  };

  const deleteMeal = async (id: number) => {
    if (!confirm('Delete this meal?')) return;
    
    try {
      await api.deleteFoodLog(id);
      setFoodLogs((prev) => prev.filter((m) => m.id !== id));
      if (editingId === id) {
        cancelEdit();
      }
    } catch (err) {
      setError(handleRequestError(err));
    }
  };

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Meals</h1>

      {error && (
        <div className="rounded bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm mb-4" role="alert" aria-live="assertive">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {editingId ? 'Edit Meal' : 'Log a Meal'}
        </h2>
        <FoodForm
          state={foodForm}
          onChange={(p) => setFoodForm((s) => ({ ...s, ...p }))}
          onSubmit={submitFood}
          busy={saving}
        />
        {editingId && (
          <button
            type="button"
            onClick={cancelEdit}
            className="mt-3 w-full bg-gray-200 text-gray-700 px-4 py-2 rounded font-medium hover:bg-gray-300"
          >
            Cancel Edit
          </button>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Meal History</h2>

        {loading && <div className="text-sm text-gray-600">Loading meals…</div>}

        {!loading && foodLogs.length === 0 && (
          <p className="text-sm text-gray-500">No meals logged yet. Start by adding one above!</p>
        )}

        {!loading && foodLogs.length > 0 && (
          <div className="space-y-3">
            {foodLogs.map((meal) => (
              <article
                key={meal.id}
                className="border border-gray-200 rounded-lg p-4 hover:border-green-300 transition-colors"
                aria-label={`Meal: ${meal.description || 'Untitled meal'}`}
              >
                <div className="font-medium text-gray-900 mb-2">
                  {meal.description || 'Untitled meal'}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                  <div className="text-gray-600">
                    <span className="text-gray-500">Calories:</span>{' '}
                    {meal.calories !== null ? `${meal.calories} kcal` : '--'}
                  </div>
                  <div className="text-gray-600">
                    <span className="text-gray-500">Protein:</span>{' '}
                    {meal.protein_g !== null ? `${meal.protein_g}g` : '--'}
                  </div>
                  <div className="text-gray-600">
                    <span className="text-gray-500">Carbs:</span>{' '}
                    {meal.carbs_g !== null ? `${meal.carbs_g}g` : '--'}
                  </div>
                  <div className="text-gray-600">
                    <span className="text-gray-500">Fat:</span>{' '}
                    {meal.fat_g !== null ? `${meal.fat_g}g` : '--'}
                  </div>
                </div>
                <div className="text-xs text-gray-500 mt-2">
                  {formatRelativeDateTime(meal.logged_at)}
                </div>
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => startEdit(meal)}
                    className="flex-1 text-sm bg-blue-50 text-blue-700 px-3 py-1.5 rounded hover:bg-blue-100 transition-colors"
                    aria-label={`Edit ${meal.description || 'meal'}`}
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => deleteMeal(meal.id)}
                    className="flex-1 text-sm bg-red-50 text-red-700 px-3 py-1.5 rounded hover:bg-red-100 transition-colors"
                    aria-label={`Delete ${meal.description || 'meal'}`}
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

