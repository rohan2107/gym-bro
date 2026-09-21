/**
 * Tests for public/sw.js.
 *
 * jsdom cannot run a service worker, so the worker's source is executed against fake `caches`,
 * `fetch` and event objects, and its listeners are driven directly.
 *
 * The behaviour under test exists because the worker once served the page cache-first for 24
 * hours: after a deploy a device kept running the old frontend against the new API.
 */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// Vitest runs from the package root (gymbro-web).
const SOURCE = readFileSync(resolve(process.cwd(), 'public/sw.js'), 'utf8')
const ORIGIN = 'https://app.test'

type Listener = (event: unknown) => void

/** A Map-backed stand-in for CacheStorage, keyed by URL. */
function fakeCaches() {
  const stores = new Map<string, Map<string, Response>>()
  const key = (request: { url: string } | string) =>
    typeof request === 'string' ? new URL(request, ORIGIN).href : request.url
  const open = async (name: string) => {
    if (!stores.has(name)) stores.set(name, new Map())
    const store = stores.get(name)!
    return {
      put: async (request: { url: string } | string, response: Response) => {
        store.set(key(request), response)
      },
      addAll: async (urls: string[]) => {
        for (const url of urls) store.set(key(url), new Response(`precached ${url}`))
      },
    }
  }
  return {
    stores,
    open,
    match: async (request: { url: string } | string) => {
      for (const store of stores.values()) {
        const hit = store.get(key(request))
        if (hit) return hit.clone()
      }
      return undefined
    },
    keys: async () => [...stores.keys()],
    delete: async (name: string) => stores.delete(name),
  }
}

function load(fetchImpl: (request: unknown) => Promise<Response>) {
  const listeners: Record<string, Listener> = {}
  const cachesFake = fakeCaches()
  const self = {
    addEventListener: (type: string, listener: Listener) => {
      listeners[type] = listener
    },
    skipWaiting: vi.fn(() => Promise.resolve()),
    clients: { claim: vi.fn(() => Promise.resolve()) },
  }
  const fetchSpy = vi.fn(fetchImpl)
  new Function('self', 'caches', 'fetch', 'console', SOURCE)(
    self,
    cachesFake,
    fetchSpy,
    { log: () => undefined }
  )
  return { listeners, caches: cachesFake, fetch: fetchSpy, self }
}

function request(path: string, init: { navigate?: boolean; method?: string } = {}) {
  return {
    url: new URL(path, ORIGIN).href,
    method: init.method ?? 'GET',
    mode: init.navigate ? 'navigate' : 'cors',
    headers: new Headers(init.navigate ? { accept: 'text/html' } : {}),
  }
}

/** Fire a fetch event; returns the response the worker chose, or null if it did not respond. */
async function dispatch(worker: ReturnType<typeof load>, req: ReturnType<typeof request>) {
  let responded: Promise<Response> | null = null
  worker.listeners.fetch({ request: req, respondWith: (p: Promise<Response>) => (responded = p) })
  return responded ? await responded : null
}

const html = (text: string) => new Response(text, { status: 200, headers: { 'content-type': 'text/html' } })

/**
 * Put a page in the worker's cache, as a visit a moment ago would have. A real cached response
 * carries a fresh Date header, which is exactly what made the old worker treat it as valid for
 * 24 hours; without one it would have looked expired and hidden the bug.
 */
