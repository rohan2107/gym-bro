export type DailyCheckIn = {
  id: number
  user_id: number
  checkin_date: string
  weight: number | null
  trained: boolean
  steps: number | null
  protein_met: boolean
  notes: string | null
}

export type FoodLog = {
  id: number
  description: string | null
  calories: number | null
  protein_g: number | null
  carbs_g: number | null
  fat_g: number | null
  logged_at: string
}

export type Workout = {
  id: number
  name: string
  note: string | null
  started_at: string
}

// API_BASE: In development uses Vite proxy (/api -> localhost:8000)
// In production, uses environment variable (ngrok tunnel or deployed backend)
const API_BASE = import.meta.env.VITE_API_URL || '/api'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include', // Send cookies for authentication
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  })

  // Handle authentication errors
  if (res.status === 401) {
    // Redirect to login page
    window.location.href = '/login'
    throw new Error('Authentication required')
  }

  if (!res.ok) {
    const message = await res.text()
    throw new Error(message || `Request failed (${res.status})`)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export const api = {
  getTodayCheckIn: () => request<DailyCheckIn>('/daily-checkins/today'),
  getCheckInByDate: (dateISO: string) => request<DailyCheckIn>(`/daily-checkins/${dateISO}`),
  upsertCheckIn: (dateISO: string, data: Partial<Omit<DailyCheckIn, 'id' | 'user_id' | 'checkin_date'>>) =>
    request<DailyCheckIn>(`/daily-checkins/${dateISO}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  listFoodLogs: () => request<FoodLog[]>('/food-logs/'),
  createFoodLog: (data: {
    description: string
    calories?: number | null
    protein_g?: number | null
    carbs_g?: number | null
    fat_g?: number | null
  }) =>
    request<FoodLog>('/food-logs/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateFoodLog: (id: number, data: {
    description: string
    calories?: number | null
    protein_g?: number | null
    carbs_g?: number | null
    fat_g?: number | null
  }) =>
    request<FoodLog>(`/food-logs/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteFoodLog: (id: number) =>
    request<void>(`/food-logs/${id}`, {
      method: 'DELETE',
    }),
  listWorkouts: () => request<Workout[]>('/workouts'),
  createWorkout: (data: { name: string; note?: string | null }) =>
    request<Workout>('/workouts', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateWorkout: (id: number, data: { name: string; note?: string | null }) =>
    request<Workout>(`/workouts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteWorkout: (id: number) =>
    request<void>(`/workouts/${id}`, {
      method: 'DELETE',
    }),
}
