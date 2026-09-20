import { useRef, useState } from 'react'
import { PhotoRateLimit } from '../lib/api'

/**
 * Meal photo capture.
 *
 * Uses a file input with capture="environment" rather than getUserMedia: it
 * opens the native camera on iOS Safari and Android Chrome, falls back to the
 * file picker on desktop, and needs no camera permission of its own — so the
 * "permission denied" path that a getUserMedia implementation has to handle
 * does not exist here.
 */
export default function PhotoCapture({
  onSelect,
  busy,
  rateLimit,
  disabled,
}: {
  onSelect: (file: File) => void
  busy?: boolean
  rateLimit?: PhotoRateLimit | null
  disabled?: boolean
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [localError, setLocalError] = useState<string | null>(null)

  const quotaExhausted = rateLimit ? rateLimit.remaining <= 0 : false
  const isDisabled = busy || disabled || quotaExhausted

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalError(null)
    const file = e.target.files?.[0]

    // Reset so picking the same file twice still fires a change event.
    e.target.value = ''

    if (!file) return

    // The backend cannot decode HEIC/HEIF (macOS Photos exports these; iOS Safari
    // normally converts to JPEG before upload). Fail here with an instruction the
    // user can act on, rather than after uploading the whole file.
    if (/^image\/hei[cf]$/i.test(file.type) || /\.hei[cf]$/i.test(file.name)) {
      setLocalError(
        'HEIC photos are not supported. Please use a JPEG or PNG. On a Mac, export from Photos as JPEG.'
      )
      return
    }

    if (!file.type.startsWith('image/')) {
      setLocalError('That file is not an image. Please choose a photo.')
      return
    }

    // Matches the backend's 10MB cap, so an oversized file fails instantly
    // instead of after a long upload.
    if (file.size > 10 * 1024 * 1024) {
      setLocalError('That photo is larger than 10MB. Try a smaller one.')
      return
    }

    onSelect(file)
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleChange}
        className="hidden"
        data-testid="photo-input"
        aria-hidden="true"
        tabIndex={-1}
      />

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={isDisabled}
        className="w-full bg-green-600 text-white px-4 py-2 rounded font-medium hover:bg-green-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors"
      >
        {busy ? 'Analysing photo…' : '📸 Log from photo'}
      </button>

      {rateLimit && (
        <p className="text-xs text-gray-500 mt-2" aria-live="polite">
          {quotaExhausted
            ? 'Daily photo limit reached. Log this one manually and try again tomorrow.'
            : `${rateLimit.remaining} of ${rateLimit.limit} photos left today.`}
        </p>
      )}

      {localError && (
        <div
          className="rounded bg-red-50 border border-red-200 text-red-700 px-3 py-2 text-sm mt-2"
          role="alert"
        >
          {localError}
        </div>
      )}
    </div>
  )
}
