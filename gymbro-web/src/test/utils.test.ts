import { describe, it, expect } from 'vitest'
import { toDateInputValue, formatRelativeDateTime, handleRequestError } from '../lib/utils'

describe('toDateInputValue', () => {
  it('formats date to YYYY-MM-DD format', () => {
    const date = new Date('2026-02-18T12:00:00Z')
    const result = toDateInputValue(date)
    expect(result).toBe('2026-02-18')
  })

  it('pads single digit months and days with zeros', () => {
    const date = new Date('2026-03-05T12:00:00Z')
    const result = toDateInputValue(date)
    expect(result).toBe('2026-03-05')
  })

  it('uses current date when no argument provided', () => {
    const result = toDateInputValue()
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})

describe('formatRelativeDateTime', () => {
  it('returns "Invalid date" for invalid date string', () => {
    const result = formatRelativeDateTime('not-a-date')
    expect(result).toBe('Invalid date')
  })

  it('formats date with time', () => {
    const dateString = '2025-12-25T15:30:00Z'
    const result = formatRelativeDateTime(dateString)
    expect(result).toContain('at')
  })

  it('formats future dates correctly', () => {
    const futureDate = new Date()
    futureDate.setFullYear(futureDate.getFullYear() + 1)
    const result = formatRelativeDateTime(futureDate.toISOString())
    expect(result).toContain('at')
  })
})

describe('handleRequestError', () => {
  it('returns offline message when navigator.onLine is false', () => {
    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    })
    
    const result = handleRequestError(new Error('Network error'))
    expect(result).toContain('internet connection')
    
    // Restore
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true,
    })
  })

  it('returns error message for Error instances', () => {
    const error = new Error('Custom error message')
    const result = handleRequestError(error)
    expect(result).toBe('Custom error message')
  })

  it('returns generic message for unknown errors', () => {
    const result = handleRequestError('string error')
    expect(result).toBe('An unexpected error occurred. Please try again.')
  })

  it('returns generic message for null errors', () => {
    const result = handleRequestError(null)
    expect(result).toBe('An unexpected error occurred. Please try again.')
  })
})
