import { Alert, Box, Button, Card, CardContent, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Divider, Stack, TextField, Typography } from '@mui/material'
import { type DragEvent, forwardRef, useEffect, useImperativeHandle, useMemo, useState } from 'react'
import { api } from '../services/api'

type Employee = {
  id: number
  name: string
  color: string
  salonId?: number | null
}

export type StaffScheduleCanvasEmployee = {
  id: number
  name: string
  color?: string
  salonId?: number | null
}

type Assignment = {
  id: number
  employeeId: number
  dateKey: string
  startMinutes: number
  durationMinutes: number
}

type PeriodMode = 'month' | 'rolling30'

const EMPLOYEES: Employee[] = [
  { id: 1, name: 'Anna K.', color: '#1565c0' },
  { id: 2, name: 'Marek Z.', color: '#2e7d32' },
  { id: 3, name: 'Iza M.', color: '#7b1fa2' },
  { id: 4, name: 'Ola P.', color: '#ef6c00' },
  { id: 5, name: 'Kasia L.', color: '#455a64' },
  { id: 6, name: 'Piotr W.', color: '#00838f' },
]
const EMPLOYEE_COLORS = ['#1565c0', '#2e7d32', '#7b1fa2', '#ef6c00', '#455a64', '#00838f', '#ad1457', '#6d4c41']

const DAY_MINUTES = 24 * 60
const DEFAULT_DURATION = 8 * 60
const DEFAULT_START = 8 * 60

