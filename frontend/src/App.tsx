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

type DictionaryItem = {
  value: string
  label_ru: string
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

type BaseModeResponse = ModeVector & {
  explanation: string
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

type TopLevelTab = 'operator' | 'sessions' | 'admin'

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
const emptyDictionary = (): DictionaryItem[] => []
const DEFAULT_MACHINE = 'HSG_3kW_150mm_VSX_NC30E'
const DEFAULT_MATERIAL = 'carbon'
const DEFAULT_GAS = 'N2'

const DEFECT_LABELS: Record<string, string> = {
  burr: 'Грат снизу',
  no_cut: 'Непрорез',
  overburn: 'Пережог / оплавление',
}

export default function App() {
  const [sessionForm, setSessionForm] = useState<CutSessionCreate>({
    machine_name: DEFAULT_MACHINE,
    material_group: DEFAULT_MATERIAL,
    thickness_mm: 1,
    gas_branch: DEFAULT_GAS,
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
  const [machines, setMachines] = useState<DictionaryItem[]>(emptyDictionary)
  const [materials, setMaterials] = useState<DictionaryItem[]>(emptyDictionary)
  const [gases, setGases] = useState<DictionaryItem[]>(emptyDictionary)
  const [defects, setDefects] = useState<DictionaryItem[]>(emptyDictionary)
  const [rules, setRules] = useState<RecommendationRule[]>([])
  const [rulesLoading, setRulesLoading] = useState(false)
  const [newRule, setNewRule] = useState<RecommendationRuleCreate>({
    defect_code: 'burr',
    parameter: RULE_PARAMETER_OPTIONS[0],
    direction: RULE_DIRECTION_OPTIONS[0],
    base_delta: 1,
    is_active: true,
  })
  const [editingRuleId, setEditingRuleId] = useState<number | null>(null)
  const [editRule, setEditRule] = useState<RecommendationRule | null>(null)
  const [activeTab, setActiveTab] = useState<TopLevelTab>('sessions')

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
    void loadDictionaries()
  }, [])

  function defectLabel(code: string): string {
    return defects.find((item) => item.value === code)?.label_ru ?? DEFECT_LABELS[code] ?? code
  }

  async function loadDictionaries() {
    try {
      const [machinesResponse, materialsResponse, gasesResponse, defectsResponse] = await Promise.all([
        fetch(`${API_BASE}/dict/machines`),
        fetch(`${API_BASE}/dict/materials`),
        fetch(`${API_BASE}/dict/gases`),
        fetch(`${API_BASE}/dict/defects`),
      ])

      if (!machinesResponse.ok || !materialsResponse.ok || !gasesResponse.ok || !defectsResponse.ok) {
        throw new Error('Не удалось загрузить справочники')
      }

      const machineOptions = (await machinesResponse.json()) as DictionaryItem[]
      const materialOptions = (await materialsResponse.json()) as DictionaryItem[]
      const gasOptions = (await gasesResponse.json()) as DictionaryItem[]
      const defectOptions = (await defectsResponse.json()) as DictionaryItem[]

      setMachines(machineOptions)
      setMaterials(materialOptions)
      setGases(gasOptions)
      setDefects(defectOptions)
      setDefectCode((prev) => (defectOptions.some((item) => item.value === prev) ? prev : (defectOptions[0]?.value ?? prev)))
      setNewRule((prev) => ({
        ...prev,
        defect_code: defectOptions.some((item) => item.value === prev.defect_code)
          ? prev.defect_code
          : (defectOptions[0]?.value ?? prev.defect_code),
      }))
      setSessionForm((prev) => ({
        ...prev,
        machine_name: machineOptions.some((item) => item.value === prev.machine_name)
          ? prev.machine_name
          : (machineOptions.find((item) => item.value === DEFAULT_MACHINE)?.value ?? machineOptions[0]?.value ?? prev.machine_name),
        material_group: materialOptions.some((item) => item.value === prev.material_group)
          ? prev.material_group
          : (materialOptions.find((item) => item.value === DEFAULT_MATERIAL)?.value ?? materialOptions[0]?.value ?? prev.material_group),
        gas_branch: gasOptions.some((item) => item.value === prev.gas_branch)
          ? prev.gas_branch
          : (gasOptions.find((item) => item.value === DEFAULT_GAS)?.value ?? gasOptions[0]?.value ?? prev.gas_branch),
      }))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить справочники')
    }
  }

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
      setError(e instanceof Error ? e.message : 'Не удалось загрузить правила')
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
    return `Ошибка запроса, статус ${response.status}`
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
      setActiveTab('operator')
      setMessage('Сессия создана. Можно начинать настройку.')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось создать сессию')
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
      setActiveTab('operator')
      setMessage('Сессия загружена. Можно продолжать настройку.')
    } catch (e) {
      setCurrentSession(null)
      setError(e instanceof Error ? e.message : 'Не удалось загрузить сессию')
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
      setMessage(`Рекомендация готова: дефект «${defectLabel(defectCode)}», уровень ${defectSeverity}.`)
    } catch (e) {
      setRecommendation(null)
      setRecommendedMode(emptyRecommendationMode())
      setError(e instanceof Error ? e.message : 'Не удалось получить рекомендацию')
    } finally {
      setIsLoading(false)
    }
  }

  async function loadBaseMode() {
    if (!currentSession) return

    setIsLoading(true)
    setError(null)
    setMessage(null)

    try {
      const response = await fetch(`${API_BASE}/sessions/${currentSession.id}/base-mode`)
      if (!response.ok) {
        throw new Error(await readError(response))
      }

      const data = (await response.json()) as BaseModeResponse
      setCurrentMode({
        power: data.power,
        speed: data.speed,
        frequency: data.frequency,
        pressure: data.pressure,
        focus: data.focus,
        height: data.height,
        duty_cycle: data.duty_cycle,
        nozzle: data.nozzle,
      })
      setMessage(data.explanation === 'Использовано точное совпадение' ? 'Стартовый режим загружен' : data.explanation)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить стартовый режим')
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
      setMessage(`Результат теста сохранён. Записан шаг ${created.step_number}.`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось сохранить результат теста')
    } finally {
      setIsLoading(false)
    }
  }

  async function createRule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (newRule.base_delta <= 0) {
      setError('base_delta должен быть больше 0')
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
      setMessage(`Правило #${created.id} создано.`)
      setNewRule({
        defect_code: newRule.defect_code,
        parameter: RULE_PARAMETER_OPTIONS[0],
        direction: RULE_DIRECTION_OPTIONS[0],
        base_delta: 1,
        is_active: true,
      })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось создать правило')
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
      setError('base_delta должен быть больше 0')
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
      setMessage(`Правило #${updated.id} сохранено.`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось обновить правило')
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
      setMessage(`Правило #${updated.id} ${updated.is_active ? 'включено' : 'отключено'}.`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось изменить статус правила')
    } finally {
      setRulesLoading(false)
    }
  }

  async function removeRule(rule: RecommendationRule) {
    const shouldDelete = window.confirm(
      `Удалить правило #${rule.id} (${defectLabel(rule.defect_code)} / ${rule.parameter})? Действие нельзя отменить.`,
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
      setMessage(`Правило #${rule.id} удалено.`)
      if (editingRuleId === rule.id) {
        cancelEditRule()
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось удалить правило')
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
      <h1>NeuroCut — интерфейс настройки</h1>
      <p className="subtitle">Операторский интерфейс: подбор режима резки по шагам.</p>
      <nav className="tabs" aria-label="Главные разделы">
        <button
          type="button"
          className={activeTab === 'operator' ? 'ghost active' : 'ghost'}
          onClick={() => setActiveTab('operator')}
        >
          Настройка
        </button>
        <button
          type="button"
          className={activeTab === 'sessions' ? 'ghost active' : 'ghost'}
          onClick={() => setActiveTab('sessions')}
        >
          Сессии
        </button>
        <button
          type="button"
          className={activeTab === 'admin' ? 'ghost active' : 'ghost'}
          onClick={() => setActiveTab('admin')}
        >
          Админ
        </button>
      </nav>

      {error && <p className="alert error">Ошибка: {error}</p>}
      {message && <p className="alert success">{message}</p>}

      {activeTab === 'admin' && (
        <section className="card">
          <h2>Админ: правила алгоритма</h2>
          <p className="muted">Технический раздел для инженера/технолога. Оператору обычно не нужен.</p>
          <div className="row">
            <button type="button" onClick={loadRules} disabled={rulesLoading}>
              Обновить правила
            </button>
          </div>

          <h3>Создать правило</h3>
          <form onSubmit={createRule} className="grid rule-grid">
            <label>
              Дефект
              <select
                value={newRule.defect_code}
                onChange={(event) => setNewRule({ ...newRule, defect_code: event.target.value })}
                required
              >
                {defects.map((item) => (
                  <option key={`rule-${item.value}`} value={item.value}>
                    {item.label_ru}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Параметр
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
              Направление
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
              Базовое изменение
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
              Активно
            </label>
            <button type="submit" disabled={rulesLoading}>
              Добавить правило
            </button>
          </form>

          <h3>Правила</h3>
          {rules.length === 0 ? (
            <p className="muted">Правила не загружены. Нажмите «Обновить правила».</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Дефект</th>
                    <th>Параметр</th>
                    <th>Направление</th>
                    <th>Базовое изменение</th>
                    <th>Активно</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.map((rule) => {
                    const isEditing = editingRuleId === rule.id && editRule !== null
                    return (
                      <tr key={rule.id}>
                        <td>{rule.id}</td>
                        <td>{defectLabel(rule.defect_code)}</td>
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
                        <td>{isEditing ? (editRule.is_active ? 'да' : 'нет') : rule.is_active ? 'да' : 'нет'}</td>
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
                                  Сохранить
                                </button>
                                <button
                                  type="button"
                                  onClick={cancelEditRule}
                                  disabled={rulesLoading}
                                  className="ghost"
                                >
                                  Отмена
                                </button>
                              </>
                            ) : (
                              <button
                                type="button"
                                onClick={() => startEditRule(rule)}
                                disabled={rulesLoading}
                                className="ghost"
                              >
                                Изменить
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => toggleRuleActive(rule)}
                              disabled={rulesLoading}
                              className="ghost"
                            >
                              {rule.is_active ? 'Отключить' : 'Включить'}
                            </button>
                            <button
                              type="button"
                              onClick={() => removeRule(rule)}
                              disabled={rulesLoading}
                              className="ghost danger"
                            >
                              Удалить
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
      )}

      {activeTab === 'sessions' && (
        <>
          <section className="card">
            <h2>Создать сессию</h2>
            <form onSubmit={createSession} className="grid">
              <label>
                Станок
                <select
                  value={sessionForm.machine_name}
                  onChange={(event) => setSessionForm({ ...sessionForm, machine_name: event.target.value })}
                  required
                >
                  {machines.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label_ru}
                    </option>
                  ))}
                </select>
                <p className="muted">Выберите ваш станок из списка. Значение применяется как стандарт машины.</p>
              </label>
              <label>
                Материал
                <select
                  value={sessionForm.material_group}
                  onChange={(event) => setSessionForm({ ...sessionForm, material_group: event.target.value })}
                  required
                >
                  {materials.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label_ru}
                    </option>
                  ))}
                </select>
                <p className="muted">Например: углеродистая сталь для типовых заказов.</p>
              </label>
              <label>
                Толщина (мм)
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
                <p className="muted">Укажите фактическую толщину листа в миллиметрах (пример: 4.0).</p>
              </label>
              <label>
                Газ
                <select
                  value={sessionForm.gas_branch}
                  onChange={(event) => setSessionForm({ ...sessionForm, gas_branch: event.target.value })}
                  required
                >
                  {gases.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label_ru}
                    </option>
                  ))}
                </select>
                <p className="muted">Выберите газ резки, который сейчас подключён к станку.</p>
              </label>
              <button type="submit" disabled={isLoading}>
                Создать сессию
              </button>
            </form>
          </section>

          <section className="card">
            <h2>Загрузить сессию</h2>
            <form onSubmit={loadSession} className="row">
              <input
                type="number"
                min="1"
                value={sessionIdInput}
                onChange={(event) => setSessionIdInput(event.target.value)}
                placeholder="ID сессии"
                required
              />
              <button type="submit" disabled={isLoading}>
                Загрузить
              </button>
            </form>
          </section>

          {currentSession ? (
            <>
              <section className="card">
                <h2>Детали сессии</h2>
                <p>ID сессии: {currentSession.id}</p>
                <p>Станок: {machines.find((item) => item.value === currentSession.machine_name)?.label_ru ?? currentSession.machine_name}</p>
                <p>Материал: {materials.find((item) => item.value === currentSession.material_group)?.label_ru ?? currentSession.material_group}</p>
                <p>Толщина: {currentSession.thickness_mm} мм</p>
                <p>Газ: {gases.find((item) => item.value === currentSession.gas_branch)?.label_ru ?? currentSession.gas_branch}</p>
                <p>Создано: {new Date(currentSession.created_at).toLocaleString()}</p>
              </section>
              <section className="card">
                <h2>Итерации (по step_number)</h2>
                {orderedIterations.length === 0 ? (
                  <p>Итераций пока нет.</p>
                ) : (
                  <div className="iterations">
                    {orderedIterations.map((iteration) => (
                      <article key={iteration.id}>
                        <h3>
                          Шаг {iteration.step_number} · дефект {defectLabel(iteration.defect_code)} · уровень{' '}
                          {iteration.severity_level}
                        </h3>
                        <p>Создано: {new Date(iteration.created_at).toLocaleString()}</p>
                        <p>
                          До: power {iteration.power_before}, speed {iteration.speed_before}, frequency{' '}
                          {iteration.frequency_before}, pressure {iteration.pressure_before}, focus{' '}
                          {iteration.focus_before}, height {iteration.height_before}, duty_cycle{' '}
                          {iteration.duty_cycle_before}, nozzle {iteration.nozzle_before}
                        </p>
                        <p>
                          После: power {iteration.power_after}, speed {iteration.speed_after}, frequency{' '}
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
          ) : (
            <section className="card">
              <p className="muted">Сессия не выбрана. Создайте или загрузите сессию, чтобы увидеть историю.</p>
            </section>
          )}
        </>
      )}

      {activeTab === 'operator' && (
        <>
          {!currentSession ? (
            <section className="card">
              <h2>Настройка</h2>
              <p className="muted">Шаг 1: выберите сессию (создайте новую или загрузите существующую).</p>
              <p className="muted">Шаг 2: загрузите стартовый режим.</p>
              <p className="muted">Шаг 3: запустите цикл подбора и подтвердите результат реза.</p>
              <button type="button" onClick={() => setActiveTab('sessions')}>
                Перейти в раздел «Сессии»
              </button>
            </section>
          ) : (
          <section className="card">
            <h2>Настройка</h2>
            <p className="session-meta">
              Сессия #{currentSession.id} · Шаг {stepNumber} · Станок{' '}
              {machines.find((item) => item.value === currentSession.machine_name)?.label_ru ?? currentSession.machine_name}
            </p>

            <h3>Шаг 1. Проверка сессии</h3>
            <p className="muted">Сессия выбрана. Проверьте станок, материал и газ перед запуском цикла.</p>

            <h3>Шаг 2. Загрузите стартовый режим</h3>
            <div className="row">
              <button type="button" onClick={loadBaseMode} disabled={isLoading}>
                Загрузить стартовый режим
              </button>
            </div>
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

            <h3>Шаг 3. Цикл настройки</h3>
            <h4>3.1 Дефект и выраженность</h4>
            <div className="grid two-col">
              <label>
                Дефект
                <select
                  value={defectCode}
                  onChange={(event) => setDefectCode(event.target.value)}
                >
                  {defects.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label_ru}
                    </option>
                  ))}
                </select>
                <p className="muted">Выберите дефект, который реально видите на детали после тестового реза.</p>
              </label>
              <div>
                <p className="mini-label">Наблюдаемая выраженность</p>
                <p className="muted">1 — слабо, 2 — средне, 3 — сильно.</p>
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
              Получить рекомендацию
            </button>

            <h4>3.2 Рекомендация на следующий шаг</h4>
            {!recommendation ? (
              <p className="muted">Пока нет рекомендации. Нажмите «Получить рекомендацию».</p>
            ) : (
              <div className="recommendation-box">
                <p>
                  Изменённые параметры:{' '}
                  {recommendationDiff.length > 0 ? recommendationDiff.join(', ') : 'нет (режим не изменился)'}
                </p>
                <ul>
                  {MODE_KEYS.map((key) => (
                    <li key={`diff-${key}`}>
                      {key}: {currentMode[key]} → {recommendedMode[key]}
                    </li>
                  ))}
                </ul>
                <h4>Пояснение</h4>
                <ul>
                  {recommendation.explanation.map((line, index) => (
                    <li key={`${index}-${line}`}>{line}</li>
                  ))}
                </ul>
                <button type="button" onClick={copyRecommendationToAfter} disabled={isLoading}>
                  Скопировать рекомендованный режим
                </button>
                {recommendationCopied && (
                  <p className="inline-success">Рекомендованный режим скопирован для переноса на станок.</p>
                )}
              </div>
            )}

            <h4>3.3 Результат тестового реза</h4>
            <p className="muted">Оператор выполняет тестовый рез на станке и подтверждает результат ниже.</p>
            <div className="button-group">
              <button
                type="button"
                className={resultSeverity === 0 ? 'ghost active' : 'ghost'}
                onClick={() => setResultSeverity(0)}
              >
                0 исправлено
              </button>
              <button
                type="button"
                className={resultSeverity === 1 ? 'ghost active' : 'ghost'}
                onClick={() => setResultSeverity(1)}
              >
                1 слабый
              </button>
              <button
                type="button"
                className={resultSeverity === 2 ? 'ghost active' : 'ghost'}
                onClick={() => setResultSeverity(2)}
              >
                2 средний
              </button>
              <button
                type="button"
                className={resultSeverity === 3 ? 'ghost active' : 'ghost'}
                onClick={() => setResultSeverity(3)}
              >
                3 сильный
              </button>
            </div>
            <button type="button" onClick={confirmTestResult} disabled={isLoading || !recommendation}>
              Подтвердить результат
            </button>
          </section>
          )}
        </>
      )}
    </main>
  )
}
