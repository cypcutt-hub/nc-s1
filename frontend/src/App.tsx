import { FormEvent, useEffect, useMemo, useState } from 'react'

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
  explanation: string[]
}

type RuleParameter =
  | 'power'
  | 'speed'
  | 'frequency'
  | 'pressure'
  | 'focus'
  | 'height'
  | 'duty_cycle'
  | 'nozzle'

type RuleDirection = 'increase' | 'decrease'

type RecommendationRule = {
  id: number
  defect_code: string
  parameter: RuleParameter
  direction: RuleDirection
  base_delta: number
  is_active: boolean
}

type RecommendationRuleCreate = {
  defect_code: string
  parameter: RuleParameter
  direction: RuleDirection
  base_delta: number
  is_active: boolean
}

const API_BASE = import.meta.env.VITE_API_BASE_PATH ?? '/api'

const MODE_KEYS: Array<keyof ModeVector> = [
  'power',
  'speed',
  'frequency',
  'pressure',
  'focus',
  'height',
  'duty_cycle',
  'nozzle',
]

const DEFECT_OPTIONS = ['burr', 'no_cut', 'overburn']
const RULE_PARAMETER_OPTIONS: RuleParameter[] = [
  'power',
  'speed',
  'frequency',
  'pressure',
  'focus',
  'height',
  'duty_cycle',
  'nozzle',
]
const RULE_DIRECTION_OPTIONS: RuleDirection[] = ['increase', 'decrease']

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

