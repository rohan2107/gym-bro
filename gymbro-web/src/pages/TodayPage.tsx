import { useEffect, useMemo, useState } from 'react';
import { api, DailyCheckIn, FoodLog } from '../lib/api';
import { CheckInForm, CheckInFormState } from '../components/Forms';
import { toDateInputValue, handleRequestError } from '../lib/utils';

export default function TodayPage() {
  const today = useMemo(() => toDateInputValue(), []);
  const [selectedDate, setSelectedDate] = useState(today);

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
        const [dateCheckin, meals] = await Promise.all([
          api.getCheckInByDate(selectedDate),
          api.listFoodLogs(),
        ]);
        if (!cancelled) {
          setCheckin(dateCheckin);
          // Filter meals for selected date only (parse date components to avoid timezone issues)
          const [yearStr, monthStr, dayStr] = selectedDate.split('-');
          const year = Number(yearStr);
          const month = Number(monthStr);
          const day = Number(dayStr);
          const dateStart = new Date(year, month - 1, day);
          const dateEnd = new Date(year, month - 1, day + 1);
          const dateMeals = meals.filter((m) => {
            const loggedAt = new Date(m.logged_at);
            return !Number.isNaN(loggedAt.getTime()) && loggedAt >= dateStart && loggedAt < dateEnd;
          });
          setFoodLogs(dateMeals);
          setCheckInForm({
            weight: dateCheckin.weight?.toString() ?? '',
            trained: dateCheckin.trained,
            proteinMet: dateCheckin.protein_met,
            steps: dateCheckin.steps?.toString() ?? '',
            notes: dateCheckin.notes ?? '',
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
  }, [selectedDate]);

  const totalCalories = useMemo(() => {
    return foodLogs.reduce((sum, meal) => sum + (meal.calories ?? 0), 0);
  }, [foodLogs]);

  const totalProtein = useMemo(() => {
    return foodLogs.reduce((sum, meal) => sum + (meal.protein_g ?? 0), 0);
  }, [foodLogs]);

  const goToPreviousDay = () => {
    const date = new Date(selectedDate);
    date.setDate(date.getDate() - 1);
    setSelectedDate(toDateInputValue(date));
  };

  const goToNextDay = () => {
    const [yearStr, monthStr, dayStr] = selectedDate.split('-');
    const currentDate = new Date(Number(yearStr), Number(monthStr) - 1, Number(dayStr));
    currentDate.setDate(currentDate.getDate() + 1);
    
    const [todayYearStr, todayMonthStr, todayDayStr] = today.split('-');
    const todayDate = new Date(Number(todayYearStr), Number(todayMonthStr) - 1, Number(todayDayStr));
    
    // Use Date comparison instead of string comparison
    if (currentDate <= todayDate) {
      setSelectedDate(toDateInputValue(currentDate));
    }
  };

  const goToToday = () => {
    setSelectedDate(today);
  };

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
      const updated = await api.upsertCheckIn(selectedDate, payload);
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
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-2xl font-bold text-gray-900">Daily Check-in</h1>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            max={today}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            aria-label="Select date"
          />
        </div>
        <div className="flex items-center justify-between gap-2">
          <button
            onClick={goToPreviousDay}
            className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
            aria-label="Previous day"
          >
            ← Previous
          </button>
          <p className="text-sm text-gray-500 text-center flex-1">
            {selectedDate === today ? 'Today' : new Date(selectedDate).toLocaleDateString(undefined, { 
              weekday: 'short', 
              month: 'short', 
              day: 'numeric' 
            })}
          </p>
          {selectedDate === today ? (
            <div className="w-20" />
          ) : (
            <button
              onClick={selectedDate < today ? goToNextDay : goToToday}
              className="px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
              aria-label={selectedDate < today ? 'Next day' : 'Go to today'}
            >
              {selectedDate < today ? 'Next →' : 'Today'}
            </button>
          )}
        </div>
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
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {selectedDate === today ? "Today's Summary" : 'Daily Summary'}
            </h2>
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

