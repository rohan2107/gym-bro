import { useEffect, useState } from 'react';
import { api, FoodLog } from '../lib/api';
import { FoodForm, FoodFormState } from '../components/Forms';

export default function MealsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [foodLogs, setFoodLogs] = useState<FoodLog[]>([]);
  const [saving, setSaving] = useState(false);

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
          setError(err instanceof Error ? err.message : 'Failed to load meals');
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
      const created = await api.createFoodLog({
        description: foodForm.description,
        calories: foodForm.calories ? Number(foodForm.calories) : null,
        protein_g: foodForm.protein ? Number(foodForm.protein) : null,
        carbs_g: foodForm.carbs ? Number(foodForm.carbs) : null,
        fat_g: foodForm.fat ? Number(foodForm.fat) : null,
      });
      setFoodLogs((prev) => [created, ...prev]);
      setFoodForm({ description: '', calories: '', protein: '', carbs: '', fat: '' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save meal');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Meals</h1>

      {error && (
        <div className="rounded bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm mb-4" role="alert">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Log a Meal</h2>
        <FoodForm
          state={foodForm}
          onChange={(p) => setFoodForm((s) => ({ ...s, ...p }))}
          onSubmit={submitFood}
          busy={saving}
        />
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
              <div
                key={meal.id}
                className="border border-gray-200 rounded-lg p-4 hover:border-green-300 transition-colors"
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
                  {new Date(meal.logged_at).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