const emptyRecommendationMode = (): ModeVector => ({ ...DEFAULT_MODE })

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
  const [defectSeverity, setDefectSeverity] = useState(1)
  const [resultSeverity, setResultSeverity] = useState(1)

  const [currentMode, setCurrentMode] = useState<ModeVector>(DEFAULT_MODE)
  const [recommendedMode, setRecommendedMode] = useState<ModeVector>(DEFAULT_MODE)

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)
  const [recommendationCopied, setRecommendationCopied] = useState(false)
  const [rules, setRules] = useState<RecommendationRule[]>([])
  const [rulesLoading, setRulesLoading] = useState(false)
  const [newRule, setNewRule] = useState<RecommendationRuleCreate>({
    defect_code: DEFECT_OPTIONS[0],
    parameter: RULE_PARAMETER_OPTIONS[0],
    direction: RULE_DIRECTION_OPTIONS[0],
    base_delta: 1,
    is_active: true,
  })
  const [editingRuleId, setEditingRuleId] = useState<number | null>(null)
  const [editRule, setEditRule] = useState<RecommendationRule | null>(null)

  const orderedIterations = useMemo(() => {
    if (!currentSession) return []
    return [...currentSession.iterations].sort((a, b) => a.step_number - b.step_number)
  }, [currentSession])

  const recommendationDiff = useMemo(() => {
    if (!recommendation) return []
    return MODE_KEYS.filter((key) => currentMode[key] !== recommendedMode[key])
  }, [currentMode, recommendedMode, recommendation])

  useEffect(() => {
    void loadRules()
  }, [])

  async function loadRules() {
    setRulesLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/rules`)
      if (!response.ok) {
        throw new Error(await readError(response))
      }

      const data = (await response.json()) as RecommendationRule[]
      setRules(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load rules')
    } finally {
      setRulesLoading(false)
    }
  }

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
      setRecommendationCopied(false)
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
      if (data.iterations.length > 0) {
        const last = data.iterations.sort((a, b) => b.step_number - a.step_number)[0]
        setCurrentMode({
          power: last.power_after,
          speed: last.speed_after,
          frequency: last.frequency_after,
          pressure: last.pressure_after,
          focus: last.focus_after,
          height: last.height_after,
          duty_cycle: last.duty_cycle_after,
          nozzle: last.nozzle_after,
        })
      }
      setRecommendation(null)
      setRecommendationCopied(false)
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
    setRecommendationCopied(false)

    try {
      const response = await fetch(`${API_BASE}/sessions/${currentSession.id}/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          defect_code: defectCode,
          severity_level: defectSeverity,
          current_mode: currentMode,
        }),
      })

      if (!response.ok) {
        throw new Error(await readError(response))
      }

      const data = (await response.json()) as Recommendation
      const newMode = {
        power: data.power_after,
        speed: data.speed_after,
        frequency: data.frequency_after,
        pressure: data.pressure_after,
        focus: data.focus_after,
        height: data.height_after,
        duty_cycle: data.duty_cycle_after,
        nozzle: data.nozzle_after,
      }
      setRecommendedMode(newMode)
      setRecommendation(data)
      setMessage(`Recommendation ready for defect "${defectCode}" (severity ${defectSeverity}).`)
    } catch (e) {
      setRecommendation(null)
      setRecommendedMode(emptyRecommendationMode())
      setError(e instanceof Error ? e.message : 'Failed to get recommendation')
    } finally {
      setIsLoading(false)
    }
  }

  function copyRecommendationToAfter() {
    if (!recommendation) return
    setRecommendedMode({
      power: recommendation.power_after,
      speed: recommendation.speed_after,
      frequency: recommendation.frequency_after,
      pressure: recommendation.pressure_after,
      focus: recommendation.focus_after,
      height: recommendation.height_after,
      duty_cycle: recommendation.duty_cycle_after,
      nozzle: recommendation.nozzle_after,
    })
    setRecommendationCopied(true)
  }

  async function confirmTestResult() {
    if (!currentSession || !recommendation) return

    setIsLoading(true)
    setError(null)
    setMessage(null)

    try {
      const payload = {
        step_number: stepNumber,
        defect_code: defectCode,
        severity_level: resultSeverity,
        power_before: currentMode.power,
        speed_before: currentMode.speed,
        frequency_before: currentMode.frequency,
        pressure_before: currentMode.pressure,
        focus_before: currentMode.focus,
        height_before: currentMode.height,
        duty_cycle_before: currentMode.duty_cycle,
        nozzle_before: currentMode.nozzle,
        power_after: recommendedMode.power,
        speed_after: recommendedMode.speed,
        frequency_after: recommendedMode.frequency,
        pressure_after: recommendedMode.pressure,
        focus_after: recommendedMode.focus,
        height_after: recommendedMode.height,
        duty_cycle_after: recommendedMode.duty_cycle,
        nozzle_after: recommendedMode.nozzle,
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
      setCurrentMode({ ...recommendedMode })
      setRecommendation(null)
      setRecommendationCopied(false)
      setMessage(`Test result saved. Step ${created.step_number} recorded.`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save test result')
    } finally {
      setIsLoading(false)
    }
  }

  async function createRule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (newRule.base_delta <= 0) {
      setError('base_delta must be greater than 0')
      return
    }

    setRulesLoading(true)
    setError(null)
    setMessage(null)

    try {
      const response = await fetch(`${API_BASE}/rules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newRule),
      })

      if (!response.ok) {
        throw new Error(await readError(response))
      }

      const created = (await response.json()) as RecommendationRule
      setRules((prev) => [...prev, created].sort((a, b) => a.id - b.id))
      setMessage(`Rule #${created.id} created.`)
      setNewRule({
        defect_code: newRule.defect_code,
        parameter: RULE_PARAMETER_OPTIONS[0],
        direction: RULE_DIRECTION_OPTIONS[0],
        base_delta: 1,
        is_active: true,
      })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create rule')
    } finally {
      setRulesLoading(false)
    }
  }

  function startEditRule(rule: RecommendationRule) {
    setEditingRuleId(rule.id)
    setEditRule({ ...rule })
  }

  function cancelEditRule() {
    setEditingRuleId(null)
    setEditRule(null)
  }

  async function saveRule(ruleId: number) {
    if (!editRule || editRule.base_delta <= 0) {
      setError('base_delta must be greater than 0')
      return
    }

    setRulesLoading(true)
    setError(null)
    setMessage(null)
    try {
      const response = await fetch(`${API_BASE}/rules/${ruleId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parameter: editRule.parameter,
          direction: editRule.direction,
          base_delta: editRule.base_delta,
          is_active: editRule.is_active,
        }),
      })
      if (!response.ok) {
        throw new Error(await readError(response))
      }

      const updated = (await response.json()) as RecommendationRule
      setRules((prev) => prev.map((rule) => (rule.id === ruleId ? updated : rule)))
      setEditingRuleId(null)
      setEditRule(null)
      setMessage(`Rule #${updated.id} saved.`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to update rule')
    } finally {
      setRulesLoading(false)
    }
  }

  async function toggleRuleActive(rule: RecommendationRule) {
    setRulesLoading(true)
    setError(null)
    setMessage(null)
    try {
      const response = await fetch(`${API_BASE}/rules/${rule.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !rule.is_active }),
      })
      if (!response.ok) {
        throw new Error(await readError(response))
      }

      const updated = (await response.json()) as RecommendationRule
      setRules((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
      setMessage(`Rule #${updated.id} ${updated.is_active ? 'enabled' : 'disabled'}.`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to toggle rule status')
    } finally {
      setRulesLoading(false)
    }
  }

  async function removeRule(rule: RecommendationRule) {
    const shouldDelete = window.confirm(
      `Delete rule #${rule.id} (${rule.defect_code} / ${rule.parameter})? This action cannot be undone.`,
    )
    if (!shouldDelete) return

    setRulesLoading(true)
    setError(null)
    setMessage(null)
    try {
      const response = await fetch(`${API_BASE}/rules/${rule.id}`, {
        method: 'DELETE',
      })
      if (!response.ok) {
        throw new Error(await readError(response))
      }

      setRules((prev) => prev.filter((item) => item.id !== rule.id))
      setMessage(`Rule #${rule.id} deleted.`)
      if (editingRuleId === rule.id) {
        cancelEditRule()
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete rule')
    } finally {
      setRulesLoading(false)
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
      <h1>NeuroCut Operator Tuning</h1>
      <p className="subtitle">Session API demo: recommendation loop for manual shop-floor tuning.</p>

      {error && <p className="alert error">Error: {error}</p>}
      {message && <p className="alert success">{message}</p>}

      <section className="card">
        <h2>Algorithm rules</h2>
        <p className="muted">Manage recommendation rules stored in DB.</p>
        <div className="row">
          <button type="button" onClick={loadRules} disabled={rulesLoading}>
            Refresh rules
          </button>
        </div>

        <h3>Create rule</h3>
        <form onSubmit={createRule} className="grid rule-grid">
          <label>
            Defect code
            <input
              list="rule-defect-codes"
              value={newRule.defect_code}
              onChange={(event) => setNewRule({ ...newRule, defect_code: event.target.value })}
              required
            />
            <datalist id="rule-defect-codes">
              {DEFECT_OPTIONS.map((item) => (
                <option key={`rule-${item}`} value={item} />
              ))}
            </datalist>
          </label>
          <label>
            Parameter
            <select
              value={newRule.parameter}
              onChange={(event) =>
                setNewRule({ ...newRule, parameter: event.target.value as RuleParameter })
              }
              required
            >
              {RULE_PARAMETER_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label>
            Direction
            <select
              value={newRule.direction}
              onChange={(event) =>
                setNewRule({ ...newRule, direction: event.target.value as RuleDirection })
              }
              required
            >
              {RULE_DIRECTION_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label>
            Base delta
            <input
              type="number"
              min="0.000001"
              step="0.01"
              value={newRule.base_delta}
              onChange={(event) => setNewRule({ ...newRule, base_delta: Number(event.target.value) })}
              required
            />
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={newRule.is_active}
              onChange={(event) => setNewRule({ ...newRule, is_active: event.target.checked })}
            />
            Active
          </label>
          <button type="submit" disabled={rulesLoading}>
            Add rule
          </button>
        </form>

        <h3>Rules</h3>
        {rules.length === 0 ? (
          <p className="muted">No rules loaded yet. Click “Refresh rules”.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Defect</th>
                  <th>Parameter</th>
                  <th>Direction</th>
                  <th>Base delta</th>
                  <th>Active</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule) => {
                  const isEditing = editingRuleId === rule.id && editRule !== null
                  return (
                    <tr key={rule.id}>
                      <td>{rule.id}</td>
                      <td>{rule.defect_code}</td>
                      <td>
                        {isEditing ? (
                          <select
                            value={editRule.parameter}
                            onChange={(event) =>
                              setEditRule({ ...editRule, parameter: event.target.value as RuleParameter })
                            }
                          >
                            {RULE_PARAMETER_OPTIONS.map((option) => (
                              <option key={`${rule.id}-${option}`} value={option}>
                                {option}
                              </option>
                            ))}
                          </select>
                        ) : (
                          rule.parameter
                        )}
                      </td>
                      <td>
                        {isEditing ? (
                          <select
                            value={editRule.direction}
                            onChange={(event) =>
                              setEditRule({ ...editRule, direction: event.target.value as RuleDirection })
                            }
                          >
                            {RULE_DIRECTION_OPTIONS.map((option) => (
                              <option key={`${rule.id}-${option}`} value={option}>
                                {option}
                              </option>
                            ))}
                          </select>
                        ) : (
                          rule.direction
                        )}
                      </td>
                      <td>
                        {isEditing ? (
                          <input
                            type="number"
                            min="0.000001"
                            step="0.01"
                            value={editRule.base_delta}
                            onChange={(event) =>
                              setEditRule({ ...editRule, base_delta: Number(event.target.value) })
                            }
                          />
                        ) : (
                          rule.base_delta
                        )}
                      </td>
                      <td>{isEditing ? (editRule.is_active ? 'yes' : 'no') : rule.is_active ? 'yes' : 'no'}</td>
                      <td>
                        <div className="button-group">
                          {isEditing ? (
                            <>
                              <button
                                type="button"
                                onClick={() => saveRule(rule.id)}
                                disabled={rulesLoading}
                                className="ghost"
                              >
                                Save
                              </button>
                              <button
                                type="button"
                                onClick={cancelEditRule}
                                disabled={rulesLoading}
                                className="ghost"
                              >
                                Cancel
                              </button>
                            </>
                          ) : (
                            <button
                              type="button"
                              onClick={() => startEditRule(rule)}
                              disabled={rulesLoading}
                              className="ghost"
                            >
                              Edit
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => toggleRuleActive(rule)}
                            disabled={rulesLoading}
                            className="ghost"
                          >
                            {rule.is_active ? 'Disable' : 'Enable'}
                          </button>
                          <button
                            type="button"
                            onClick={() => removeRule(rule)}
                            disabled={rulesLoading}
                            className="ghost danger"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

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
            <h2>Operator workflow</h2>
            <p className="session-meta">
              Session #{currentSession.id} · Step {stepNumber} · Machine {currentSession.machine_name}
            </p>

            <h3>A) Current mode</h3>
            <div className="grid two-col">
              {MODE_KEYS.map((key) => (
                <label key={`current-${key}`}>
                  {key}
                  <input
                    type="number"
                    step="0.01"
                    value={currentMode[key]}
                    onChange={(event) => updateMode(setCurrentMode, currentMode, key, event.target.value)}
                  />
                </label>
              ))}
            </div>

            <h3>B) Defect and severity</h3>
            <div className="grid two-col">
              <label>
                Defect code
                <input
                  list="defect-codes"
                  value={defectCode}
                  onChange={(event) => setDefectCode(event.target.value)}
                />
                <datalist id="defect-codes">
                  {DEFECT_OPTIONS.map((item) => (
                    <option key={item} value={item} />
                  ))}
                </datalist>
              </label>
              <div>
                <p className="mini-label">Observed severity</p>
                <div className="button-group">
                  {[1, 2, 3].map((value) => (
                    <button
                      key={`defect-${value}`}
                      type="button"
                      className={defectSeverity === value ? 'ghost active' : 'ghost'}
                      onClick={() => setDefectSeverity(value)}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <button type="button" onClick={getRecommendation} disabled={isLoading}>
              Get recommendation
            </button>

            <h3>C) Next step recommendation</h3>
            {!recommendation ? (
              <p className="muted">No recommendation yet. Click “Get recommendation”.</p>
            ) : (
              <div className="recommendation-box">
                <p>
                  Changed parameters:{' '}
                  {recommendationDiff.length > 0 ? recommendationDiff.join(', ') : 'none (same as current mode)'}
                </p>
                <ul>
                  {MODE_KEYS.map((key) => (
                    <li key={`diff-${key}`}>
                      {key}: {currentMode[key]} → {recommendedMode[key]}
                    </li>
                  ))}
                </ul>
                <h4>Explanation</h4>
                <ul>
                  {recommendation.explanation.map((line, index) => (
                    <li key={`${index}-${line}`}>{line}</li>
                  ))}
                </ul>
                <button type="button" onClick={copyRecommendationToAfter} disabled={isLoading}>
                  Copy recommended mode
                </button>
                {recommendationCopied && (
                  <p className="inline-success">Recommended mode copied for manual machine transfer.</p>
                )}
              </div>
            )}

            <h3>D) Test cut result</h3>
            <p className="muted">Operator runs test cut on machine manually, then confirms the result below.</p>
            <div className="button-group">
              <button
                type="button"
                className={resultSeverity === 0 ? 'ghost active' : 'ghost'}
                onClick={() => setResultSeverity(0)}
              >
                0 fixed
              </button>
              <button
                type="button"
                className={resultSeverity === 1 ? 'ghost active' : 'ghost'}
                onClick={() => setResultSeverity(1)}
              >
                1 weak
              </button>
              <button
                type="button"
                className={resultSeverity === 2 ? 'ghost active' : 'ghost'}
                onClick={() => setResultSeverity(2)}
              >
                2 medium
              </button>
              <button
                type="button"
                className={resultSeverity === 3 ? 'ghost active' : 'ghost'}
                onClick={() => setResultSeverity(3)}
              >
                3 strong
              </button>
            </div>
            <button type="button" onClick={confirmTestResult} disabled={isLoading || !recommendation}>
              Confirm test result
            </button>
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
