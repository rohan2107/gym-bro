import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import BottomNav from '../components/BottomNav'

const renderWithRouter = (component: React.ReactElement, initialRoute = '/') => {
  window.history.pushState({}, 'Test page', initialRoute)
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

describe('BottomNav', () => {
  it('renders all navigation buttons', () => {
    renderWithRouter(<BottomNav />)
    
    expect(screen.getByLabelText("Today's overview")).toBeInTheDocument()
    expect(screen.getByLabelText('Meal planning')).toBeInTheDocument()
    expect(screen.getByLabelText('Workout routines')).toBeInTheDocument()
    expect(screen.getByLabelText('User profile')).toBeInTheDocument()
  })

  it('highlights active route', () => {
    renderWithRouter(<BottomNav />, '/')
    
    const todayButton = screen.getByLabelText("Today's overview")
    expect(todayButton).toHaveClass('text-blue-600')
  })

  it('navigates to meals page when meals button clicked', async () => {
    const user = userEvent.setup()
    renderWithRouter(<BottomNav />)
    
    const mealsButton = screen.getByLabelText('Meal planning')
    await user.click(mealsButton)
    
    expect(window.location.pathname).toBe('/meals')
  })

  it('navigates to today page when today button clicked', async () => {
    const user = userEvent.setup()
    renderWithRouter(<BottomNav />, '/meals') // Start on different page
    
    const todayButton = screen.getByLabelText("Today's overview")
    await user.click(todayButton)
    
    expect(window.location.pathname).toBe('/')
  })

  it('navigates to workout page when workout button clicked', async () => {
    const user = userEvent.setup()
    renderWithRouter(<BottomNav />)
    
    const workoutButton = screen.getByLabelText('Workout routines')
    await user.click(workoutButton)
    
    expect(window.location.pathname).toBe('/workout')
  })

  it('navigates to profile page when profile button clicked', async () => {
    const user = userEvent.setup()
    renderWithRouter(<BottomNav />)
    
    const profileButton = screen.getByLabelText('User profile')
    await user.click(profileButton)
    
    expect(window.location.pathname).toBe('/profile')
  })

  it('has proper ARIA labels for accessibility', () => {
    renderWithRouter(<BottomNav />)
    
    const nav = screen.getByRole('navigation', { name: 'Main navigation' })
    expect(nav).toBeInTheDocument()
  })

  it('displays text labels for each button', () => {
    renderWithRouter(<BottomNav />)
    
    expect(screen.getByText('Today')).toBeInTheDocument()
    expect(screen.getByText('Meals')).toBeInTheDocument()
    expect(screen.getByText('Workout')).toBeInTheDocument()
    expect(screen.getByText('Profile')).toBeInTheDocument()
  })
})
