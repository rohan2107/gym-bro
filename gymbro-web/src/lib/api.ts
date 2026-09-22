import { prepareImageForUpload } from './image'

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

export type PhotoNutrition = {
  name: string
  fdc_id: number | null
  calories: number | null
  protein_g: number | null
  carbs_g: number | null
  fat_g: number | null
  /** "100g" for USDA per-100g values, or the estimated portion, e.g. "300g". */
  serving_size: string | null
  confidence: string | null
  /** Where the numbers came from. Absent on older responses, which were USDA per 100g. */
  source?: 'usda' | 'ai_estimate'
  /** The gram basis calories/macros above correspond to. Absent on older responses (100g). */
  portion_g?: number
}

export type PhotoPrediction = {
  label: string
  confidence: number
  nutrition: PhotoNutrition
}

export type PhotoRateLimit = {
  remaining: number
  limit: number
  used_today: number
}

export type PhotoAnalysis = {
  predictions: PhotoPrediction[]
  rate_limit: PhotoRateLimit
  image_info: {
    format: string | null
    size_kb: number | null
  }
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

/**
 * Upload a meal photo for AI analysis.
 *
 * Deliberately does not reuse request(): the browser must set Content-Type
 * itself so the multipart boundary is included.
 */
async function uploadPhoto(file: File): Promise<PhotoAnalysis> {
  const body = new FormData()
  body.append('photo', await prepareImageForUpload(file))

  let res: Response
  try {
    res = await fetch(`${API_BASE}/food-logs/from-photo`, {
      method: 'POST',
      credentials: 'include',
      body,
    })
  } catch {
    // fetch rejects only when no response arrived at all; Safari's own text for that is a
    // bare "Load failed".
    throw new Error("Couldn't reach the server. Check your connection and try again.")
  }

  if (res.status === 401) {
    window.location.href = '/login'
    throw new Error('Authentication required')
  }

  if (!res.ok) {
    throw new Error(await extractErrorMessage(res))
  }

  return (await res.json()) as PhotoAnalysis
}

/** Pull FastAPI's {"detail": "..."} message out of an error response. */
async function extractErrorMessage(res: Response): Promise<string> {
  const raw = await res.text()
  try {
    const parsed = JSON.parse(raw) as { detail?: unknown }
    if (typeof parsed.detail === 'string') return parsed.detail
  } catch {
    // Not JSON - fall through to the raw body.
  }
  return raw || `Request failed (${res.status})`
}

export const api = {
  analyzeMealPhoto: uploadPhoto,
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
