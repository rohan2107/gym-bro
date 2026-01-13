import { useEffect, useState } from 'react';
import { api, Workout } from '../lib/api';
import { WorkoutForm, WorkoutFormState } from '../components/Forms';
import { handleRequestError } from '../lib/utils';

export default function WorkoutPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [workoutForm, setWorkoutForm] = useState<WorkoutFormState>({
    name: '',
    note: '',
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const wkts = await api.listWorkouts();
        if (!cancelled) {
          setWorkouts(wkts);
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

  const submitWorkout = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const workoutData = {
        name: workoutForm.name,
        note: workoutForm.note || null,
      };

      if (editingId !== null) {
        // Update existing workout
        const updated = await api.updateWorkout(editingId, workoutData);
        setWorkouts((prev) => prev.map((w) => (w.id === editingId ? updated : w)));
        setEditingId(null);
      } else {
        // Create new workout
        const created = await api.createWorkout(workoutData);
        setWorkouts((prev) => [created, ...prev]);
      }

      setWorkoutForm({ name: '', note: '' });
    } catch (err) {
      setError(handleRequestError(err));
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (workout: Workout) => {
    setEditingId(workout.id);
    setWorkoutForm({
      name: workout.name,
      note: workout.note || '',
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setWorkoutForm({ name: '', note: '' });
  };

  const deleteWorkout = async (id: number) => {
    if (!confirm('Delete this workout?')) return;

    try {
      await api.deleteWorkout(id);
      setWorkouts((prev) => prev.filter((w) => w.id !== id));
      if (editingId === id) {
        cancelEdit();
      }
    } catch (err) {
      setError(handleRequestError(err));
    }
  };

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Workouts</h1>

      {error && (
        <div className="rounded bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm mb-4" role="alert" aria-live="assertive">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {editingId ? 'Edit Workout' : 'Quick Log'}
        </h2>
        <WorkoutForm
          state={workoutForm}
          onChange={(p) => setWorkoutForm((s) => ({ ...s, ...p }))}
          onSubmit={submitWorkout}
          busy={saving}
        />
        {editingId ? (
          <button
            type="button"
            onClick={cancelEdit}
            className="mt-3 w-full bg-gray-200 text-gray-700 px-4 py-2 rounded font-medium hover:bg-gray-300"
          >
            Cancel Edit
          </button>
        ) : (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg text-sm">
            <p className="text-gray-700">
              <strong>Coming soon:</strong> Import workouts from Strong app (paste JSON).
              For now, use the form above to log workouts manually.
            </p>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Workout History
          {!loading && workouts.length > 0 && (
            <span className="ml-2 text-sm font-normal text-gray-500">
              ({workouts.length} total)
            </span>
          )}
        </h2>

        {loading && <div className="text-sm text-gray-600">Loading workouts…</div>}

        {!loading && workouts.length === 0 && (
          <div className="text-center py-8">
            <div className="text-4xl mb-2">💪</div>
            <p className="text-sm text-gray-500">No workouts logged yet.</p>
            <p className="text-xs text-gray-400 mt-1">Start by logging one above!</p>
          </div>
        )}

        {!loading && workouts.length > 0 && (
          <div className="space-y-3">
            {workouts.map((workout) => (
              <article
                key={workout.id}
                className="border border-gray-200 rounded-lg p-4 hover:border-purple-300 transition-colors"
                aria-label={`Workout: ${workout.name}`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 text-lg">{workout.name}</div>
                    {workout.note && (
                      <div className="text-sm text-gray-600 mt-1">{workout.note}</div>
                    )}
                  </div>
                  <div className="ml-4 text-right">
                    <div className="text-xs text-gray-500">
                      {new Date(workout.started_at).toLocaleDateString([], {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </div>
                    <div className="text-xs text-gray-400">
                      {new Date(workout.started_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => startEdit(workout)}
                    className="flex-1 text-sm bg-blue-50 text-blue-700 px-3 py-1.5 rounded hover:bg-blue-100 transition-colors"
                    aria-label={`Edit ${workout.name}`}
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => deleteWorkout(workout.id)}
                    className="flex-1 text-sm bg-red-50 text-red-700 px-3 py-1.5 rounded hover:bg-red-100 transition-colors"
                    aria-label={`Delete ${workout.name}`}
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

