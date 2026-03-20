import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert,
  Autocomplete,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableContainer,
  TextField,
  Typography,
} from '@mui/material'
import { Delete, Edit, PersonAdd, AddBusiness, Storefront, CalendarMonth, ViewWeek } from '@mui/icons-material'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import StaffScheduleCanvas, { type StaffScheduleCanvasEmployee, type StaffScheduleCanvasHandle } from '../components/StaffScheduleCanvas'

type Salon = { id: number; code: string; name: string; is_active: boolean }
type StaffFunction = { id: number; code: string; name: string }
type StaffMember = {
  id: number
  display_name: string
  salon_id?: number | null
  salon_name?: string | null
  role_id?: number | null
  role_name?: string | null
  user_id?: number | null
  login_username?: string | null
  login_role?: string | null
  is_active: boolean
  legacy_code?: string | null
  public_bio?: string | null
  public_photo_url?: string | null
  public_photo_preview_url?: string | null
  public_photo_has_blob?: boolean
}
type BundleOfferRow = {
  bundle_id: number
  bundle_code: string
  bundle_name: string
  priority: number
  is_active: boolean
}
type CatalogBundleRow = {
  bundle_id: number
  bundle_code: string
  bundle_name: string
}

type LoginUser = {
  id: number
  username: string
  role: 'admin' | 'manager' | 'manager_main' | 'manager_salon' | 'employee' | 'receptionist'
  linked_staff_id?: number | null
}

type LoginUserOption = LoginUser & { detach?: boolean }

type StaffSortBy = 'name' | 'salon' | 'function' | 'active'
type StaffScheduleRead = {
  id: number
  staff_id: number
  salon_id: number
  work_date: string
  time_from: string
  time_to: string
  is_active: boolean
}
type StaffScheduleDraft = {
  work_date: string
  label: string
  salon_id: number | null
  time_from: string
  time_to: string
  is_active: boolean
}

const PREFERRED_SALON_CODE_ORDER: Record<string, number> = {
  '05': 0, // Pulawska
  '12': 1, // Krasinskiego
  '07': 2, // Odynca
}

const sortSalonsPreferred = (rows: Salon[]) =>
  [...rows].sort((a, b) => {
    const aRank = PREFERRED_SALON_CODE_ORDER[(a.code || '').trim()] ?? 999
    const bRank = PREFERRED_SALON_CODE_ORDER[(b.code || '').trim()] ?? 999
    if (aRank !== bRank) return aRank - bRank
    return a.name.localeCompare(b.name)
  })

const normalizeTime = (value?: string | null) => (value || '').slice(0, 5) || '08:00'
const formatDateOnly = (value: Date) => value.toISOString().slice(0, 10)
const parseDateOnly = (value: string) => new Date(`${value}T00:00:00`)
const addDays = (value: Date, days: number) => {
  const next = new Date(value)
  next.setDate(next.getDate() + days)
  return next
}
const startOfIsoWeek = (value: Date) => {
  const dayIndex = (value.getDay() + 6) % 7
  return addDays(value, -dayIndex)
}
const formatScheduleLabel = (dateKey: string) =>
  parseDateOnly(dateKey).toLocaleDateString('pl-PL', { weekday: 'long', day: '2-digit', month: '2-digit' })

const getDisplayedStaffRoleName = (row: StaffMember) => {
  if ((row.login_role || '').toLowerCase() === 'manager_main') {
    return 'Manager glowny'
  }
  return row.role_name || '-'
}

const isManagerControlRow = (row: StaffMember) => {
  const role = (row.login_role || '').toLowerCase()
  return role === 'manager_main' || role === 'manager_salon'
}

