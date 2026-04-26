import { FormEvent, useMemo, useState } from 'react'

type CutSessionCreate = {
  machine_name: string
  material_group: string
  thickness_mm: number
  gas_branch: string
}

type ModeVector = {
  power: number
  speed: number
  frequency: number
  pressure: number
  focus: number
  height: number
  duty_cycle: number
  nozzle: number
}

type CutIteration = {
  id: number
  session_id: number
  step_number: number
  defect_code: string
  severity_level: number
  power_before: number
  speed_before: number
  frequency_before: number
  pressure_before: number
  focus_before: number
  height_before: number
  duty_cycle_before: number
  nozzle_before: number
  power_after: number
  speed_after: number
  frequency_after: number
  pressure_after: number
  focus_after: number
  height_after: number
  duty_cycle_after: number
  nozzle_after: number
  created_at: string
}

type CutSession = {
  id: number
  machine_name: string
  material_group: string
  thickness_mm: number
  gas_branch: string
  created_at: string
  iterations: CutIteration[]
}

type ApiError = {
  detail?: string
}

type Recommendation = {
  power_after: number
  speed_after: number
  frequency_after: number
  pressure_after: number
  focus_after: number
  height_after: number
  duty_cycle_after: number
  nozzle_after: number
}

const API_BASE = import.meta.env.VITE_API_BASE_PATH ?? '/api'

const DEFAULT_MODE: ModeVector = {
  power: 0,
  speed: 0,
  frequency: 0,
  pressure: 0,
  focus: 0,
  height: 0,
  duty_cycle: 0,
  nozzle: 0,
}

