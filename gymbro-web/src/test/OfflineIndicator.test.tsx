import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { OfflineIndicator } from '../components/OfflineIndicator'

describe('OfflineIndicator', () => {
  let onlineSetter: ((value: boolean) => void) | undefined

  beforeEach(() => {
    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      configurable: true,
      value: true,
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('does not render when online', () => {
    const { container } = render(<OfflineIndicator />)
    expect(container.firstChild).toBeNull()
  })

  it('renders offline message when offline', () => {
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    })
    
    render(<OfflineIndicator />)
    
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText(/Offline/)).toBeInTheDocument()
    expect(screen.getByText(/Changes will sync when you're back online/)).toBeInTheDocument()
  })

  it('has proper ARIA attributes for accessibility', () => {
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    })
    
    render(<OfflineIndicator />)
    
    const alert = screen.getByRole('alert')
    expect(alert).toHaveAttribute('aria-live', 'assertive')
  })

  it('displays in prominent orange color when offline', () => {
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    })
    
    render(<OfflineIndicator />)
    
    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('bg-orange-500')
  })

  it('is positioned at the top of the viewport', () => {
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    })
    
    render(<OfflineIndicator />)
    
    const alert = screen.getByRole('alert')
    expect(alert).toHaveClass('fixed', 'top-0')
  })
})
