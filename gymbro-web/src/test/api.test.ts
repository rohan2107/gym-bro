import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from '../lib/api'
import * as image from '../lib/image'

const original = new File(['original'], 'meal.heic', { type: 'image/heic' })
const resized = new File(['resized'], 'meal.jpg', { type: 'image/jpeg' })

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('analyzeMealPhoto', () => {
  it('uploads the resized photo, not the original', async () => {
    vi.spyOn(image, 'prepareImageForUpload').mockResolvedValue(resized)
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ predictions: [] }), { status: 200 })
    )
    vi.stubGlobal('fetch', fetchMock)

    await api.analyzeMealPhoto(original)

    const body = fetchMock.mock.calls[0][1].body as FormData
    expect((body.get('photo') as File).name).toBe('meal.jpg')
  })

  it("explains a dropped connection instead of showing the browser's own text", async () => {
    vi.spyOn(image, 'prepareImageForUpload').mockResolvedValue(resized)
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Load failed')))

    await expect(api.analyzeMealPhoto(original)).rejects.toThrow(/couldn't reach the server/i)
  })

  it('still surfaces the API error message for an error response', async () => {
    vi.spyOn(image, 'prepareImageForUpload').mockResolvedValue(resized)
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: 'Daily photo limit reached' }), { status: 429 })
      )
    )

    await expect(api.analyzeMealPhoto(original)).rejects.toThrow('Daily photo limit reached')
  })
})

describe('request helper', () => {
  function respond(response: Response) {
    const fetchMock = vi.fn().mockResolvedValue(response)
    vi.stubGlobal('fetch', fetchMock)
    return fetchMock
  }

  it('sends cookies and a JSON content type', async () => {
    const fetchMock = respond(new Response('[]', { status: 200 }))

    await api.listWorkouts()

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/workouts')
    expect(init.credentials).toBe('include')
    expect(init.headers['Content-Type']).toBe('application/json')
  })

  it('returns undefined for a 204 response', async () => {
    respond(new Response(null, { status: 204 }))

    expect(await api.deleteWorkout(1)).toBeUndefined()
  })

  it('sends the user to the login page on a 401', async () => {
    respond(new Response('', { status: 401 }))
    const location = { href: '' }
    vi.stubGlobal('location', location)

    await expect(api.listWorkouts()).rejects.toThrow('Authentication required')
    expect(location.href).toBe('/login')
  })

  it('throws the response text for other errors, or a fallback when it is empty', async () => {
    respond(new Response('Workout not found', { status: 404 }))
    await expect(api.listWorkouts()).rejects.toThrow('Workout not found')

    respond(new Response('', { status: 500 }))
    await expect(api.listWorkouts()).rejects.toThrow('Request failed (500)')
  })
})

describe('endpoint wrappers', () => {
  const food = { description: 'Oats', calories: 300 }
  const workout = { name: 'Push' }
  const checkIn = { weight: 80 }

  const cases: Array<[string, () => Promise<unknown>, string, string, unknown?]> = [
    ['getTodayCheckIn', () => api.getTodayCheckIn(), 'GET', '/api/daily-checkins/today'],
    ['getCheckInByDate', () => api.getCheckInByDate('2026-09-21'), 'GET', '/api/daily-checkins/2026-09-21'],
    ['upsertCheckIn', () => api.upsertCheckIn('2026-09-21', checkIn), 'PUT', '/api/daily-checkins/2026-09-21', checkIn],
    ['listFoodLogs', () => api.listFoodLogs(), 'GET', '/api/food-logs/'],
    ['createFoodLog', () => api.createFoodLog(food), 'POST', '/api/food-logs/', food],
    ['updateFoodLog', () => api.updateFoodLog(7, food), 'PUT', '/api/food-logs/7', food],
    ['deleteFoodLog', () => api.deleteFoodLog(7), 'DELETE', '/api/food-logs/7'],
    ['listWorkouts', () => api.listWorkouts(), 'GET', '/api/workouts'],
    ['createWorkout', () => api.createWorkout(workout), 'POST', '/api/workouts', workout],
    ['updateWorkout', () => api.updateWorkout(3, workout), 'PUT', '/api/workouts/3', workout],
    ['deleteWorkout', () => api.deleteWorkout(3), 'DELETE', '/api/workouts/3'],
  ]

  it.each(cases)('%s calls the right endpoint', async (_name, call, method, url, body) => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await call()

    const [requestedUrl, init] = fetchMock.mock.calls[0]
    expect(requestedUrl).toBe(url)
    expect(init.method ?? 'GET').toBe(method)
    if (body !== undefined) expect(JSON.parse(init.body)).toEqual(body)
  })
})