const formatDateKey = (value: Date) => {
  const yyyy = value.getFullYear()
  const mm = String(value.getMonth() + 1).padStart(2, '0')
  const dd = String(value.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

const parseDateKey = (value: string) => new Date(`${value}T00:00:00`)
const addDays = (value: Date, days: number) => {
  const next = new Date(value)
  next.setDate(next.getDate() + days)
  return next
}

const minutesToTime = (minutes: number) => {
  const clamped = Math.max(0, Math.min(DAY_MINUTES - 1, minutes))
  const hh = String(Math.floor(clamped / 60)).padStart(2, '0')
  const mm = String(clamped % 60).padStart(2, '0')
  return `${hh}:${mm}`
}

const timeToMinutes = (value: string) => {
  const [rawHours, rawMinutes] = value.split(':')
  const hours = Number(rawHours || 0)
  const minutes = Number(rawMinutes || 0)
  return Math.max(0, Math.min(DAY_MINUTES - 1, hours * 60 + minutes))
}

const formatRange = (startMinutes: number, durationMinutes: number) => {
  const endMinutes = Math.min(DAY_MINUTES, startMinutes + durationMinutes)
  return `${minutesToTime(startMinutes)} - ${minutesToTime(endMinutes)}`
}

const dayLabel = (dateKey: string) => {
  const value = parseDateKey(dateKey)
  return value.toLocaleDateString('pl-PL', { weekday: 'short', day: '2-digit', month: '2-digit' })
}

const isWeekend = (dateKey: string) => {
  const day = parseDateKey(dateKey).getDay()
  return day === 0 || day === 6
}

const getWeekendAnchor = (dateKey: string) => {
  const value = parseDateKey(dateKey)
  const day = value.getDay()
  if (day === 6) return formatDateKey(value)
  if (day === 0) return formatDateKey(addDays(value, -1))
  return null
}

const dragPayload = (event: DragEvent) => event.dataTransfer.getData('text/plain')

type StaffScheduleCanvasProps = {
  employees?: StaffScheduleCanvasEmployee[]
  autoLoadOnMount?: boolean
}

export type StaffScheduleCanvasHandle = {
  loadFromBackend: () => Promise<void>
  saveAsOfficialSchedule: () => Promise<void>
}

const StaffScheduleCanvas = forwardRef<StaffScheduleCanvasHandle, StaffScheduleCanvasProps>(function StaffScheduleCanvas(
  { employees, autoLoadOnMount = false }: StaffScheduleCanvasProps,
  ref,
) {
  const [periodMode, setPeriodMode] = useState<PeriodMode>('month')
  const [anchorDate, setAnchorDate] = useState(formatDateKey(new Date()))
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [nextId, setNextId] = useState(1)
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<number | null>(null)
  const [editStart, setEditStart] = useState('08:00')
  const [editDurationHours, setEditDurationHours] = useState('8')
  const [backendInfo, setBackendInfo] = useState('')
  const [backendError, setBackendError] = useState('')

  const periodStart = useMemo(() => {
    const anchor = parseDateKey(anchorDate)
    if (periodMode === 'month') {
      return new Date(anchor.getFullYear(), anchor.getMonth(), 1)
    }
    return anchor
  }, [anchorDate, periodMode])

  const periodLength = periodMode === 'month'
    ? new Date(periodStart.getFullYear(), periodStart.getMonth() + 1, 0).getDate()
    : 30

  const dayKeys = useMemo(
    () => Array.from({ length: periodLength }, (_, index) => formatDateKey(addDays(periodStart, index))),
    [periodLength, periodStart],
  )

  const resolvedEmployees = useMemo<Employee[]>(
    () => (employees && employees.length > 0
      ? employees.map((employee, index) => ({
          id: employee.id,
          name: employee.name,
          color: employee.color || EMPLOYEE_COLORS[index % EMPLOYEE_COLORS.length],
          salonId: employee.salonId ?? null,
        }))
      : EMPLOYEES),
    [employees],
  )

  const employeeById = useMemo(
    () => new Map(resolvedEmployees.map((employee) => [employee.id, employee])),
    [resolvedEmployees],
  )

  const visibleAssignments = useMemo(
    () => assignments.filter((item) => dayKeys.includes(item.dateKey)),
    [assignments, dayKeys],
  )

  const selectedAssignment = useMemo(
    () => assignments.find((item) => item.id === selectedAssignmentId) || null,
    [assignments, selectedAssignmentId],
  )

  useEffect(() => {
    if (!selectedAssignment) return
    setEditStart(minutesToTime(selectedAssignment.startMinutes))
    setEditDurationHours((selectedAssignment.durationMinutes / 60).toFixed(1).replace('.0', ''))
  }, [selectedAssignment])

  const assignmentWarnings = useMemo(() => {
    const warnings: string[] = []
    const byEmployeeDay = new Map<string, Assignment[]>()
    for (const assignment of visibleAssignments) {
      const key = `${assignment.employeeId}:${assignment.dateKey}`
      const list = byEmployeeDay.get(key) || []
      list.push(assignment)
      byEmployeeDay.set(key, list)
    }

    byEmployeeDay.forEach((dayAssignments, key) => {
      const [employeeIdRaw, dateKey] = key.split(':')
      const employee = employeeById.get(Number(employeeIdRaw))
      if (!employee) return

      const totalMinutes = dayAssignments.reduce((sum, item) => sum + item.durationMinutes, 0)
      if (totalMinutes > DEFAULT_DURATION) {
        warnings.push(`${employee.name}: ${dateKey} ma ${Math.round(totalMinutes / 60)}h (limit 8h).`)
      }

      const sorted = [...dayAssignments].sort((a, b) => a.startMinutes - b.startMinutes)
      for (let index = 1; index < sorted.length; index += 1) {
        const previous = sorted[index - 1]
        const current = sorted[index]
        if (previous.startMinutes + previous.durationMinutes > current.startMinutes) {
          warnings.push(`${employee.name}: nakladajace sie zmiany w dniu ${dateKey}.`)
          break
        }
      }
    })

    for (const employee of resolvedEmployees) {
      const weekendAnchors = new Set<string>()
      for (const assignment of visibleAssignments) {
        if (assignment.employeeId !== employee.id) continue
        const anchor = getWeekendAnchor(assignment.dateKey)
        if (anchor) weekendAnchors.add(anchor)
      }
      const anchors = [...weekendAnchors].sort()
      for (let index = 1; index < anchors.length; index += 1) {
        const previous = parseDateKey(anchors[index - 1])
        const current = parseDateKey(anchors[index])
        const days = Math.round((current.getTime() - previous.getTime()) / 86400000)
        if (days === 7) {
          warnings.push(`${employee.name}: pracuje 2 weekendy pod rzad (${anchors[index - 1]} i ${anchors[index]}).`)
          break
        }
      }
    }
    return warnings
  }, [employeeById, resolvedEmployees, visibleAssignments])

  const hoursByEmployee = useMemo(() => {
    const map = new Map<number, number>()
    for (const assignment of visibleAssignments) {
      map.set(assignment.employeeId, (map.get(assignment.employeeId) || 0) + assignment.durationMinutes)
    }
    return map
  }, [visibleAssignments])

  const loadFromBackend = async () => {
    setBackendError('')
    setBackendInfo('')
    try {
      const loadedAssignments: Assignment[] = []
      let loadedId = 1
      const dateFrom = dayKeys[0]
      const dateTo = dayKeys[dayKeys.length - 1]
      if (!dateFrom || !dateTo) {
        setAssignments([])
        setNextId(1)
        return
      }

      for (const employee of resolvedEmployees) {
        const params = new URLSearchParams({ date_from: dateFrom, date_to: dateTo })
        const res = await api.get<Array<{ work_date: string; time_from: string; time_to: string }>>(
          `/booking/staff/${employee.id}/monthly-schedule?${params.toString()}`,
        )
        const rows = res.data || []
        for (const row of rows) {
          const dateKey = String(row.work_date).slice(0, 10)
          if (!dayKeys.includes(dateKey)) continue
          const startMinutes = timeToMinutes((row.time_from || '').slice(0, 5))
          const endMinutes = timeToMinutes((row.time_to || '').slice(0, 5))
          const durationMinutes = Math.max(30, endMinutes - startMinutes)
          loadedAssignments.push({
            id: loadedId,
            employeeId: employee.id,
            dateKey,
            startMinutes,
            durationMinutes,
          })
          loadedId += 1
        }
      }
      setAssignments(loadedAssignments)
      setNextId(loadedId)
      setBackendInfo('Wczytano aktualny grafik miesieczny z backendu dla widocznego okresu.')
    } catch (err: any) {
      setBackendError(err?.response?.data?.detail || 'Nie udalo sie wczytac grafiku z backendu.')
    }
  }

  const saveAsOfficialSchedule = async () => {
    setBackendError('')
    setBackendInfo('')
    try {
      const byStaff = new Map<number, Array<{ workDate: string; timeFrom: string; timeTo: string }>>()
      const dedupe = new Set<string>()
      const dateFrom = dayKeys[0]
      const dateTo = dayKeys[dayKeys.length - 1]
      if (!dateFrom || !dateTo) {
        throw new Error('Brak zakresu dat do zapisu.')
      }

      for (const assignment of visibleAssignments) {
        const startMinutes = Math.max(0, assignment.startMinutes)
        const endMinutes = Math.min(DAY_MINUTES, assignment.startMinutes + assignment.durationMinutes)
        if (endMinutes <= startMinutes) continue
        const slot = {
          workDate: assignment.dateKey,
          timeFrom: minutesToTime(startMinutes),
          timeTo: minutesToTime(endMinutes),
        }
        const dedupeKey = `${assignment.employeeId}|${slot.workDate}|${slot.timeFrom}|${slot.timeTo}`
        if (dedupe.has(dedupeKey)) continue
        dedupe.add(dedupeKey)
        const list = byStaff.get(assignment.employeeId) || []
        list.push(slot)
        byStaff.set(assignment.employeeId, list)
      }

      for (const employee of resolvedEmployees) {
        const employeeSlots = byStaff.get(employee.id) || []
        if (employeeSlots.length > 0 && !employee.salonId) {
          throw new Error(`Brak salonu glownego dla pracownika ${employee.name}.`)
        }

        await api.put(`/booking/staff/${employee.id}/monthly-schedule`, {
          date_from: dateFrom,
          date_to: dateTo,
          entries: employeeSlots.map((slot) => ({
            salon_id: employee.salonId,
            work_date: slot.workDate,
            time_from: slot.timeFrom,
            time_to: slot.timeTo,
            is_active: true,
          })),
        })
      }
      setBackendInfo('Grafik zapisany jako obowiazujacy (miesieczny/datowany).')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setBackendError(detail || err?.message || 'Nie udalo sie zapisac grafiku.')
    }
  }

  useImperativeHandle(ref, () => ({
    loadFromBackend,
    saveAsOfficialSchedule,
  }), [loadFromBackend, saveAsOfficialSchedule])

  useEffect(() => {
    if (!autoLoadOnMount) return
    void loadFromBackend()
  }, [autoLoadOnMount])

  const handleDropOnDay = (event: DragEvent, dateKey: string) => {
    event.preventDefault()
    const payload = dragPayload(event)
    if (!payload) return

    if (payload.startsWith('employee:')) {
      const employeeId = Number(payload.replace('employee:', ''))
      if (!employeeById.has(employeeId)) return
      setAssignments((previous) => [...previous, {
        id: nextId,
        employeeId,
        dateKey,
        startMinutes: DEFAULT_START,
        durationMinutes: DEFAULT_DURATION,
      }])
      setNextId((previous) => previous + 1)
      return
    }

    if (payload.startsWith('assignment:')) {
      const assignmentId = Number(payload.replace('assignment:', ''))
      setAssignments((previous) => {
        const dragged = previous.find((item) => item.id === assignmentId)
        if (!dragged) return previous
        if (event.shiftKey) {
          return previous.map((item) => (item.id === assignmentId ? { ...item, dateKey } : item))
        }
        return [...previous, { ...dragged, id: nextId, dateKey }]
      })
      if (!event.shiftKey) {
        setNextId((previous) => previous + 1)
      }
    }
  }

  const saveAssignment = () => {
    if (!selectedAssignment) return
    const durationMinutes = Math.max(30, Math.round(Number(editDurationHours || 0) * 60))
    const startMinutes = timeToMinutes(editStart)
    const correctedDuration = Math.min(durationMinutes, DAY_MINUTES - startMinutes)
    setAssignments((previous) => previous.map((item) => (
      item.id === selectedAssignment.id
        ? { ...item, startMinutes, durationMinutes: correctedDuration }
        : item
    )))
    setSelectedAssignmentId(null)
  }

  const removeAssignment = () => {
    if (!selectedAssignment) return
    setAssignments((previous) => previous.filter((item) => item.id !== selectedAssignment.id))
    setSelectedAssignmentId(null)
  }

  return (
    <Stack spacing={2}>
      <Card>
        <CardContent>
          <Stack spacing={1.5}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} justifyContent="space-between" alignItems={{ xs: 'stretch', md: 'center' }}>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
                <Button
                  variant={periodMode === 'month' ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setPeriodMode('month')}
                >
                  Miesiac
                </Button>
                <Button
                  variant={periodMode === 'rolling30' ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setPeriodMode('rolling30')}
                >
                  30 dni
                </Button>
              </Stack>
              <TextField
                size="small"
                type="date"
                label={periodMode === 'month' ? 'Miesiac bazowy' : 'Start 30 dni'}
                value={anchorDate}
                onChange={(event) => setAnchorDate(event.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Stack>
          </Stack>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5 }}>
            Przeciagnij ikone pracownika na dzien. Przeciagniecie bloku zmiany tworzy kopie, a Shift+przeciagnij przenosi.
          </Typography>
        </CardContent>
      </Card>

      {!!backendError && <Alert severity="error">{backendError}</Alert>}
      {!!backendInfo && <Alert severity="success">{backendInfo}</Alert>}

      {!!assignmentWarnings.length && (
        <Alert severity="warning">
          <Stack spacing={0.5}>
            {assignmentWarnings.slice(0, 6).map((warning) => <Typography key={warning} variant="body2">{warning}</Typography>)}
            {assignmentWarnings.length > 6 && (
              <Typography variant="caption">... oraz {assignmentWarnings.length - 6} kolejnych ostrzezen.</Typography>
            )}
          </Stack>
        </Alert>
      )}

      <Stack direction={{ xs: 'column', lg: 'row' }} spacing={2} alignItems="stretch">
        <Card sx={{ width: { xs: '100%', lg: 280 }, flexShrink: 0 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>Pracownicy</Typography>
            <Stack spacing={1}>
              {resolvedEmployees.map((employee) => (
                <Box
                  key={employee.id}
                  draggable
                  onDragStart={(event) => event.dataTransfer.setData('text/plain', `employee:${employee.id}`)}
                  sx={{
                    p: 1,
                    borderRadius: 1.5,
                    border: '1px solid #d3d9e2',
                    backgroundColor: '#fff',
                    cursor: 'grab',
                  }}
                >
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Box sx={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: employee.color }} />
                      <Typography variant="body2">{employee.name}</Typography>
                    </Stack>
                    <Chip size="small" label={`${((hoursByEmployee.get(employee.id) || 0) / 60).toFixed(1)}h`} />
                  </Stack>
                </Box>
              ))}
            </Stack>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1, minWidth: 0 }}>
          <CardContent sx={{ p: 1.5 }}>
            <Box sx={{ overflowX: 'auto', pb: 1 }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: `repeat(${dayKeys.length}, minmax(180px, 1fr))`, gap: 1, minWidth: dayKeys.length * 185 }}>
                {dayKeys.map((dateKey) => (
                  <Box
                    key={dateKey}
                    onDragOver={(event) => event.preventDefault()}
                    onDrop={(event) => handleDropOnDay(event, dateKey)}
                    sx={{
                      border: '1px solid #d3d9e2',
                      borderRadius: 1.5,
                      backgroundColor: isWeekend(dateKey) ? '#fff8ef' : '#f8fbff',
                      minHeight: 190,
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    <Box sx={{ px: 1, py: 0.75, borderBottom: '1px solid #d3d9e2' }}>
                      <Typography variant="caption" sx={{ fontWeight: 600 }}>{dayLabel(dateKey)}</Typography>
                    </Box>
                    <Stack spacing={0.75} sx={{ p: 1, flex: 1 }}>
                      {visibleAssignments
                        .filter((item) => item.dateKey === dateKey)
                        .sort((a, b) => a.startMinutes - b.startMinutes)
                        .map((item) => {
                          const employee = employeeById.get(item.employeeId)
                          if (!employee) return null
                          return (
                            <Box
                              key={item.id}
                              draggable
                              onDragStart={(event) => event.dataTransfer.setData('text/plain', `assignment:${item.id}`)}
                              onClick={() => setSelectedAssignmentId(item.id)}
                              sx={{
                                p: 0.8,
                                borderRadius: 1,
                                backgroundColor: employee.color,
                                color: '#fff',
                                cursor: 'pointer',
                              }}
                            >
                              <Typography variant="caption" sx={{ display: 'block', fontWeight: 700 }}>{employee.name}</Typography>
                              <Typography variant="caption">{formatRange(item.startMinutes, item.durationMinutes)}</Typography>
                            </Box>
                          )
                        })}
                    </Stack>
                  </Box>
                ))}
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Stack>

      <Dialog open={!!selectedAssignment} onClose={() => setSelectedAssignmentId(null)} fullWidth maxWidth="xs">
        <DialogTitle>Edycja zmiany</DialogTitle>
        <DialogContent>
          {selectedAssignment && (
            <Stack spacing={1.5} sx={{ pt: 1 }}>
              <Typography variant="body2">
                {employeeById.get(selectedAssignment.employeeId)?.name} | {selectedAssignment.dateKey}
              </Typography>
              <Divider />
              <TextField
                label="Start"
                type="time"
                value={editStart}
                onChange={(event) => setEditStart(event.target.value)}
                inputProps={{ step: 1800 }}
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                label="Liczba godzin"
                type="number"
                value={editDurationHours}
                onChange={(event) => setEditDurationHours(event.target.value)}
                inputProps={{ min: 0.5, max: 12, step: 0.5 }}
              />
              {Math.abs(Number(editDurationHours || 0) - 8) > 0.01 && (
                <Alert severity="info">Zmiana odbiega od standardu 8h i bedzie oznaczona jako niestandardowa.</Alert>
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button color="error" onClick={removeAssignment}>Usun</Button>
          <Button onClick={() => setSelectedAssignmentId(null)}>Anuluj</Button>
          <Button variant="contained" onClick={saveAssignment}>Zapisz</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
})

export default StaffScheduleCanvas
