import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from './App'

const machineOptions = [
  { value: 'HSG_3kW_150mm_VSX_NC30E', label: 'HSG 3 кВт, линза 150 мм, голова VSX NC30E' },
]
const materialOptions = [
  { value: 'stainless', label: 'Нержавеющая сталь' },
  { value: 'carbon', label: 'Углеродистая сталь' },
]
const gasOptions = [
  { value: 'N2', label: 'Азот N2' },
  { value: 'air', label: 'Воздух' },
]
const defectOptions = [
  { value: 'burr', label: 'Грат снизу' },
]

afterEach(() => {
  vi.restoreAllMocks()
})

function setupFetchMock() {
  return vi.spyOn(global, 'fetch').mockImplementation(async (input, init) => {
    const url = String(input)

    if (url.endsWith('/dictionaries/machines')) {
      return new Response(JSON.stringify(machineOptions), { status: 200 })
    }
    if (url.endsWith('/dictionaries/materials')) {
      return new Response(JSON.stringify(materialOptions), { status: 200 })
    }
    if (url.endsWith('/dictionaries/gases')) {
      return new Response(JSON.stringify(gasOptions), { status: 200 })
    }
    if (url.endsWith('/dictionaries/defects')) {
      return new Response(JSON.stringify(defectOptions), { status: 200 })
    }
    if (url.endsWith('/rules')) {
      return new Response(JSON.stringify([]), { status: 200 })
    }

    if (url.includes('/dict/thicknesses?')) {
      if (url.includes('gas_branch=N2')) {
        return new Response(
          JSON.stringify([
            { value: 1, label: '1 мм' },
            { value: 2, label: '2 мм' },
          ]),
          { status: 200 },
        )
      }
      if (url.includes('gas_branch=air')) {
        return new Response(
          JSON.stringify([
            { value: 4, label: '4 мм' },
            { value: 5, label: '5 мм' },
          ]),
          { status: 200 },
        )
      }
      return new Response(JSON.stringify([]), { status: 200 })
    }

    if (url.endsWith('/sessions') && init?.method === 'POST') {
      const body = JSON.parse(String(init.body))
      return new Response(
        JSON.stringify({
          id: 10,
          machine_name: body.machine_name,
          material_group: body.material_group,
          thickness_mm: body.thickness_mm,
          gas_branch: body.gas_branch,
          created_at: '2026-04-27T00:00:00Z',
        }),
        { status: 201 },
      )
    }

    return new Response('not found', { status: 404 })
  })
}

describe('session thickness selection', () => {
  it('submits only selectable thickness values', async () => {
    const fetchMock = setupFetchMock()
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Сессии' }))

    const thicknessSelect = await screen.findByLabelText('Толщина (мм)')
    fireEvent.change(thicknessSelect, { target: { value: '2' } })
    fireEvent.change(thicknessSelect, { target: { value: '2.5' } })

    fireEvent.click(screen.getByRole('button', { name: 'Создать сессию' }))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/sessions',
        expect.objectContaining({ method: 'POST' }),
      )
    })

    const call = fetchMock.mock.calls.find(
      ([url, init]) => String(url).endsWith('/sessions') && init?.method === 'POST',
    )
    const payload = JSON.parse(String(call?.[1]?.body))
    expect(payload.thickness_mm).toBe(2)
  })

  it('recalculates thickness when gas changes and previous value is unavailable', async () => {
    setupFetchMock()
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Сессии' }))

    const thicknessSelect = (await screen.findByLabelText('Толщина (мм)')) as HTMLSelectElement
    fireEvent.change(thicknessSelect, { target: { value: '2' } })
    expect(thicknessSelect.value).toBe('2')

    const gasSelect = screen.getByLabelText('Газ')
    fireEvent.change(gasSelect, { target: { value: 'air' } })

    await waitFor(() => {
      expect((screen.getByLabelText('Толщина (мм)') as HTMLSelectElement).value).toBe('4')
    })
  })
})