export default function App() {
  const [sessionForm, setSessionForm] = useState<CutSessionCreate>({
    machine_name: '',
    material_group: '',
    thickness_mm: 1,
    gas_branch: '',
  })
  const [sessionIdInput, setSessionIdInput] = useState('')
  const [currentSession, setCurrentSession] = useState<CutSession | null>(null)

  const [stepNumber, setStepNumber] = useState(1)
  const [defectCode, setDefectCode] = useState('burr')
  const [severityLevel, setSeverityLevel] = useState(1)
  const [beforeMode, setBeforeMode] = useState<ModeVector>(DEFAULT_MODE)
  const [afterMode, setAfterMode] = useState<ModeVector>(DEFAULT_MODE)

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)

  const orderedIterations = useMemo(() => {
    if (!currentSession) return []
    return [...currentSession.iterations].sort((a, b) => a.step_number - b.step_number)
  }, [currentSession])

  async function readError(response: Response): Promise<string> {
    try {
      const payload = (await response.json()) as ApiError
      if (payload.detail) return payload.detail
    } catch {
      // ignore parse errors
    }
    return `Request failed with status ${response.status}`
  }

  async function createSession(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsLoading(true)
    setError(null)
    setMessage(null)

    try {
      const response = await fetch(`${API_BASE}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sessionForm),
      })

      if (!response.ok) {
        throw new Error(await readError(response))
      }

      const created = (await response.json()) as Omit<CutSession, 'iterations'>
      const hydrated: CutSession = { ...created, iterations: [] }
      setCurrentSession(hydrated)
      setSessionIdInput(String(created.id))
      setStepNumber(1)
      setRecommendation(null)
      setMessage(`Session #${created.id} created.`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create session')
    } finally {
      setIsLoading(false)
    }
  }

  async function loadSession(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsLoading(true)
    setError(null)
    setMessage(null)

    try {
      const response = await fetch(`${API_BASE}/sessions/${sessionIdInput}`)
      if (!response.ok) {
        throw new Error(await readError(response))
      }

      const data = (await response.json()) as CutSession
      setCurrentSession(data)
      const nextStep = data.iterations.length
        ? Math.max(...data.iterations.map((item) => item.step_number)) + 1
        : 1
      setStepNumber(nextStep)
      setRecommendation(null)
      setMessage(`Session #${data.id} loaded.`)
    } catch (e) {
      setCurrentSession(null)
      setError(e instanceof Error ? e.message : 'Failed to load session')
    } finally {
      setIsLoading(false)
    }
  }

  async function getRecommendation() {
    if (!currentSession) return

    setIsLoading(true)
    setError(null)
    setMessage(null)

    try {
      const response = await fetch(`${API_BASE}/sessions/${currentSession.id}/recommend`, {
        method: 'POST',
      })

      if (!response.ok) {
        if (response.status === 400) {
          const responseError = await readError(response)
          if (responseError.includes('session has no iterations')) {
            throw new Error('Cannot get recommendation: session has no iterations yet.')
          }
          throw new Error(`Cannot get recommendation: ${responseError}`)
        }

        if (response.status === 404) {
          throw new Error('Cannot get recommendation: session not found (404).')
        }

        if (response.status === 422) {
          throw new Error('Cannot get recommendation: invalid request data (422).')
        }

        throw new Error(await readError(response))
      }

      const data = (await response.json()) as Recommendation
      setRecommendation(data)
      setMessage('Recommendation loaded.')
    } catch (e) {
      if (e instanceof TypeError) {
        setError('Network error while requesting recommendation. Please check your connection.')
      } else {
        setError(e instanceof Error ? e.message : 'Failed to get recommendation')
      }
      setRecommendation(null)
    } finally {
      setIsLoading(false)
    }
  }

  async function addIteration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!currentSession) return

    setIsLoading(true)
    setError(null)
    setMessage(null)

    try {
      const payload = {
        step_number: stepNumber,
        defect_code: defectCode,
        severity_level: severityLevel,
        power_before: beforeMode.power,
        speed_before: beforeMode.speed,
        frequency_before: beforeMode.frequency,
        pressure_before: beforeMode.pressure,
        focus_before: beforeMode.focus,
        height_before: beforeMode.height,
        duty_cycle_before: beforeMode.duty_cycle,
        nozzle_before: beforeMode.nozzle,
        power_after: afterMode.power,
        speed_after: afterMode.speed,
        frequency_after: afterMode.frequency,
        pressure_after: afterMode.pressure,
        focus_after: afterMode.focus,
        height_after: afterMode.height,
        duty_cycle_after: afterMode.duty_cycle,
        nozzle_after: afterMode.nozzle,
      }

      const response = await fetch(`${API_BASE}/sessions/${currentSession.id}/iterations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error(await readError(response))
      }

      const created = (await response.json()) as CutIteration
      setCurrentSession({
        ...currentSession,
        iterations: [...currentSession.iterations, created],
      })
      setStepNumber((prev) => prev + 1)
      setMessage(`Iteration step ${created.step_number} added.`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to add iteration')
    } finally {
      setIsLoading(false)
    }
  }

  const updateMode = (
    setter: (value: ModeVector) => void,
    source: ModeVector,
    key: keyof ModeVector,
    value: string,
  ) => {
    setter({ ...source, [key]: Number(value) })
  }

  return (
    <main className="page">
      <h1>Cut Sessions</h1>
      <p className="subtitle">Manual tester for Session API endpoints.</p>

      {error && <p className="alert error">Error: {error}</p>}
      {message && <p className="alert success">{message}</p>}

      <section className="card">
        <h2>Create session</h2>
        <form onSubmit={createSession} className="grid">
          <label>
            Machine name
            <input
              value={sessionForm.machine_name}
              onChange={(event) => setSessionForm({ ...sessionForm, machine_name: event.target.value })}
              required
            />
          </label>
          <label>
            Material group
            <input
              value={sessionForm.material_group}
              onChange={(event) => setSessionForm({ ...sessionForm, material_group: event.target.value })}
              required
            />
          </label>
          <label>
            Thickness (mm)
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={sessionForm.thickness_mm}
              onChange={(event) =>
                setSessionForm({ ...sessionForm, thickness_mm: Number(event.target.value) })
              }
              required
            />
          </label>
          <label>
            Gas branch
            <input
              value={sessionForm.gas_branch}
              onChange={(event) => setSessionForm({ ...sessionForm, gas_branch: event.target.value })}
              required
            />
          </label>
          <button type="submit" disabled={isLoading}>
            Create session
          </button>
        </form>
      </section>

      <section className="card">
        <h2>Load session</h2>
        <form onSubmit={loadSession} className="row">
          <input
            type="number"
            min="1"
            value={sessionIdInput}
            onChange={(event) => setSessionIdInput(event.target.value)}
            placeholder="Session ID"
            required
          />
          <button type="submit" disabled={isLoading}>
            Load
          </button>
        </form>
      </section>

      {currentSession && (
        <>
          <section className="card">
            <h2>Session details</h2>
            <ul>
              <li>ID: {currentSession.id}</li>
              <li>Created at: {new Date(currentSession.created_at).toLocaleString()}</li>
              <li>Machine: {currentSession.machine_name}</li>
              <li>Material: {currentSession.material_group}</li>
              <li>Thickness: {currentSession.thickness_mm}</li>
              <li>Gas branch: {currentSession.gas_branch}</li>
            </ul>
          </section>

          <section className="card">
            <h2>Add iteration</h2>
            <form onSubmit={addIteration} className="grid two-col">
              <label>
                Step number
                <input
                  type="number"
                  min="1"
                  value={stepNumber}
                  onChange={(event) => setStepNumber(Number(event.target.value))}
                  required
                />
              </label>
              <label>
                Defect code
                <input
                  value={defectCode}
                  onChange={(event) => setDefectCode(event.target.value)}
                  required
                />
              </label>
              <label>
                Severity level (0-3)
                <input
                  type="number"
                  min="0"
                  max="3"
                  value={severityLevel}
                  onChange={(event) => setSeverityLevel(Number(event.target.value))}
                  required
                />
              </label>

              <h3>Before</h3>
              <div />
              {Object.keys(DEFAULT_MODE).map((key) => (
                <label key={`before-${key}`}>
                  {key}
                  <input
                    type="number"
                    step="0.01"
                    value={beforeMode[key as keyof ModeVector]}
                    onChange={(event) =>
                      updateMode(
                        setBeforeMode,
                        beforeMode,
                        key as keyof ModeVector,
                        event.target.value,
                      )
                    }
                    required
                  />
                </label>
              ))}

              <h3>After</h3>
              <div />
              {Object.keys(DEFAULT_MODE).map((key) => (
                <label key={`after-${key}`}>
                  {key}
                  <input
                    type="number"
                    step="0.01"
                    value={afterMode[key as keyof ModeVector]}
                    onChange={(event) =>
                      updateMode(
                        setAfterMode,
                        afterMode,
                        key as keyof ModeVector,
                        event.target.value,
                      )
                    }
                    required
                  />
                </label>
              ))}

              <button type="submit" disabled={isLoading}>
                Add iteration
              </button>
            </form>
          </section>

          <section className="card">
            <h2>Recommendation</h2>
            <button type="button" onClick={getRecommendation} disabled={isLoading}>
              Get recommendation / Получить рекомендацию
            </button>
            {recommendation && (
              <ul>
                <li>power_after: {recommendation.power_after}</li>
                <li>speed_after: {recommendation.speed_after}</li>
                <li>frequency_after: {recommendation.frequency_after}</li>
                <li>pressure_after: {recommendation.pressure_after}</li>
                <li>focus_after: {recommendation.focus_after}</li>
                <li>height_after: {recommendation.height_after}</li>
                <li>duty_cycle_after: {recommendation.duty_cycle_after}</li>
                <li>nozzle_after: {recommendation.nozzle_after}</li>
              </ul>
            )}
          </section>

          <section className="card">
            <h2>Iterations (ordered by step_number)</h2>
            {orderedIterations.length === 0 ? (
              <p>No iterations yet.</p>
            ) : (
              <div className="iterations">
                {orderedIterations.map((iteration) => (
                  <article key={iteration.id}>
                    <h3>
                      Step {iteration.step_number} · defect {iteration.defect_code} · severity{' '}
                      {iteration.severity_level}
                    </h3>
                    <p>Created at: {new Date(iteration.created_at).toLocaleString()}</p>
                    <p>
                      Before: power {iteration.power_before}, speed {iteration.speed_before}, frequency{' '}
                      {iteration.frequency_before}, pressure {iteration.pressure_before}, focus{' '}
                      {iteration.focus_before}, height {iteration.height_before}, duty_cycle{' '}
                      {iteration.duty_cycle_before}, nozzle {iteration.nozzle_before}
                    </p>
                    <p>
                      After: power {iteration.power_after}, speed {iteration.speed_after}, frequency{' '}
                      {iteration.frequency_after}, pressure {iteration.pressure_after}, focus{' '}
                      {iteration.focus_after}, height {iteration.height_after}, duty_cycle{' '}
                      {iteration.duty_cycle_after}, nozzle {iteration.nozzle_after}
                    </p>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  )
}
