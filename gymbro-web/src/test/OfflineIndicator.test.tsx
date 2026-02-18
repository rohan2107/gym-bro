import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { OfflineIndicator } from '../components/OfflineIndicator'

describe('OfflineIndicator', () => {

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

  it('shows offline indicator when offline event fires', async () => {
    const { container, rerender } = render(<OfflineIndicator />)
    
    // Initially online (no indicator)
    expect(container.firstChild).toBeNull()
    
    // Simulate going offline by dispatching event
    await act(async () => {
      window.dispatchEvent(new Event('offline'))
    })
    
    // Force re-render to see the update
    rerender(<OfflineIndicator />)
    
    // Should now show indicator
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('hides offline indicator when online event fires', async () => {
    // Start offline
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: false,
    })
    
    const { container, rerender } = render(<OfflineIndicator />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
    
    // Simulate coming back online
    await act(async () => {
      window.dispatchEvent(new Event('online'))
    })
    
    // Force re-render to see the update
    rerender(<OfflineIndicator />)
    
    // Should hide indicator
    expect(container.firstChild).toBeNull()
  })
})