const GroupsPage = () => {
  const { user } = useAuth()
  const [salons, setSalons] = useState<Salon[]>([])
  const [functions, setFunctions] = useState<StaffFunction[]>([])
  const [staff, setStaff] = useState<StaffMember[]>([])
  const [assignableUsers, setAssignableUsers] = useState<LoginUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  const [staffSearch, setStaffSearch] = useState('')
  const [staffSalonFilter, setStaffSalonFilter] = useState<number | ''>('')
  const [staffFunctionFilter, setStaffFunctionFilter] = useState<number | ''>('')
  const [staffActiveFilter, setStaffActiveFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [staffSortBy, setStaffSortBy] = useState<StaffSortBy>('name')
  const [staffSortDir, setStaffSortDir] = useState<'asc' | 'desc'>('asc')

  const [salonActiveFilter, setSalonActiveFilter] = useState<'all' | 'active' | 'inactive'>('all')

  const [salonOpen, setSalonOpen] = useState(false)
  const [editingSalon, setEditingSalon] = useState<Salon | null>(null)
  const [salonCode, setSalonCode] = useState('')
  const [salonName, setSalonName] = useState('')
  const [salonActive, setSalonActive] = useState(true)

  const [staffOpen, setStaffOpen] = useState(false)
  const [editingStaff, setEditingStaff] = useState<StaffMember | null>(null)
  const [staffName, setStaffName] = useState('')
  const [staffLegacyCode, setStaffLegacyCode] = useState('')
  const [staffPublicBio, setStaffPublicBio] = useState('')
  const [staffPublicPhotoUrl, setStaffPublicPhotoUrl] = useState('')
  const [staffPhotoFile, setStaffPhotoFile] = useState<File | null>(null)
  const [removeStaffPhotoBlob, setRemoveStaffPhotoBlob] = useState(false)
  const [staffSalonId, setStaffSalonId] = useState<number | ''>('')
  const [staffRoleId, setStaffRoleId] = useState<number | ''>('')
  const [staffUserId, setStaffUserId] = useState<number | ''>('')
  const [staffActive, setStaffActive] = useState(true)
  const [staffLocationsOpen, setStaffLocationsOpen] = useState(false)
  const [selectedStaffForLocations, setSelectedStaffForLocations] = useState<StaffMember | null>(null)
  const [selectedLocationSalonIds, setSelectedLocationSalonIds] = useState<number[]>([])
  const [staffBundlesOpen, setStaffBundlesOpen] = useState(false)
  const [selectedStaffForBundles, setSelectedStaffForBundles] = useState<StaffMember | null>(null)
  const [catalogBundles, setCatalogBundles] = useState<CatalogBundleRow[]>([])
  const [selectedBundleIds, setSelectedBundleIds] = useState<number[]>([])
  const [bundlePriorityById, setBundlePriorityById] = useState<Record<number, number>>({})
  const [quickUserOpen, setQuickUserOpen] = useState(false)
  const [quickUsername, setQuickUsername] = useState('')
  const [quickPassword, setQuickPassword] = useState('')
  const [quickRole, setQuickRole] = useState<'employee' | 'receptionist'>('receptionist')
  const [staffScheduleOpen, setStaffScheduleOpen] = useState(false)
  const [staffPlannerOpen, setStaffPlannerOpen] = useState(false)
  const [plannerSaving, setPlannerSaving] = useState(false)
  const [selectedStaffForSchedule, setSelectedStaffForSchedule] = useState<StaffMember | null>(null)
  const [scheduleDraftRows, setScheduleDraftRows] = useState<StaffScheduleDraft[]>([])
  const [scheduleRangeStart, setScheduleRangeStart] = useState(formatDateOnly(startOfIsoWeek(new Date())))
  const staffPlannerRef = useRef<StaffScheduleCanvasHandle | null>(null)
  const canManageOffersAndSchedule = user?.role === 'admin' || user?.role === 'manager_main'

  const loadData = async () => {
    setLoading(true)
    setError('')
    try {
      const [salonsRes, functionsRes, staffRes] = await Promise.all([
        api.get<Salon[]>('/resources/salons'),
        api.get<StaffFunction[]>('/resources/functions'),
        api.get<StaffMember[]>('/resources/staff'),
      ])
      setSalons(salonsRes.data || [])
      setFunctions(functionsRes.data || [])
      setStaff(staffRes.data || [])
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac danych zasobow.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const filteredSalons = useMemo(() => {
    return sortSalonsPreferred(
      salons
      .filter((s) => {
        if (salonActiveFilter === 'active' && !s.is_active) return false
        if (salonActiveFilter === 'inactive' && s.is_active) return false
        return true
      })
    )
  }, [salons, salonActiveFilter])

  const orderedSalons = useMemo(() => sortSalonsPreferred(salons), [salons])

  const filteredStaff = useMemo(() => {
    const q = staffSearch.trim().toLowerCase()
    let rows = staff.filter((row) => {
      if (staffSalonFilter !== '' && row.salon_id !== staffSalonFilter) return false
      if (staffFunctionFilter !== '' && row.role_id !== staffFunctionFilter) return false
      if (staffActiveFilter === 'active' && !row.is_active) return false
      if (staffActiveFilter === 'inactive' && row.is_active) return false
      if (!q) return true
      return (
        row.display_name.toLowerCase().includes(q) ||
        (row.legacy_code || '').toLowerCase().includes(q) ||
        (row.salon_name || '').toLowerCase().includes(q) ||
        (row.role_name || '').toLowerCase().includes(q)
      )
    })

    rows = [...rows].sort((a, b) => {
      const dir = staffSortDir === 'asc' ? 1 : -1
      if (staffSortBy === 'active') {
        return (Number(a.is_active) - Number(b.is_active)) * dir
      }
      if (staffSortBy === 'salon') {
        return (a.salon_name || '').localeCompare(b.salon_name || '') * dir
      }
      if (staffSortBy === 'function') {
        return (a.role_name || '').localeCompare(b.role_name || '') * dir
      }
      return (a.display_name || '').localeCompare(b.display_name || '') * dir
    })
    return rows
  }, [
    staff,
    staffSearch,
    staffSalonFilter,
    staffFunctionFilter,
    staffActiveFilter,
    staffSortBy,
    staffSortDir,
  ])

  const plannerEmployees = useMemo<StaffScheduleCanvasEmployee[]>(
    () =>
      filteredStaff
        .filter((row) => row.is_active && !isManagerControlRow(row))
        .map((row) => ({ id: row.id, name: row.display_name, salonId: row.salon_id ?? null })),
    [filteredStaff],
  )

  const staffPhotoPreviewUrl = useMemo(() => {
    if (!staffPhotoFile) return null
    return URL.createObjectURL(staffPhotoFile)
  }, [staffPhotoFile])

  useEffect(() => {
    return () => {
      if (staffPhotoPreviewUrl) URL.revokeObjectURL(staffPhotoPreviewUrl)
    }
  }, [staffPhotoPreviewUrl])

  const loadAssignableUsers = async (targetStaffId?: number | null) => {
    const params = new URLSearchParams()
    params.set('role', 'receptionist,employee,manager')
    params.set('available', 'true')
    if (targetStaffId) {
      params.set('staff_id', String(targetStaffId))
    }
    const res = await api.get<LoginUser[]>(`/auth/users?${params.toString()}`)
    const rows = res.data || []
    console.log('Lista zaladowanych kont:', rows.map((user) => `${user.username} - ${user.role}`))
    setAssignableUsers(rows)
  }

  const loginOptions: LoginUserOption[] = useMemo(
    () => [{ id: -1, username: 'Brak', role: 'employee', detach: true }, ...assignableUsers],
    [assignableUsers],
  )

  const openCreateSalon = () => {
    setEditingSalon(null)
    setSalonCode('')
    setSalonName('')
    setSalonActive(true)
    setSalonOpen(true)
  }

  const openEditSalon = (row: Salon) => {
    setEditingSalon(row)
    setSalonCode(row.code)
    setSalonName(row.name)
    setSalonActive(row.is_active)
    setSalonOpen(true)
  }

  const saveSalon = async () => {
    setError('')
    setInfo('')
    try {
      if (editingSalon) {
        await api.patch(`/resources/salons/${editingSalon.id}`, {
          code: salonCode.trim(),
          name: salonName.trim(),
          is_active: salonActive,
        })
        setInfo('Salon zaktualizowany.')
      } else {
        await api.post('/resources/salons', {
          code: salonCode.trim(),
          name: salonName.trim(),
          is_active: salonActive,
        })
        setInfo('Salon dodany.')
      }
      setSalonOpen(false)
      await loadData()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac salonu.')
    }
  }

  const removeSalon = async (row: Salon) => {
    if (!window.confirm(`Usunac salon ${row.name}?`)) return
    setError('')
    setInfo('')
    try {
      await api.delete(`/resources/salons/${row.id}`)
      setInfo('Salon usuniety.')
      await loadData()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie usunac salonu.')
    }
  }

  const openCreateStaff = () => {
    setEditingStaff(null)
    setStaffName('')
    setStaffLegacyCode('')
    setStaffPublicBio('')
    setStaffPublicPhotoUrl('')
    setStaffPhotoFile(null)
    setRemoveStaffPhotoBlob(false)
    setStaffSalonId('')
    setStaffRoleId('')
    setStaffUserId('')
    setStaffActive(true)
    setStaffOpen(true)
    void loadAssignableUsers()
  }

  const openEditStaff = (row: StaffMember) => {
    setEditingStaff(row)
    setStaffName(row.display_name)
    setStaffLegacyCode(row.legacy_code || '')
    setStaffPublicBio(row.public_bio || '')
    setStaffPublicPhotoUrl(row.public_photo_url || '')
    setStaffPhotoFile(null)
    setRemoveStaffPhotoBlob(false)
    setStaffSalonId(row.salon_id ?? '')
    setStaffRoleId(row.role_id ?? '')
    setStaffUserId(row.user_id ?? '')
    setStaffActive(row.is_active)
    setStaffOpen(true)
    void loadAssignableUsers(row.id)
  }

  const openQuickCreateUser = () => {
    const normalizedBase = staffName
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '.')
      .replace(/^\.+|\.+$/g, '')
    setQuickUsername(normalizedBase || 'recepcja')
    setQuickPassword('Recepcja2026!')
    setQuickRole('receptionist')
    setQuickUserOpen(true)
  }

  const createQuickUser = async () => {
    setError('')
    setInfo('')
    try {
      const res = await api.post<LoginUser>('/auth/register', {
        username: quickUsername.trim(),
        password: quickPassword,
        role: quickRole,
      })
      setStaffUserId(res.data.id)
      await loadAssignableUsers(editingStaff?.id)
      setQuickUserOpen(false)
      setInfo('Konto logowania utworzone i podpite do pracownika.')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie utworzyc konta logowania.')
    }
  }

  const saveStaff = async () => {
    setError('')
    setInfo('')
    const payload = {
      display_name: staffName.trim(),
      legacy_code: staffLegacyCode.trim() || null,
      public_bio: staffPublicBio.trim() || null,
      public_photo_url: staffPublicPhotoUrl.trim() || null,
      salon_id: staffSalonId === '' ? null : staffSalonId,
      role_id: staffRoleId === '' ? null : staffRoleId,
      user_id: staffUserId === '' ? null : staffUserId,
      is_active: staffActive,
    }
    try {
      let savedStaff: StaffMember | null = null
      if (editingStaff) {
        const res = await api.patch<StaffMember>(`/resources/staff/${editingStaff.id}`, payload)
        savedStaff = res.data
        setInfo('Pracownik zaktualizowany.')
      } else {
        const res = await api.post<StaffMember>('/resources/staff', payload)
        savedStaff = res.data
        setInfo('Pracownik dodany.')
      }
      if (savedStaff) {
        if (removeStaffPhotoBlob) {
          await api.delete(`/resources/staff/${savedStaff.id}/photo`)
        }
        if (staffPhotoFile) {
          const formData = new FormData()
          formData.append('file', staffPhotoFile)
          await api.post(`/resources/staff/${savedStaff.id}/photo`, formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          })
        }
      }
      setStaffOpen(false)
      setStaffPhotoFile(null)
      setRemoveStaffPhotoBlob(false)
      await loadData()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac pracownika.')
    }
  }

  const removeStaff = async (row: StaffMember) => {
    if (!window.confirm(`Dezaktywowac pracownika ${row.display_name}?`)) return
    setError('')
    setInfo('')
    try {
      await api.delete(`/resources/staff/${row.id}`)
      setInfo('Pracownik dezaktywowany.')
      await loadData()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie dezaktywowac pracownika.')
    }
  }

  const openStaffLocations = async (row: StaffMember) => {
    setError('')
    setInfo('')
    try {
      const res = await api.get(`/booking/staff/${row.id}/locations`)
      setSelectedStaffForLocations(row)
      setSelectedLocationSalonIds((res.data || []).map((item: any) => item.salon_id))
      setStaffLocationsOpen(true)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac przypisania salonow.')
    }
  }

  const saveStaffLocations = async () => {
    if (!selectedStaffForLocations) return
    setError('')
    setInfo('')
    try {
      const currentRes = await api.get(`/booking/staff/${selectedStaffForLocations.id}/locations`)
      const currentIds: number[] = (currentRes.data || []).map((item: any) => item.salon_id)
      const toAdd = selectedLocationSalonIds.filter((id) => !currentIds.includes(id))
      const toRemove = currentIds.filter((id) => !selectedLocationSalonIds.includes(id))

      await Promise.all([
        ...toAdd.map((salonId) =>
          api.post(`/booking/staff/${selectedStaffForLocations.id}/locations`, { salon_id: salonId }),
        ),
        ...toRemove.map((salonId) =>
          api.delete(`/booking/staff/${selectedStaffForLocations.id}/locations`, { params: { salon_id: salonId } }),
        ),
      ])

      setStaffLocationsOpen(false)
      setSelectedStaffForLocations(null)
      setInfo('Przypisanie salonow zaktualizowane.')
      await loadData()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac przypisania salonow.')
    }
  }

  const openStaffBundles = async (row: StaffMember) => {
    if (!row.salon_id) {
      setError('Pracownik nie ma przypisanego salonu glownego.')
      return
    }
    setError('')
    setInfo('')
    try {
      const [catalogRes, offersRes] = await Promise.all([
        api.get('/legacy/catalog', { params: { salon_id: row.salon_id } }),
        api.get<BundleOfferRow[]>(`/booking/staff/${row.id}/bundle-offers`),
      ])
      const bundles = (catalogRes.data?.bundles || []) as CatalogBundleRow[]
      const offers = (offersRes.data || []) as BundleOfferRow[]
      const activeIds = offers.filter((item) => item.is_active).map((item) => item.bundle_id)
      const nextPriorityById: Record<number, number> = {}
      for (const item of offers) {
        nextPriorityById[item.bundle_id] = Number(item.priority || 100)
      }
      setSelectedStaffForBundles(row)
      setCatalogBundles(bundles)
      setSelectedBundleIds(activeIds)
      setBundlePriorityById(nextPriorityById)
      setStaffBundlesOpen(true)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac przypisania forfetow.')
    }
  }

  const saveStaffBundles = async () => {
    if (!selectedStaffForBundles) return
    setError('')
    setInfo('')
    try {
      const offers = selectedBundleIds
        .map((bundleId, index) => ({
          bundle_id: bundleId,
          priority: Math.max(1, Number(bundlePriorityById[bundleId] || index + 1)),
          is_active: true,
        }))
        .sort((a, b) => a.priority - b.priority)
      await api.put(`/booking/staff/${selectedStaffForBundles.id}/bundle-offers`, { offers })
      setStaffBundlesOpen(false)
      setSelectedStaffForBundles(null)
      setInfo('Forfety pracownika zapisane.')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac forfetow pracownika.')
    }
  }

  const loadStaffScheduleRange = async (row: StaffMember, rangeStart: string) => {
    setError('')
    setInfo('')
    try {
      const start = parseDateOnly(rangeStart)
      const end = addDays(start, 13)
      const params = new URLSearchParams({
        date_from: formatDateOnly(start),
        date_to: formatDateOnly(end),
      })
      const res = await api.get<StaffScheduleRead[]>(`/booking/staff/${row.id}/monthly-schedule?${params.toString()}`)
      const scheduleRows = res.data || []
      const byDate = new Map<string, StaffScheduleRead[]>()
      for (const item of scheduleRows) {
        const workDate = String(item.work_date).slice(0, 10)
        const list = byDate.get(workDate) || []
        list.push(item)
        byDate.set(workDate, list)
      }

      const defaultSalonId = row.salon_id ?? orderedSalons[0]?.id ?? null
      const nextDraftRows: StaffScheduleDraft[] = Array.from({ length: 14 }, (_, index) => {
        const dateKey = formatDateOnly(addDays(start, index))
        const rowsForDay = (byDate.get(dateKey) || []).sort((a, b) => a.time_from.localeCompare(b.time_from))
        const first = rowsForDay[0]
        return {
          work_date: dateKey,
          label: formatScheduleLabel(dateKey),
          salon_id: first?.salon_id ?? defaultSalonId,
          time_from: normalizeTime(first?.time_from || '08:00:00'),
          time_to: normalizeTime(first?.time_to || '16:00:00'),
          is_active: Boolean(first),
        }
      })

      setScheduleDraftRows(nextDraftRows)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac grafiku pracownika.')
    }
  }

  const openStaffSchedule = async (row: StaffMember) => {
    const start = formatDateOnly(startOfIsoWeek(new Date()))
    setScheduleRangeStart(start)
    setSelectedStaffForSchedule(row)
    setStaffScheduleOpen(true)
    await loadStaffScheduleRange(row, start)
  }

  const shiftStaffScheduleRange = async (days: number) => {
    if (!selectedStaffForSchedule) return
    const nextStart = formatDateOnly(addDays(parseDateOnly(scheduleRangeStart), days))
    setScheduleRangeStart(nextStart)
    await loadStaffScheduleRange(selectedStaffForSchedule, nextStart)
  }

  const saveStaffSchedule = async () => {
    if (!selectedStaffForSchedule) return
    setError('')
    setInfo('')
    try {
      const rangeStart = parseDateOnly(scheduleRangeStart)
      const rangeEnd = addDays(rangeStart, 13)
      const entries = scheduleDraftRows
        .filter((row) => row.is_active)
        .map((row) => {
          const salonId = row.salon_id ?? selectedStaffForSchedule.salon_id ?? orderedSalons[0]?.id
          if (!salonId) return null
          return {
            salon_id: salonId,
            work_date: row.work_date,
            time_from: row.time_from,
            time_to: row.time_to,
            is_active: true,
          }
        })
        .filter((item): item is { salon_id: number; work_date: string; time_from: string; time_to: string; is_active: boolean } => item !== null)

      await api.put(`/booking/staff/${selectedStaffForSchedule.id}/monthly-schedule`, {
        date_from: formatDateOnly(rangeStart),
        date_to: formatDateOnly(rangeEnd),
        entries,
      })
      setInfo('Grafik pracownika zapisany.')
      closeStaffSchedule()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac grafiku pracownika.')
    }
  }

  const closeStaffSchedule = () => {
    setStaffScheduleOpen(false)
    setSelectedStaffForSchedule(null)
    setScheduleDraftRows([])
  }

  const savePlannerAsOfficial = async () => {
    if (!staffPlannerRef.current) return
    setPlannerSaving(true)
    try {
      await staffPlannerRef.current.saveAsOfficialSchedule()
      setStaffPlannerOpen(false)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac grafiku planera.')
      setInfo('')
    } finally {
      setPlannerSaving(false)
    }
  }

  return (
    <Box>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent='space-between' sx={{ mb: 2 }}>
        <Typography variant='h4'>Salony i zasoby</Typography>
        <Stack direction='row' spacing={1}>
          <Button variant='outlined' onClick={loadData}>Odswiez</Button>
          <Button variant='contained' startIcon={<AddBusiness />} onClick={openCreateSalon}>Dodaj salon</Button>
          <Button variant='contained' startIcon={<PersonAdd />} onClick={openCreateStaff}>Dodaj pracownika</Button>
          <Button variant='outlined' startIcon={<ViewWeek />} onClick={() => setStaffPlannerOpen(true)}>Planer grafiku</Button>
        </Stack>
      </Stack>

      {error && <Alert severity='error' sx={{ mb: 2 }}>{error}</Alert>}
      {info && <Alert severity='success' sx={{ mb: 2 }}>{info}</Alert>}

      <Stack spacing={2}>
        <Card>
          <CardContent>
            <Typography variant='h6' sx={{ mb: 1 }}>CRUD salonu</Typography>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} sx={{ mb: 1.5 }}>
              <FormControl size='small' sx={{ minWidth: 180 }}>
                <InputLabel>Aktywnosc</InputLabel>
                <Select
                  label='Aktywnosc'
                  value={salonActiveFilter}
                  onChange={(e) => setSalonActiveFilter(e.target.value as 'all' | 'active' | 'inactive')}
                >
                  <MenuItem value='all'>Wszystkie</MenuItem>
                  <MenuItem value='active'>Aktywne</MenuItem>
                  <MenuItem value='inactive'>Nieaktywne</MenuItem>
                </Select>
              </FormControl>
            </Stack>
            <TableContainer>
            <Table size='small' stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Kod</TableCell>
                  <TableCell>Nazwa</TableCell>
                  <TableCell>Aktywny</TableCell>
                  <TableCell align='right'>Akcje</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredSalons.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>{row.code}</TableCell>
                    <TableCell>{row.name}</TableCell>
                    <TableCell>{row.is_active ? 'TAK' : 'NIE'}</TableCell>
                    <TableCell align='right'>
                      <Stack direction='row' spacing={1} justifyContent='flex-end'>
                        <Button size='small' variant='outlined' startIcon={<Edit fontSize='small' />} onClick={() => openEditSalon(row)}>
                          Edytuj
                        </Button>
                        <Button size='small' variant='outlined' color='error' startIcon={<Delete fontSize='small' />} onClick={() => removeSalon(row)}>
                          Usun
                        </Button>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
                {!filteredSalons.length && !loading && (
                  <TableRow><TableCell colSpan={4}>Brak salonow</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
            </TableContainer>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant='h6' sx={{ mb: 1 }}>CRUD pracownika i przydzial do salonu</Typography>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} sx={{ mb: 1.5, flexWrap: 'wrap' }}>
              <TextField
                size='small'
                label='Szukaj pracownika'
                value={staffSearch}
                onChange={(e) => setStaffSearch(e.target.value)}
                sx={{ minWidth: 260 }}
              />
              <FormControl size='small' sx={{ minWidth: 170 }}>
                <InputLabel>Salon</InputLabel>
                <Select
                  label='Salon'
                  value={staffSalonFilter}
                  onChange={(e) => setStaffSalonFilter(e.target.value === '' ? '' : Number(e.target.value))}
                >
                  <MenuItem value=''>Wszystkie</MenuItem>
                  {orderedSalons.map((s) => (
                    <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl size='small' sx={{ minWidth: 170 }}>
                <InputLabel>Funkcja</InputLabel>
                <Select
                  label='Funkcja'
                  value={staffFunctionFilter}
                  onChange={(e) => setStaffFunctionFilter(e.target.value === '' ? '' : Number(e.target.value))}
                >
                  <MenuItem value=''>Wszystkie</MenuItem>
                  {functions.map((f) => (
                    <MenuItem key={f.id} value={f.id}>{f.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl size='small' sx={{ minWidth: 150 }}>
                <InputLabel>Aktywnosc</InputLabel>
                <Select
                  label='Aktywnosc'
                  value={staffActiveFilter}
                  onChange={(e) => setStaffActiveFilter(e.target.value as 'all' | 'active' | 'inactive')}
                >
                  <MenuItem value='all'>Wszystkie</MenuItem>
                  <MenuItem value='active'>Aktywni</MenuItem>
                  <MenuItem value='inactive'>Nieaktywni</MenuItem>
                </Select>
              </FormControl>
              <FormControl size='small' sx={{ minWidth: 140 }}>
                <InputLabel>Sortuj</InputLabel>
                <Select
                  label='Sortuj'
                  value={staffSortBy}
                  onChange={(e) => setStaffSortBy(e.target.value as StaffSortBy)}
                >
                  <MenuItem value='name'>Nazwa</MenuItem>
                  <MenuItem value='salon'>Salon</MenuItem>
                  <MenuItem value='function'>Funkcja</MenuItem>
                  <MenuItem value='active'>Aktywnosc</MenuItem>
                </Select>
              </FormControl>
              <FormControl size='small' sx={{ minWidth: 110 }}>
                <InputLabel>Kierunek</InputLabel>
                <Select
                  label='Kierunek'
                  value={staffSortDir}
                  onChange={(e) => setStaffSortDir(e.target.value as 'asc' | 'desc')}
                >
                  <MenuItem value='asc'>Rosnaco</MenuItem>
                  <MenuItem value='desc'>Malejaco</MenuItem>
                </Select>
              </FormControl>
            </Stack>
            <TableContainer>
            <Table size='small' stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Kod</TableCell>
                  <TableCell>Pracownik</TableCell>
                  <TableCell>Konto logowania</TableCell>
                  <TableCell>Funkcja</TableCell>
                  <TableCell>Salony</TableCell>
                  {canManageOffersAndSchedule && <TableCell>Forfety</TableCell>}
                  {canManageOffersAndSchedule && <TableCell>Grafik</TableCell>}
                  <TableCell>Aktywny</TableCell>
                  <TableCell align='right'>Akcje</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredStaff.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>{row.legacy_code || '-'}</TableCell>
                    <TableCell>{row.display_name}</TableCell>
                    <TableCell>{row.login_username || '-'}</TableCell>
                    <TableCell>{getDisplayedStaffRoleName(row)}</TableCell>
                    <TableCell>
                      <Button
                        size='small'
                        startIcon={<Storefront />}
                        onClick={() => openStaffLocations(row)}
                      >
                        Salony
                      </Button>
                    </TableCell>
                    {canManageOffersAndSchedule && (
                      <TableCell>
                        {isManagerControlRow(row) ? (
                          '-'
                        ) : (
                          <Button
                            size='small'
                            variant='outlined'
                            onClick={() => openStaffBundles(row)}
                            disabled={!row.salon_id}
                          >
                            Forfety
                          </Button>
                        )}
                      </TableCell>
                    )}
                    {canManageOffersAndSchedule && (
                      <TableCell>
                        {isManagerControlRow(row) ? (
                          '-'
                        ) : (
                          <Button
                            size='small'
                            variant='outlined'
                            startIcon={<CalendarMonth />}
                            onClick={() => openStaffSchedule(row)}
                          >
                            Grafik
                          </Button>
                        )}
                      </TableCell>
                    )}
                    <TableCell>{row.is_active ? 'TAK' : 'NIE'}</TableCell>
                    <TableCell align='right'>
                      <Stack direction='row' spacing={1} justifyContent='flex-end'>
                        <Button size='small' variant='outlined' startIcon={<Edit fontSize='small' />} onClick={() => openEditStaff(row)}>
                          Edytuj
                        </Button>
                        <Button size='small' variant='outlined' color='error' startIcon={<Delete fontSize='small' />} onClick={() => removeStaff(row)}>
                          Usun
                        </Button>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
                {!filteredStaff.length && !loading && (
                  <TableRow><TableCell colSpan={canManageOffersAndSchedule ? 9 : 7}>Brak pracownikow</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Stack>

      <Dialog open={salonOpen} onClose={() => setSalonOpen(false)} fullWidth maxWidth='sm'>
        <DialogTitle>{editingSalon ? 'Edytuj salon' : 'Nowy salon'}</DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 1 }}>
            <TextField label='Kod salonu' size='small' value={salonCode} onChange={(e) => setSalonCode(e.target.value)} />
            <TextField label='Nazwa salonu' size='small' value={salonName} onChange={(e) => setSalonName(e.target.value)} />
            <Stack direction='row' alignItems='center' spacing={1}>
              <Typography variant='body2'>Aktywny</Typography>
              <Switch checked={salonActive} onChange={(_, checked) => setSalonActive(checked)} />
            </Stack>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSalonOpen(false)}>Anuluj</Button>
          <Button variant='contained' onClick={saveSalon} disabled={salonCode.trim().length === 0 || salonName.trim().length === 0}>
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={staffOpen} onClose={() => setStaffOpen(false)} fullWidth maxWidth='sm'>
        <DialogTitle>{editingStaff ? 'Edytuj pracownika' : 'Nowy pracownik'}</DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 1 }}>
            <TextField label='Imie i nazwisko / nazwa' size='small' value={staffName} onChange={(e) => setStaffName(e.target.value)} />
            <TextField label='Kod legacy (opcjonalnie)' size='small' value={staffLegacyCode} onChange={(e) => setStaffLegacyCode(e.target.value)} />
            <TextField
              label='Zdjecie do rezerwacji online (URL)'
              size='small'
              value={staffPublicPhotoUrl}
              onChange={(e) => setStaffPublicPhotoUrl(e.target.value)}
              placeholder='https://...'
            />
            <Stack direction='row' spacing={1} alignItems='center'>
              <Avatar
                src={
                  staffPhotoPreviewUrl ||
                  editingStaff?.public_photo_preview_url ||
                  staffPublicPhotoUrl ||
                  undefined
                }
                sx={{ width: 56, height: 56 }}
              >
                {(staffName || editingStaff?.display_name || '?').slice(0, 1).toUpperCase()}
              </Avatar>
              <Button variant='outlined' component='label'>
                Wgraj zdjecie
                <input
                  hidden
                  type='file'
                  accept='image/jpeg,image/png,image/webp'
                  onChange={(event) => {
                    const file = event.target.files?.[0] || null
                    setStaffPhotoFile(file)
                    if (file) setRemoveStaffPhotoBlob(false)
                  }}
                />
              </Button>
              <Typography variant='caption' color='text.secondary'>
                JPG/PNG/WEBP, max 2 MB
              </Typography>
            </Stack>
            <FormControlLabel
              control={
                <Checkbox
                  checked={removeStaffPhotoBlob}
                  onChange={(_, checked) => setRemoveStaffPhotoBlob(checked)}
                />
              }
              label='Usun zdjecie z bazy'
            />
            <TextField
              label='Bio do rezerwacji online'
              size='small'
              multiline
              minRows={3}
              value={staffPublicBio}
              onChange={(e) => setStaffPublicBio(e.target.value)}
            />
            <FormControl size='small'>
              <InputLabel>Funkcja</InputLabel>
              <Select label='Funkcja' value={staffRoleId} onChange={(e) => setStaffRoleId(e.target.value === '' ? '' : Number(e.target.value))}>
                <MenuItem value=''>Brak</MenuItem>
                {functions.map((f) => (
                  <MenuItem key={f.id} value={f.id}>{f.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <Autocomplete
              size='small'
              options={loginOptions}
              value={loginOptions.find((user) => (staffUserId === '' ? user.detach : user.id === staffUserId)) ?? null}
              onChange={(_, value) => setStaffUserId(value?.detach ? '' : (value?.id ?? ''))}
              getOptionLabel={(option) => (option.detach ? 'Brak (odpinam)' : `${option.username} - ${option.role}`)}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              noOptionsText='Brak dostepnych kont'
              renderInput={(params) => <TextField {...params} label='Konto logowania' />}
            />
            <Stack direction='row' justifyContent='flex-end'>
              <Button variant='outlined' size='small' onClick={openQuickCreateUser}>
                Utworz konto logowania
              </Button>
            </Stack>
            <FormControl size='small'>
              <InputLabel>Salon</InputLabel>
              <Select label='Salon' value={staffSalonId} onChange={(e) => setStaffSalonId(e.target.value === '' ? '' : Number(e.target.value))}>
                <MenuItem value=''>Brak</MenuItem>
                {orderedSalons.map((s) => (
                  <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <Stack direction='row' alignItems='center' spacing={1}>
              <Typography variant='body2'>Aktywny</Typography>
              <Switch checked={staffActive} onChange={(_, checked) => setStaffActive(checked)} />
            </Stack>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStaffOpen(false)}>Anuluj</Button>
          <Button variant='contained' onClick={saveStaff} disabled={staffName.trim().length === 0}>
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={staffLocationsOpen} onClose={() => setStaffLocationsOpen(false)} fullWidth maxWidth='sm'>
        <DialogTitle>
          Salony pracownika: {selectedStaffForLocations?.display_name}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={0.5} sx={{ mt: 1 }}>
            {orderedSalons.map((salon) => (
              <FormControlLabel
                key={salon.id}
                control={
                  <Checkbox
                    checked={selectedLocationSalonIds.includes(salon.id)}
                    onChange={(_, checked) =>
                      setSelectedLocationSalonIds((prev) =>
                        checked ? [...prev, salon.id] : prev.filter((id) => id !== salon.id),
                      )
                    }
                  />
                }
                label={salon.name}
              />
            ))}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStaffLocationsOpen(false)}>Anuluj</Button>
          <Button variant='contained' onClick={saveStaffLocations}>Zapisz</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={staffBundlesOpen} onClose={() => setStaffBundlesOpen(false)} fullWidth maxWidth='sm'>
        <DialogTitle>
          Forfety pracownika: {selectedStaffForBundles?.display_name}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={1} sx={{ mt: 1 }}>
            {!catalogBundles.length && (
              <Typography variant='body2' color='text.secondary'>Brak forfetow w salonie.</Typography>
            )}
            {catalogBundles.map((bundle) => (
              <Stack key={bundle.bundle_id} direction='row' spacing={1} alignItems='center'>
                <Checkbox
                  checked={selectedBundleIds.includes(bundle.bundle_id)}
                  onChange={(_, checked) =>
                    setSelectedBundleIds((prev) => {
                      if (checked) return prev.includes(bundle.bundle_id) ? prev : [...prev, bundle.bundle_id]
                      return prev.filter((id) => id !== bundle.bundle_id)
                    })
                  }
                />
                <Typography sx={{ flex: 1 }}>
                  {bundle.bundle_code} - {bundle.bundle_name}
                </Typography>
                <TextField
                  label='Priorytet'
                  size='small'
                  type='number'
                  sx={{ width: 120 }}
                  disabled={!selectedBundleIds.includes(bundle.bundle_id)}
                  value={bundlePriorityById[bundle.bundle_id] ?? 100}
                  onChange={(event) =>
                    setBundlePriorityById((prev) => ({
                      ...prev,
                      [bundle.bundle_id]: Math.max(1, Number(event.target.value || 1)),
                    }))
                  }
                  inputProps={{ min: 1 }}
                />
              </Stack>
            ))}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStaffBundlesOpen(false)}>Anuluj</Button>
          <Button variant='contained' onClick={saveStaffBundles}>Zapisz</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={staffScheduleOpen} onClose={closeStaffSchedule} fullWidth maxWidth='md'>
        <DialogTitle>
          Grafik pracownika: {selectedStaffForSchedule?.display_name}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 1 }}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ xs: 'stretch', md: 'center' }}>
              <Button variant='outlined' size='small' onClick={() => shiftStaffScheduleRange(-7)}>Poprzedni tydzien</Button>
              <TextField
                size='small'
                label='Start zakresu'
                type='date'
                value={scheduleRangeStart}
                onChange={(event) => {
                  const value = event.target.value
                  setScheduleRangeStart(value)
                  if (selectedStaffForSchedule) void loadStaffScheduleRange(selectedStaffForSchedule, value)
                }}
                InputLabelProps={{ shrink: true }}
              />
              <Button variant='outlined' size='small' onClick={() => shiftStaffScheduleRange(7)}>Nastepny tydzien</Button>
              <Typography variant='body2' color='text.secondary'>
                Zakres: {formatScheduleLabel(scheduleRangeStart)} - {formatScheduleLabel(formatDateOnly(addDays(parseDateOnly(scheduleRangeStart), 13)))}
              </Typography>
            </Stack>
            {scheduleDraftRows.map((row, index) => (
              <Stack key={row.work_date} direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ xs: 'stretch', md: 'center' }}>
                <FormControlLabel
                  sx={{ minWidth: 170 }}
                  control={
                    <Switch
                      checked={row.is_active}
                      onChange={(_, checked) =>
                        setScheduleDraftRows((prev) =>
                          prev.map((item, itemIndex) =>
                            itemIndex === index ? { ...item, is_active: checked } : item,
                          ),
                        )
                      }
                    />
                  }
                  label={row.label}
                />
                <FormControl size='small' sx={{ minWidth: 180 }}>
                  <InputLabel>Salon</InputLabel>
                  <Select
                    label='Salon'
                    value={row.salon_id ?? ''}
                    onChange={(event) =>
                      setScheduleDraftRows((prev) =>
                        prev.map((item, itemIndex) =>
                          itemIndex === index
                            ? { ...item, salon_id: event.target.value === '' ? null : Number(event.target.value) }
                            : item,
                        ),
                      )
                    }
                  >
                    {orderedSalons.map((salon) => (
                      <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <TextField
                  size='small'
                  label='Od'
                  type='time'
                  value={row.time_from}
                  onChange={(event) =>
                    setScheduleDraftRows((prev) =>
                      prev.map((item, itemIndex) =>
                        itemIndex === index ? { ...item, time_from: event.target.value } : item,
                      ),
                    )
                  }
                  InputLabelProps={{ shrink: true }}
                  disabled={!row.is_active}
                />
                <TextField
                  size='small'
                  label='Do'
                  type='time'
                  value={row.time_to}
                  onChange={(event) =>
                    setScheduleDraftRows((prev) =>
                      prev.map((item, itemIndex) =>
                        itemIndex === index ? { ...item, time_to: event.target.value } : item,
                      ),
                    )
                  }
                  InputLabelProps={{ shrink: true }}
                  disabled={!row.is_active}
                />
              </Stack>
            ))}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeStaffSchedule}>Anuluj</Button>
          <Button variant='contained' onClick={saveStaffSchedule}>Zapisz grafik</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={staffPlannerOpen} onClose={() => setStaffPlannerOpen(false)} fullWidth maxWidth='xl'>
        <DialogTitle>Planer grafiku pracownikow</DialogTitle>
        <DialogContent>
          <Stack sx={{ mt: 1 }}>
            <StaffScheduleCanvas ref={staffPlannerRef} employees={plannerEmployees} autoLoadOnMount />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStaffPlannerOpen(false)}>Anuluj</Button>
          <Button variant='contained' onClick={savePlannerAsOfficial} disabled={plannerSaving}>
            {plannerSaving ? 'Zapisywanie...' : 'Zapisz jako obowiazujacy'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={quickUserOpen} onClose={() => setQuickUserOpen(false)} fullWidth maxWidth='xs'>
        <DialogTitle>Nowe konto logowania</DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 1 }}>
            <TextField
              autoFocus
              label='Login'
              size='small'
              value={quickUsername}
              onChange={(e) => setQuickUsername(e.target.value)}
            />
            <TextField
              label='Haslo'
              size='small'
              type='text'
              value={quickPassword}
              onChange={(e) => setQuickPassword(e.target.value)}
              helperText='Min. 10 znakow, mala/duza litera, cyfra.'
            />
            <FormControl size='small'>
              <InputLabel>Rola konta</InputLabel>
              <Select
                label='Rola konta'
                value={quickRole}
                onChange={(e) => setQuickRole(e.target.value as 'employee' | 'receptionist')}
              >
                <MenuItem value='receptionist'>receptionist</MenuItem>
                <MenuItem value='employee'>employee</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setQuickUserOpen(false)}>Anuluj</Button>
          <Button
            variant='contained'
            onClick={createQuickUser}
            disabled={quickUsername.trim().length < 3 || quickPassword.length < 10}
          >
            Utworz i przypnij
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default GroupsPage
