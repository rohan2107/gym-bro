import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import PhotoCapture from '../components/PhotoCapture'

function imageFile(name = 'meal.jpg', type = 'image/jpeg', sizeBytes = 1024): File {
  const file = new File(['x'], name, { type })
  // File size is read-only, so it is defined explicitly for the size-cap test.
  Object.defineProperty(file, 'size', { value: sizeBytes })
  return file
}

function selectFile(file: File) {
  const input = screen.getByTestId('photo-input') as HTMLInputElement
  fireEvent.change(input, { target: { files: [file] } })
}

describe('PhotoCapture', () => {
  it('renders the capture button', () => {
    render(<PhotoCapture onSelect={vi.fn()} />)
    expect(screen.getByRole('button', { name: /log from photo/i })).toBeInTheDocument()
  })

  it('tells the user the photo is sent to Google and not stored', () => {
    render(<PhotoCapture onSelect={vi.fn()} />)
    expect(screen.getByText(/sent to Google.*does not store/i)).toBeInTheDocument()
  })

  it('opens the native camera on mobile via a capture-enabled file input', () => {
    render(<PhotoCapture onSelect={vi.fn()} />)
    const input = screen.getByTestId('photo-input')

    expect(input).toHaveAttribute('accept', 'image/*')
    expect(input).toHaveAttribute('capture', 'environment')
  })

  it('passes a chosen image to onSelect', () => {
    const onSelect = vi.fn()
    render(<PhotoCapture onSelect={onSelect} />)

    const file = imageFile()
    selectFile(file)

    expect(onSelect).toHaveBeenCalledWith(file)
  })

  it('rejects non-image files without calling onSelect', () => {
    const onSelect = vi.fn()
    render(<PhotoCapture onSelect={onSelect} />)

    selectFile(imageFile('notes.pdf', 'application/pdf'))

    expect(onSelect).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toHaveTextContent(/not an image/i)
  })

  it.each([
    ['photo.heic', 'image/heic'],
    ['photo.HEIC', 'image/heic'],
    ['photo.heif', 'image/heif'],
    // Some browsers report an empty type for HEIC; the extension still catches it.
    ['IMG_0001.heic', ''],
  ])('rejects HEIC/HEIF (%s) with an actionable message', (name, type) => {
    const onSelect = vi.fn()
    render(<PhotoCapture onSelect={onSelect} />)

    selectFile(imageFile(name, type))

    expect(onSelect).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toHaveTextContent(/HEIC photos are not supported/i)
    expect(screen.getByRole('alert')).toHaveTextContent(/JPEG/i)
  })

  it('accepts a large phone photo, because it is shrunk before upload', () => {
    const onSelect = vi.fn()
    render(<PhotoCapture onSelect={onSelect} />)

    selectFile(imageFile('iphone.jpg', 'image/jpeg', 12 * 1024 * 1024))

    expect(onSelect).toHaveBeenCalled()
  })

  it('rejects a file too large to decode safely', () => {
    const onSelect = vi.fn()
    render(<PhotoCapture onSelect={onSelect} />)

    selectFile(imageFile('huge.jpg', 'image/jpeg', 31 * 1024 * 1024))

    expect(onSelect).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toHaveTextContent(/larger than 30MB/i)
  })

  it('shows a busy label and disables the button while analysing', () => {
    render(<PhotoCapture onSelect={vi.fn()} busy />)

    const button = screen.getByRole('button', { name: /analysing photo/i })
    expect(button).toBeDisabled()
  })

  it('shows remaining quota', () => {
    render(
      <PhotoCapture
        onSelect={vi.fn()}
        rateLimit={{ remaining: 28, limit: 30, used_today: 2 }}
      />
    )

    expect(screen.getByText(/28 of 30 photos left today/i)).toBeInTheDocument()
  })

  it('disables capture and points to manual entry when quota is exhausted', () => {
    render(
      <PhotoCapture
        onSelect={vi.fn()}
        rateLimit={{ remaining: 0, limit: 30, used_today: 30 }}
      />
    )

    expect(screen.getByRole('button', { name: /log from photo/i })).toBeDisabled()
    expect(screen.getByText(/log this one manually/i)).toBeInTheDocument()
  })

  it('allows re-selecting the same file twice', () => {
    const onSelect = vi.fn()
    render(<PhotoCapture onSelect={onSelect} />)

    const input = screen.getByTestId('photo-input') as HTMLInputElement
    const file = imageFile()

    fireEvent.change(input, { target: { files: [file] } })
    // The component clears the input value so a repeat pick still fires change.
    expect(input.value).toBe('')

    fireEvent.change(input, { target: { files: [file] } })
    expect(onSelect).toHaveBeenCalledTimes(2)
  })
})
