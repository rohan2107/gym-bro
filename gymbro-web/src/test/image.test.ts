import { afterEach, describe, expect, it, vi } from 'vitest'
import { MAX_UPLOAD_BYTES, prepareImageForUpload } from '../lib/image'

type FakeCanvas = { width: number; height: number; getContext: () => unknown; toBlob: unknown }

/** Stubs the browser image APIs, which jsdom does not implement. */
function stubBrowser(options: {
  width: number
  height: number
  blobSizes?: number[]
  decodeFails?: boolean
  noContext?: boolean
}) {
  const close = vi.fn()
  const drawImage = vi.fn()
  const sizes = options.blobSizes ?? [200_000]
  let encoded = 0
  const canvases: FakeCanvas[] = []

  vi.stubGlobal(
    'createImageBitmap',
    options.decodeFails
      ? vi.fn().mockRejectedValue(new Error('cannot decode'))
      : vi.fn().mockResolvedValue({ width: options.width, height: options.height, close })
  )

  const realCreate = document.createElement.bind(document)
  vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
    if (tag !== 'canvas') return realCreate(tag)
    const canvas: FakeCanvas = {
      width: 0,
      height: 0,
      getContext: () => (options.noContext ? null : { drawImage }),
      toBlob: (cb: (b: Blob | null) => void) => {
        // Each encode gets the next size; the last one repeats.
        const size = sizes[Math.min(encoded++, sizes.length - 1)]
        const blob = new Blob(['x'])
        Object.defineProperty(blob, 'size', { value: size })
        cb(blob)
      },
    }
    canvases.push(canvas)
    return canvas as unknown as HTMLCanvasElement
  })

  return { close, drawImage, canvases }
}

function photo(sizeBytes: number, name = 'IMG_0001.HEIC', type = 'image/heic'): File {
  const file = new File(['x'], name, { type })
  Object.defineProperty(file, 'size', { value: sizeBytes })
  return file
}

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('prepareImageForUpload', () => {
  it('scales a large photo down so its longest side is 1600px', async () => {
    const { canvases, drawImage } = stubBrowser({ width: 4000, height: 3000 })

    await prepareImageForUpload(photo(9 * 1024 * 1024))

    expect(canvases[0].width).toBe(1600)
    expect(canvases[0].height).toBe(1200)
    expect(drawImage).toHaveBeenCalledWith(expect.anything(), 0, 0, 1600, 1200)
  })

  it('never upscales a small photo', async () => {
    const { canvases } = stubBrowser({ width: 800, height: 600 })

    await prepareImageForUpload(photo(50_000, 'small.jpg', 'image/jpeg'))

    expect([canvases[0].width, canvases[0].height]).toEqual([800, 600])
  })

  it('returns a JPEG file, renaming a HEIC source', async () => {
    stubBrowser({ width: 4000, height: 3000 })

    const result = await prepareImageForUpload(photo(9 * 1024 * 1024))

    expect(result.type).toBe('image/jpeg')
    expect(result.name).toBe('IMG_0001.jpg')
  })

  it('applies the EXIF orientation when decoding', async () => {
    stubBrowser({ width: 4000, height: 3000 })

    await prepareImageForUpload(photo(9 * 1024 * 1024))

    expect(createImageBitmap).toHaveBeenCalledWith(expect.anything(), {
      imageOrientation: 'from-image',
    })
  })

  it('lowers the quality when the first encoding is still too large', async () => {
    stubBrowser({ width: 4000, height: 3000, blobSizes: [MAX_UPLOAD_BYTES + 1, 500_000] })

    const result = await prepareImageForUpload(photo(9 * 1024 * 1024))

    expect(result.type).toBe('image/jpeg')
  })

  it('fails with a clear message when no quality fits the limit', async () => {
    stubBrowser({ width: 4000, height: 3000, blobSizes: [MAX_UPLOAD_BYTES + 1] })

    await expect(prepareImageForUpload(photo(9 * 1024 * 1024))).rejects.toThrow(
      /still too large/i
    )
  })

  it('releases the decoded bitmap, on success and on failure', async () => {
    const ok = stubBrowser({ width: 800, height: 600 })
    await prepareImageForUpload(photo(50_000, 'a.jpg', 'image/jpeg'))
    expect(ok.close).toHaveBeenCalledTimes(1)

    vi.restoreAllMocks()
    const bad = stubBrowser({ width: 800, height: 600, blobSizes: [MAX_UPLOAD_BYTES + 1] })
    await expect(prepareImageForUpload(photo(9 * 1024 * 1024))).rejects.toThrow()
    expect(bad.close).toHaveBeenCalledTimes(1)
  })

  describe('when the browser cannot decode the file', () => {
    it('lets a small file through for the server to judge', async () => {
      stubBrowser({ width: 0, height: 0, decodeFails: true })
      const file = photo(1_000_000)

      expect(await prepareImageForUpload(file)).toBe(file)
    })

    it('refuses a file over the upload limit instead of sending it', async () => {
      stubBrowser({ width: 0, height: 0, decodeFails: true })

      await expect(prepareImageForUpload(photo(MAX_UPLOAD_BYTES + 1))).rejects.toThrow(
        /could not be resized/i
      )
    })
  })

  it('falls back to the original when no 2D context is available and it is small enough', async () => {
    stubBrowser({ width: 800, height: 600, noContext: true })
    const file = photo(1_000_000, 'a.jpg', 'image/jpeg')

    expect(await prepareImageForUpload(file)).toBe(file)
  })
})
