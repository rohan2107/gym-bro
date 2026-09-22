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
      portion_g: 100,
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

  it('says when the figures are scaled to an estimated portion', () => {
    render(
      <MealReview
        predictions={[prediction({ nutrition: { serving_size: '300g', portion_g: 300, source: 'usda' } as never })]}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    )

    expect(screen.getByTestId('basis-note')).toHaveTextContent(
      /estimated for about 300g, from USDA values scaled to the portion/i
    )
    expect(screen.queryByText(/per 100g from USDA/i)).not.toBeInTheDocument()
  })

  it('warns that an AI estimate is not from a nutrition database', () => {
    render(
      <MealReview
        predictions={[
          prediction({ nutrition: { serving_size: '300g', portion_g: 300, source: 'ai_estimate', confidence: 'low' } as never }),
        ]}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    )

    const note = screen.getByTestId('basis-note')
    expect(note).toHaveTextContent(/AI estimate for about 300g/i)
    expect(note).toHaveTextContent(/not from a nutrition database/i)
    expect(note).toHaveTextContent(/check these numbers/i)
  })

  it('updates the note when the user switches to a food with a different basis', () => {
    const estimated = prediction({
      label: 'rice',
      nutrition: { serving_size: '150g', portion_g: 150, source: 'ai_estimate' } as never,
    })

    render(
      <MealReview
        predictions={[prediction(), estimated]}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    )
    expect(screen.getByTestId('basis-note')).toHaveTextContent(/per 100g from USDA/i)

    fireEvent.click(screen.getByRole('button', { name: /rice/i }))

    expect(screen.getByTestId('basis-note')).toHaveTextContent(/AI estimate for about 150g/i)
  })

  it('pre-fills the portion from the prediction', () => {
    render(
      <MealReview
        predictions={[prediction({ nutrition: { portion_g: 250 } as never })]}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    )

    expect(screen.getByLabelText(/portion/i)).toHaveValue(250)
  })

  it('defaults the portion to 100g when the prediction has none', () => {
    render(
      <MealReview
        predictions={[prediction({ nutrition: { portion_g: undefined } as never })]}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    )

    expect(screen.getByLabelText(/portion/i)).toHaveValue(100)
  })

  it('recalculates every macro when the portion changes, scaling from the original basis', () => {
    render(
      <MealReview predictions={[prediction()]} onConfirm={vi.fn()} onCancel={vi.fn()} />
    )

    fireEvent.change(screen.getByLabelText(/portion/i), { target: { value: '250' } })

    // Basis: 265 kcal / 11g protein / 33g carbs / 10g fat at 100g.
    expect(screen.getByLabelText(/calories/i)).toHaveValue(663)
    expect(screen.getByLabelText(/protein/i)).toHaveValue(27.5)
    expect(screen.getByLabelText(/carbs/i)).toHaveValue(82.5)
    expect(screen.getByLabelText(/fat/i)).toHaveValue(25)
  })

  it('re-derives from the original basis each time, so edits do not compound rounding error', () => {
    render(
      <MealReview predictions={[prediction()]} onConfirm={vi.fn()} onCancel={vi.fn()} />
    )

    const portionField = screen.getByLabelText(/portion/i)
    fireEvent.change(portionField, { target: { value: '250' } })
    fireEvent.change(portionField, { target: { value: '400' } })

    expect(screen.getByLabelText(/calories/i)).toHaveValue(Math.round(265 * 4))
  })

  it('updates the basis note as the portion is edited', () => {
    render(
      <MealReview predictions={[prediction()]} onConfirm={vi.fn()} onCancel={vi.fn()} />
    )

    fireEvent.change(screen.getByLabelText(/portion/i), { target: { value: '180' } })

    expect(screen.getByTestId('basis-note')).toHaveTextContent(
      /estimated for about 180g, from usda values scaled to the portion/i
    )
  })

  it('resets the portion when the user switches to a different detected food', () => {
    const salad = prediction({
      label: 'salad',
      nutrition: { calories: 20, portion_g: 300 } as never,
    })

    render(
      <MealReview predictions={[prediction(), salad]} onConfirm={vi.fn()} onCancel={vi.fn()} />
    )

    fireEvent.click(screen.getByRole('button', { name: /salad/i }))

    expect(screen.getByLabelText(/portion/i)).toHaveValue(300)
  })

  it('leaves the macros as they are while the portion field is being cleared', () => {
    render(
      <MealReview predictions={[prediction()]} onConfirm={vi.fn()} onCancel={vi.fn()} />
    )

    fireEvent.change(screen.getByLabelText(/portion/i), { target: { value: '' } })

    expect(screen.getByLabelText(/portion/i)).toHaveValue(null)
    expect(screen.getByLabelText(/calories/i)).toHaveValue(265)
  })

  it('does not send the portion to onConfirm, only description and macros', () => {
    const onConfirm = vi.fn()
    render(
      <MealReview predictions={[prediction()]} onConfirm={onConfirm} onCancel={vi.fn()} />
    )

    fireEvent.change(screen.getByLabelText(/portion/i), { target: { value: '250' } })
    fireEvent.click(screen.getByRole('button', { name: /save meal/i }))

    expect(onConfirm).toHaveBeenCalledWith(
      expect.not.objectContaining({ portion_g: expect.anything() })
    )
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