async function cachePage(worker: ReturnType<typeof load>, text: string, path = '/index.html') {
  const cache = await worker.caches.open('gymbro-v3')
  const cached = new Response(text, {
    status: 200,
    headers: { 'content-type': 'text/html', date: new Date().toUTCString() },
  })
  await cache.put(path, cached)
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('navigation (the page itself)', () => {
  // The installed app opens '/', which the old worker precached, and every route it had visited
  // was cached under its own URL too. Both were served for 24 hours after a deploy.
  it.each(['/', '/meals'])(
    'shows the new page after a deploy instead of the cached old one (%s)',
    async (path) => {
      const worker = load(async () => html('new build'))
      await cachePage(worker, 'old build', path)
      await cachePage(worker, 'old build', '/index.html')

      const response = await dispatch(worker, request(path, { navigate: true }))

      expect(await response!.text()).toBe('new build')
      expect(worker.fetch).toHaveBeenCalled()
    }
  )

  it('refreshes the cached shell with what the network returned', async () => {
    const worker = load(async () => html('new build'))
    await cachePage(worker, 'old build')

    await dispatch(worker, request('/meals', { navigate: true }))
    await vi.advanceTimersByTimeAsync(0)

    const cached = await worker.caches.match('/index.html')
    expect(await cached!.text()).toBe('new build')
  })

  it('opens from the cached shell when offline', async () => {
    const worker = load(async () => {
      throw new TypeError('Failed to fetch')
    })
    await cachePage(worker, 'last good build')

    const response = await dispatch(worker, request('/meals', { navigate: true }))

    expect(await response!.text()).toBe('last good build')
  })

  it('shows an offline page when offline with nothing cached', async () => {
    const worker = load(async () => {
      throw new TypeError('Failed to fetch')
    })

    const response = await dispatch(worker, request('/', { navigate: true }))

    expect(await response!.text()).toContain("You're offline")
  })

  it('falls back to the cached shell when the network is too slow, without hanging', async () => {
    const worker = load(() => new Promise(() => undefined)) // never answers
    await cachePage(worker, 'cached build')

    const pending = dispatch(worker, request('/meals', { navigate: true }))
    await vi.advanceTimersByTimeAsync(4000)

    expect(await (await pending)!.text()).toBe('cached build')
  })

  it('still refreshes the cache when a slow response arrives after the fallback', async () => {
    let answer: (response: Response) => void = () => undefined
    const worker = load(() => new Promise<Response>((resolve) => (answer = resolve)))
    await cachePage(worker, 'cached build')

    const pending = dispatch(worker, request('/meals', { navigate: true }))
    await vi.advanceTimersByTimeAsync(4000)
    expect(await (await pending)!.text()).toBe('cached build')

    answer(html('late new build'))
    await vi.advanceTimersByTimeAsync(0)

    const cached = await worker.caches.match('/index.html')
    expect(await cached!.text()).toBe('late new build')
  })

  it('keeps waiting for the network when it is slow and nothing is cached', async () => {
    let answer: (response: Response) => void = () => undefined
    const worker = load(() => new Promise<Response>((resolve) => (answer = resolve)))

    const pending = dispatch(worker, request('/', { navigate: true }))
    await vi.advanceTimersByTimeAsync(10_000)
    answer(html('first ever load'))

    expect(await (await pending)!.text()).toBe('first ever load')
  })

  it('does not cache an error page as the shell', async () => {
    const worker = load(async () => new Response('gateway error', { status: 502 }))
    await cachePage(worker, 'good build')

    await dispatch(worker, request('/meals', { navigate: true }))
    await vi.advanceTimersByTimeAsync(0)

    const cached = await worker.caches.match('/index.html')
    expect(await cached!.text()).toBe('good build')
  })
})

describe('static assets', () => {
  const HASHED = '/assets/index-abc123.js'

  it('serves a hashed asset from the cache without touching the network', async () => {
    const worker = load(async () => new Response('from network'))
    const cache = await worker.caches.open('gymbro-v3')
    await cache.put(HASHED, new Response('from cache'))

    const response = await dispatch(worker, request(HASHED))

    expect(await response!.text()).toBe('from cache')
    expect(worker.fetch).not.toHaveBeenCalled()
  })

  it('never expires a hashed asset, whatever its age', async () => {
    const worker = load(async () => new Response('from network'))
    const cache = await worker.caches.open('gymbro-v3')
    const old = new Response('from cache', { headers: { date: 'Mon, 01 Jan 2024 00:00:00 GMT' } })
    await cache.put(HASHED, old)

    const response = await dispatch(worker, request(HASHED))

    expect(await response!.text()).toBe('from cache')
  })

  it('fetches and caches a hashed asset it has not seen', async () => {
    const worker = load(async () => new Response('fresh asset', { status: 200 }))

    const response = await dispatch(worker, request(HASHED))
    await vi.advanceTimersByTimeAsync(0)

    expect(await response!.text()).toBe('fresh asset')
    expect(await (await worker.caches.match(HASHED))!.text()).toBe('fresh asset')
  })

  it('still expires other cached files after a day', async () => {
    const worker = load(async () => new Response('new icon'))
    const cache = await worker.caches.open('gymbro-v3')
    await cache.put(
      '/icon.svg',
      new Response('old icon', { headers: { date: 'Mon, 01 Jan 2024 00:00:00 GMT' } })
    )

    const response = await dispatch(worker, request('/icon.svg'))

    expect(await response!.text()).toBe('new icon')
  })
})

describe('requests the worker must leave alone or handle as before', () => {
  it('does not intercept auth endpoints, even as navigations', async () => {
    const worker = load(async () => new Response('x'))

    expect(await dispatch(worker, request('/api/auth/google/login', { navigate: true }))).toBeNull()
  })

  it('does not intercept non-GET requests', async () => {
    const worker = load(async () => new Response('x'))

    expect(await dispatch(worker, request('/api/food-logs/from-photo', { method: 'POST' }))).toBeNull()
  })

  it('keeps API requests network-first with a cache fallback, not the page strategy', async () => {
    const worker = load(async () => new Response('{"ok":true}', { status: 200 }))

    const response = await dispatch(worker, request('/api/food-logs/'))

    expect(await response!.text()).toBe('{"ok":true}')
    expect(worker.fetch).toHaveBeenCalledTimes(1)
  })

  it('answers an API request offline with a 503 JSON body when nothing is cached', async () => {
    const worker = load(async () => {
      throw new TypeError('Failed to fetch')
    })

    const response = await dispatch(worker, request('/api/food-logs/'))

    expect(response!.status).toBe(503)
    expect(await response!.json()).toMatchObject({ offline: true })
  })
})

describe('lifecycle', () => {
  it('precaches the shell on install and activates immediately', async () => {
    const worker = load(async () => new Response('x'))
    const waits: Promise<unknown>[] = []

    worker.listeners.install({ waitUntil: (p: Promise<unknown>) => waits.push(p) })
    await Promise.all(waits)

    expect(worker.caches.stores.get('gymbro-v3')?.has(`${ORIGIN}/index.html`)).toBe(true)
    expect(worker.self.skipWaiting).toHaveBeenCalled()
  })

  it('drops the cache left by the old cache-first worker when it activates', async () => {
    const worker = load(async () => new Response('x'))
    await worker.caches.open('gymbro-v2')
    await worker.caches.open('gymbro-v3')
    await worker.caches.open('gymbro-api-v2')
    const waits: Promise<unknown>[] = []

    worker.listeners.activate({ waitUntil: (p: Promise<unknown>) => waits.push(p) })
    await Promise.all(waits)

    expect([...worker.caches.stores.keys()].sort()).toEqual(['gymbro-api-v2', 'gymbro-v3'])
    expect(worker.self.clients.claim).toHaveBeenCalled()
  })
})
