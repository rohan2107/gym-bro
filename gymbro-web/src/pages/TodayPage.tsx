import { useEffect, useMemo, useState } from 'react';
import { api, DailyCheckIn, FoodLog } from '../lib/api';
import { CheckInForm, CheckInFormState } from '../components/Forms';
import { toDateInputValue, handleRequestError } from '../lib/utils';

export default function TodayPage() {
  const today = useMemo(() => toDateInputValue(), []);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkin, setCheckin] = useState<DailyCheckIn | null>(null);
  const [foodLogs, setFoodLogs] = useState<FoodLog[]>([]);
  const [saving, setSaving] = useState(false);

  const [checkInForm, setCheckInForm] = useState<CheckInFormState>({
    weight: '',
    trained: false,
    proteinMet: false,
    steps: '',
    notes: '',
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [todayCheckin, meals] = await Promise.all([
          api.getTodayCheckIn(),
          api.listFoodLogs(),
        ]);
        if (!cancelled) {
          setCheckin(todayCheckin);
          // Filter meals for today only (using local date range)
          const todayStart = new Date();
          todayStart.setHours(0, 0, 0, 0);
          const todayEnd = new Date(todayStart);
          todayEnd.setDate(todayEnd.getDate() + 1);
          const todayMeals = meals.filter((m) => {
            const loggedAt = new Date(m.logged_at);
            return !Number.isNaN(loggedAt.getTime()) && loggedAt >= todayStart && loggedAt < todayEnd;
          });
          setFoodLogs(todayMeals);
          setCheckInForm({
            weight: todayCheckin.weight?.toString() ?? '',
            trained: todayCheckin.trained,
            proteinMet: todayCheckin.protein_met,
            steps: todayCheckin.steps?.toString() ?? '',
            notes: todayCheckin.notes ?? '',
          });
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
  }, [today]);

  const totalCalories = useMemo(() => {
    return foodLogs.reduce((sum, meal) => sum + (meal.calories ?? 0), 0);
  }, [foodLogs]);

  const totalProtein = useMemo(() => {
    return foodLogs.reduce((sum, meal) => sum + (meal.protein_g ?? 0), 0);
  }, [foodLogs]);

  const submitCheckin = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = {
        weight: checkInForm.weight ? Number(checkInForm.weight) : null,
        trained: checkInForm.trained,
        protein_met: checkInForm.proteinMet,
        steps: checkInForm.steps ? Number(checkInForm.steps) : null,
        notes: checkInForm.notes || null,
      };
      const updated = await api.upsertCheckIn(today, payload);
      setCheckin(updated);
    } catch (err) {
      setError(handleRequestError(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Today's Check-in</h1>
        <p className="text-sm text-gray-500">{today}</p>
      </div>

      {error && (
        <div className="rounded bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm mb-4" role="alert" aria-live="assertive">
          {error}
        </div>
      )}

      {loading && <div className="text-sm text-gray-600">Loading…</div>}

      {!loading && (
        <>
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Today's Summary</h2>
            <div className="space-y-2 text-sm text-gray-700">
              <div className="flex justify-between">
                <span>Weight:</span>
                <span className="font-semibold">{checkin?.weight ?? '--'} kg</span>
              </div>
              <div className="flex justify-between">
                <span>Trained:</span>
                <span className="font-semibold">{checkin?.trained ? 'Yes ✓' : 'No'}</span>
              </div>
              <div className="pt-2 mt-2 border-t">
                <div className="flex justify-between">
                  <span className="text-green-700">Total Calories:</span>
                  <span className="font-semibold text-green-700">{totalCalories.toFixed(0)} kcal</span>
                </div>
                <div className="flex justify-between mt-1">
                  <span className="text-green-700">Total Protein:</span>
                  <span className="font-semibold text-green-700">{totalProtein.toFixed(1)}g</span>
                </div>
              </div>
              <div className="flex justify-between">
                <span>Protein met:</span>
                <span className="font-semibold">{checkin?.protein_met ? 'Yes ✓' : 'No'}</span>
              </div>
              <div className="flex justify-between">
                <span>Steps:</span>
                <span className="font-semibold">{checkin?.steps?.toLocaleString() ?? '--'}</span>
              </div>
              {checkin?.notes && (
                <div className="pt-2 mt-2 border-t">
                  <span className="text-gray-500 text-xs">Notes:</span>
                  <p className="text-gray-700 mt-1">{checkin.notes}</p>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {checkin ? 'Update Check-in' : 'Daily Check-in Form'}
            </h2>
            <CheckInForm
              state={checkInForm}
              onChange={(p) => setCheckInForm((s) => ({ ...s, ...p }))}
              onSubmit={submitCheckin}
              busy={saving}
            />
          </div>
        </>
      )}
    </div>
  );
}

