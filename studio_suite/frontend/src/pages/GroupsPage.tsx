import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
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
  TextField,
  Typography,
} from '@mui/material'
import { Delete, Edit, PersonAdd, AddBusiness } from '@mui/icons-material'
import { api } from '../services/api'

type Salon = { id: number; code: string; name: string; is_active: boolean }
type StaffFunction = { id: number; code: string; name: string }
type StaffMember = {
  id: number
  display_name: string
  salon_id?: number | null
  salon_name?: string | null
  role_id?: number | null
  role_name?: string | null
  is_active: boolean
  legacy_code?: string | null
}

type StaffSortBy = 'name' | 'salon' | 'function' | 'active'

const GroupsPage = () => {
  const [salons, setSalons] = useState<Salon[]>([])
  const [functions, setFunctions] = useState<StaffFunction[]>([])
  const [staff, setStaff] = useState<StaffMember[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  const [staffSearch, setStaffSearch] = useState('')
  const [staffSalonFilter, setStaffSalonFilter] = useState<number | ''>('')
  const [staffFunctionFilter, setStaffFunctionFilter] = useState<number | ''>('')
  const [staffActiveFilter, setStaffActiveFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [staffSortBy, setStaffSortBy] = useState<StaffSortBy>('name')
  const [staffSortDir, setStaffSortDir] = useState<'asc' | 'desc'>('asc')

  const [salonSearch, setSalonSearch] = useState('')
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
  const [staffSalonId, setStaffSalonId] = useState<number | ''>('')
  const [staffRoleId, setStaffRoleId] = useState<number | ''>('')
  const [staffActive, setStaffActive] = useState(true)

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
    const q = salonSearch.trim().toLowerCase()
    return salons
      .filter((s) => {
        if (salonActiveFilter === 'active' && !s.is_active) return false
        if (salonActiveFilter === 'inactive' && s.is_active) return false
        if (!q) return true
        return s.code.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
      })
      .sort((a, b) => a.name.localeCompare(b.name))
  }, [salons, salonSearch, salonActiveFilter])

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
    setStaffSalonId('')
    setStaffRoleId('')
    setStaffActive(true)
    setStaffOpen(true)
  }

  const openEditStaff = (row: StaffMember) => {
    setEditingStaff(row)
    setStaffName(row.display_name)
    setStaffLegacyCode(row.legacy_code || '')
    setStaffSalonId(row.salon_id ?? '')
    setStaffRoleId(row.role_id ?? '')
    setStaffActive(row.is_active)
    setStaffOpen(true)
  }

  const saveStaff = async () => {
    setError('')
    setInfo('')
    const payload = {
      display_name: staffName.trim(),
      legacy_code: staffLegacyCode.trim() || null,
      salon_id: staffSalonId === '' ? null : staffSalonId,
      role_id: staffRoleId === '' ? null : staffRoleId,
      is_active: staffActive,
    }
    try {
      if (editingStaff) {
        await api.patch(`/resources/staff/${editingStaff.id}`, payload)
        setInfo('Pracownik zaktualizowany.')
      } else {
        await api.post('/resources/staff', payload)
        setInfo('Pracownik dodany.')
      }
      setStaffOpen(false)
      await loadData()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac pracownika.')
    }
  }

  const removeStaff = async (row: StaffMember) => {
    if (!window.confirm(`Usunac pracownika ${row.display_name}?`)) return
    setError('')
    setInfo('')
    try {
      await api.delete(`/resources/staff/${row.id}`)
      setInfo('Pracownik usuniety.')
      await loadData()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie usunac pracownika.')
    }
  }

  const quickAssignSalon = async (row: StaffMember, salonId: number | null) => {
    setError('')
    setInfo('')
    try {
      await api.patch(`/resources/staff/${row.id}`, { salon_id: salonId })
      setInfo('Przydzial pracownika do salonu zapisany.')
      await loadData()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac przydzialu salonu.')
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
        </Stack>
      </Stack>

      {error && <Alert severity='error' sx={{ mb: 2 }}>{error}</Alert>}
      {info && <Alert severity='success' sx={{ mb: 2 }}>{info}</Alert>}

      <Stack spacing={2}>
        <Card>
          <CardContent>
            <Typography variant='h6' sx={{ mb: 1 }}>CRUD salonu</Typography>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} sx={{ mb: 1.5 }}>
              <TextField
                size='small'
                label='Szukaj salonu'
                value={salonSearch}
                onChange={(e) => setSalonSearch(e.target.value)}
                sx={{ minWidth: 260 }}
              />
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
            <Table size='small'>
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
                      <IconButton size='small' onClick={() => openEditSalon(row)}><Edit fontSize='small' /></IconButton>
                      <IconButton size='small' color='error' onClick={() => removeSalon(row)}><Delete fontSize='small' /></IconButton>
                    </TableCell>
                  </TableRow>
                ))}
                {!filteredSalons.length && !loading && (
                  <TableRow><TableCell colSpan={4}>Brak salonow</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
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
                  {salons.map((s) => (
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
            <Table size='small'>
              <TableHead>
                <TableRow>
                  <TableCell>Pracownik</TableCell>
                  <TableCell>Funkcja</TableCell>
                  <TableCell>Salon</TableCell>
                  <TableCell>Aktywny</TableCell>
                  <TableCell align='right'>Akcje</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredStaff.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>{row.display_name}</TableCell>
                    <TableCell>{row.role_name || '-'}</TableCell>
                    <TableCell>
                      <FormControl size='small' sx={{ minWidth: 220 }}>
                        <InputLabel>Salon</InputLabel>
                        <Select
                          label='Salon'
                          value={row.salon_id ?? ''}
                          onChange={(e) => quickAssignSalon(row, e.target.value === '' ? null : Number(e.target.value))}
                        >
                          <MenuItem value=''>Brak</MenuItem>
                          {salons.map((s) => (
                            <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </TableCell>
                    <TableCell>{row.is_active ? 'TAK' : 'NIE'}</TableCell>
                    <TableCell align='right'>
                      <IconButton size='small' onClick={() => openEditStaff(row)}><Edit fontSize='small' /></IconButton>
                      <IconButton size='small' color='error' onClick={() => removeStaff(row)}><Delete fontSize='small' /></IconButton>
                    </TableCell>
                  </TableRow>
                ))}
                {!filteredStaff.length && !loading && (
                  <TableRow><TableCell colSpan={5}>Brak pracownikow</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
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
            <FormControl size='small'>
              <InputLabel>Funkcja</InputLabel>
              <Select label='Funkcja' value={staffRoleId} onChange={(e) => setStaffRoleId(e.target.value === '' ? '' : Number(e.target.value))}>
                <MenuItem value=''>Brak</MenuItem>
                {functions.map((f) => (
                  <MenuItem key={f.id} value={f.id}>{f.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size='small'>
              <InputLabel>Salon</InputLabel>
              <Select label='Salon' value={staffSalonId} onChange={(e) => setStaffSalonId(e.target.value === '' ? '' : Number(e.target.value))}>
                <MenuItem value=''>Brak</MenuItem>
                {salons.map((s) => (
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
    </Box>
  )
}

export default GroupsPage
