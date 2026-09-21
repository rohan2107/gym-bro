/**
 * Shrinks a photo in the browser before it is uploaded.
 *
 * Vercel rejects a request body over about 4.5MB at its edge (FUNCTION_PAYLOAD_TOO_LARGE),
 * before the API runs, and a phone photo routinely exceeds that. Safari reports the dropped
 * upload as a bare "Load failed". Recognition does not need full resolution, so the photo is
 * scaled down and re-encoded as JPEG first, which typically leaves a few hundred KB.
 *
 * Decoding through the browser also turns HEIC into JPEG where the browser can read it
 * (Safari can), which the server cannot do.
 */

/** Stay under Vercel's ~4.5MB request limit, leaving room for the multipart envelope. */
export const MAX_UPLOAD_BYTES = 4 * 1024 * 1024
const MAX_DIMENSION = 1600
const QUALITIES = [0.85, 0.7, 0.5]

function toJpeg(canvas: HTMLCanvasElement, quality: number): Promise<Blob | null> {
  return new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', quality))
}

export async function prepareImageForUpload(file: File): Promise<File> {
  let bitmap: ImageBitmap
  try {
    // 'from-image' applies the EXIF rotation, so a portrait phone photo is not uploaded sideways.
    bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
  } catch {
    // The browser cannot decode it. A small file can still go up for the server to judge.
    if (file.size <= MAX_UPLOAD_BYTES) return file
    throw new Error('That photo is too large to upload and could not be resized. Try a smaller one.')
  }

  try {
    const scale = Math.min(1, MAX_DIMENSION / Math.max(bitmap.width, bitmap.height))
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(bitmap.width * scale))
    canvas.height = Math.max(1, Math.round(bitmap.height * scale))

    const context = canvas.getContext('2d')
    if (!context) {
      if (file.size <= MAX_UPLOAD_BYTES) return file
      throw new Error('That photo is too large to upload and could not be resized. Try a smaller one.')
    }
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height)

    for (const quality of QUALITIES) {
      const blob = await toJpeg(canvas, quality)
      if (blob && blob.size <= MAX_UPLOAD_BYTES) {
        const name = file.name.replace(/\.[^.]+$/, '') || 'photo'
        return new File([blob], `${name}.jpg`, { type: 'image/jpeg' })
      }
    }
    throw new Error('That photo is still too large after resizing. Try a smaller one.')
  } finally {
    bitmap.close()
  }
}
