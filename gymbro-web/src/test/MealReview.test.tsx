import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import MealReview from '../components/MealReview'
import { PhotoPrediction } from '../lib/api'

function prediction(overrides: Partial<PhotoPrediction> = {}): PhotoPrediction {
  return {
    label: 'pizza',
    confidence: 0.85,
    nutrition: {
      name: 'Pizza, cheese, regular crust',
      fdc_id: 174987,
      calories: 265,
      protein_g: 11,
      carbs_g: 33,
      fat_g: 10,
      serving_size: '100g',
      confidence: 'high',
      ...(overrides.nutrition || {}),
    },
    ...overrides,
  }
}

describe('MealReview', () => {
  it('pre-fills the form from the first prediction', () => {
    render(
      <MealReview predictions={[prediction()]} onConfirm={vi.fn()} onCancel={vi.fn()} />
    )

    expect(screen.getByLabelText(/description/i)).toHaveValue('Pizza, cheese, regular crust')
    expect(screen.getByLabelText(/calories/i)).toHaveValue(265)
    expect(screen.getByLabelText(/protein/i)).toHaveValue(11)
    expect(screen.getByLabelText(/carbs/i)).toHaveValue(33)
    expect(screen.getByLabelText(/fat/i)).toHaveValue(10)
  })

  it('states that figures are per 100g rather than implying a portion', () => {
    render(
      <MealReview predictions={[prediction()]} onConfirm={vi.fn()} onCancel={vi.fn()} />
    )

    expect(screen.getByText(/per 100g from USDA/i)).toBeInTheDocument()
  })

  it('confirms the meal with edited values, not the predicted ones', () => {
    const onConfirm = vi.fn()
    render(
      <MealReview predictions={[prediction()]} onConfirm={onConfirm} onCancel={vi.fn()} />
    )

    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: 'Two slices of pizza' },
    })
    fireEvent.change(screen.getByLabelText(/calories/i), { target: { value: '530' } })
    fireEvent.click(screen.getByRole('button', { name: /save meal/i }))

    expect(onConfirm).toHaveBeenCalledWith({
      description: 'Two slices of pizza',
      calories: 530,
      protein_g: 11,
      carbs_g: 33,
      fat_g: 10,
    })
  })

  it('treats a cleared macro field as null rather than zero', () => {
    const onConfirm = vi.fn()
    render(
      <MealReview predictions={[prediction()]} onConfirm={onConfirm} onCancel={vi.fn()} />
    )

    fireEvent.change(screen.getByLabelText(/fat/i), { target: { value: '' } })
    fireEvent.click(screen.getByRole('button', { name: /save meal/i }))

    expect(onConfirm).toHaveBeenCalledWith(expect.objectContaining({ fat_g: null }))
  })

  it('hides the food picker when there is only one prediction', () => {
    render(
      <MealReview predictions={[prediction()]} onConfirm={vi.fn()} onCancel={vi.fn()} />
    )

    expect(screen.queryByText(/detected foods/i)).not.toBeInTheDocument()
  })

  it('lets the user switch between detected foods, refilling the form', () => {
    const salad = prediction({
      label: 'salad',
      confidence: 0.72,
      nutrition: {
        name: 'Garden salad',
        fdc_id: 168409,
        calories: 20,
        protein_g: 1.5,
        carbs_g: 4,
        fat_g: 0.2,
        serving_size: '100g',
        confidence: 'high',
      },
    })

    render(
      <MealReview
        predictions={[prediction(), salad]}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    )

    const saladButton = screen.getByRole('button', { name: /salad/i })
    expect(saladButton).toHaveAttribute('aria-pressed', 'false')

    fireEvent.click(saladButton)

    expect(saladButton).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByLabelText(/description/i)).toHaveValue('Garden salad')
    expect(screen.getByLabelText(/calories/i)).toHaveValue(20)
  })

  it('shows each prediction confidence as a percentage', () => {
    render(
      <MealReview
        predictions={[prediction(), prediction({ label: 'salad', confidence: 0.72 })]}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    )

    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getByText('72%')).toBeInTheDocument()
  })

  it('discards without confirming', () => {
    const onCancel = vi.fn()
    const onConfirm = vi.fn()
    render(
      <MealReview predictions={[prediction()]} onConfirm={onConfirm} onCancel={onCancel} />
    )

    fireEvent.click(screen.getByRole('button', { name: /discard/i }))

    expect(onCancel).toHaveBeenCalled()
    expect(onConfirm).not.toHaveBeenCalled()
  })

  it('disables both actions while saving', () => {
    render(
      <MealReview predictions={[prediction()]} onConfirm={vi.fn()} onCancel={vi.fn()} busy />
    )

    expect(screen.getByRole('button', { name: /saving/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /discard/i })).toBeDisabled()
  })

  it('falls back to the raw label when USDA has no name', () => {
    const unnamed = prediction({
      nutrition: {
        name: '',
        fdc_id: null,
        calories: 100,
        protein_g: null,
        carbs_g: null,
        fat_g: null,
        serving_size: null,
        confidence: null,
      },
    })

    render(<MealReview predictions={[unnamed]} onConfirm={vi.fn()} onCancel={vi.fn()} />)

    expect(screen.getByLabelText(/description/i)).toHaveValue('pizza')
  })
})
