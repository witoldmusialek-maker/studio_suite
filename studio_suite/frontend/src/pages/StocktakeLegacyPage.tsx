import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  CardContent,
  Checkbox,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'

import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'
import { api } from '../services/api'

type StocktakeCandidate = {
  product_id: number
  product_code: string
  product_name: string
  unit: string
  measurement_mode: 'PCS' | 'WEIGHT'
  dose_weight?: number | null
  package_weight?: number | null
}

const SALON_ORDER_CODES = ['05', '12', '02', '07'] as const

const getSalonOrderRank = (salon: { code?: string | null; name: string }) => {
  const code = (salon.code || '').trim()
  const idx = SALON_ORDER_CODES.indexOf(code as (typeof SALON_ORDER_CODES)[number])
  if (idx >= 0) return idx
  const normalized = salon.name.toLowerCase()
  if (normalized.includes('pulaw')) return 0
  if (normalized.includes('kras')) return 1
  if (normalized.includes('odyn')) return 2
  return 99
}

const sortSalonsPreferred = <T extends { code?: string | null; name: string }>(rows: T[]) =>
  [...rows].sort((left, right) => {
    const rankDiff = getSalonOrderRank(left) - getSalonOrderRank(right)
    if (rankDiff !== 0) return rankDiff
    return left.name.localeCompare(right.name, 'pl')
  })

const StocktakeLegacyPage = () => {
  const { user } = useAuth()
  const { salons } = useBooking()

  const orderedSalons = useMemo(() => sortSalonsPreferred(salons), [salons])
  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')
  const [candidates, setCandidates] = useState<StocktakeCandidate[]>([])
  const [search, setSearch] = useState('')
  const [values, setValues] = useState<Record<number, string>>({})
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importApplyStockLevels, setImportApplyStockLevels] = useState(true)
  const [importingArchive, setImportingArchive] = useState(false)

  const canUseStocktake = ['admin', 'manager', 'manager_main', 'manager_salon', 'receptionist'].includes(user?.role || '')
  const isReceptionist = user?.role === 'receptionist'
  const isAdmin = user?.role === 'admin'

  useEffect(() => {
    if (selectedSalonId !== '' || !orderedSalons.length) return
    const nextSalonId =
      orderedSalons.find((salon) => user?.assigned_salon_ids?.includes(salon.id))?.id ?? orderedSalons[0].id
    setSelectedSalonId(nextSalonId)
  }, [orderedSalons, selectedSalonId, user?.assigned_salon_ids])

  useEffect(() => {
    if (selectedSalonId === '') return
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const candidatesRes = await api.get<StocktakeCandidate[]>('/inventory/stocktake-candidates', { params: { salon_id: selectedSalonId } })
        setCandidates(candidatesRes.data || [])
        setValues({})
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Nie udalo sie pobrac danych remanentu legacy.')
      } finally {
        setLoading(false)
      }
    }
    load().catch(() => undefined)
  }, [selectedSalonId])

  const filteredCandidates = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return candidates
    return candidates.filter((item) => item.product_code.toLowerCase().includes(q) || item.product_name.toLowerCase().includes(q))
  }, [candidates, search])

  const filledCount = useMemo(
    () => candidates.filter((candidate) => (values[candidate.product_id] || '').trim().length > 0).length,
    [candidates, values],
  )

  const pendingCount = Math.max(candidates.length - filledCount, 0)

  const saveLegacyStocktake = async () => {
    if (selectedSalonId === '') {
      setError('Wybierz salon remanentu.')
      return
    }
    const lines = candidates
      .map((candidate) => {
        const raw = (values[candidate.product_id] || '').trim()
        if (!raw) return null
        const parsed = Number(raw.replace(',', '.'))
        if (!Number.isFinite(parsed) || parsed < 0) return null
        if (candidate.measurement_mode === 'WEIGHT') {
          return {
            product_id: candidate.product_id,
            measured_gross_weight: parsed,
            unit: 'G',
          }
        }
        return {
          product_id: candidate.product_id,
          counted_units: parsed,
          unit: 'PCS',
        }
      })
      .filter(Boolean)

    if (!lines.length) {
      setError('Uzupelnij co najmniej jedna pozycje przed zapisem.')
      return
    }

    setSaving(true)
    setError('')
    setInfo('')
    try {
      await api.post('/inventory/stock-adjustments/stocktake', {
        salon_id: selectedSalonId,
        remarks: 'Remanent legacy',
        lines,
      })
      setInfo('Remanent legacy zapisany do weryfikacji. Manager/Admin musi zatwierdzic dokument w magazynie.')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac remanentu legacy.')
    } finally {
      setSaving(false)
    }
  }

  const importLegacyArchive = async () => {
    if (!importFile) {
      setError('Wybierz plik .7z do importu.')
      return
    }
    setError('')
    setInfo('')
    setImportingArchive(true)
    try {
      const formData = new FormData()
      formData.append('archive', importFile)
      formData.append('apply_stock_levels', importApplyStockLevels ? 'true' : 'false')
      const response = await api.post('/inventory/legacy-stock/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const batchId = response.data?.import?.batch_id
      const rows = response.data?.import?.rows_imported
      setInfo(`Import zakonczony. Batch: ${batchId ?? '-'}, wiersze: ${rows ?? 0}.`)
      if (selectedSalonId !== '') {
        const candidatesRes = await api.get<StocktakeCandidate[]>('/inventory/stocktake-candidates', {
          params: { salon_id: selectedSalonId },
        })
        setCandidates(candidatesRes.data || [])
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zaimportowac archiwum.')
    } finally {
      setImportingArchive(false)
    }
  }

  if (!canUseStocktake) {
    return <Alert severity="warning">Brak uprawnien do remanentu legacy.</Alert>
  }

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1}>
        <Typography variant="h4">Remanent legacy</Typography>
        <Button variant="contained" onClick={saveLegacyStocktake} disabled={saving || loading}>
          {saving ? 'Zapisywanie...' : 'Zapisz remanent legacy'}
        </Button>
      </Stack>

      {error && <Alert severity="error">{error}</Alert>}
      {info && <Alert severity="success">{info}</Alert>}

      {isAdmin && (
        <Card>
          <CardContent>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} alignItems={{ xs: 'stretch', md: 'center' }}>
              <Button variant="outlined" component="label">
                Wybierz archiwum .7z
                <input
                  type="file"
                  accept=".7z"
                  hidden
                  onChange={(event) => setImportFile(event.target.files?.[0] || null)}
                />
              </Button>
              <Typography variant="body2" color="text.secondary">
                {importFile ? importFile.name : 'Brak pliku'}
              </Typography>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={importApplyStockLevels}
                    onChange={(event) => setImportApplyStockLevels(event.target.checked)}
                  />
                }
                label="Po imporcie przepisz stany z najnowszego rem_table"
              />
              <Button variant="contained" onClick={importLegacyArchive} disabled={importingArchive || !importFile}>
                {importingArchive ? 'Import...' : 'Importuj archiwum'}
              </Button>
            </Stack>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
            {!isReceptionist && (
              <FormControl size="small" sx={{ minWidth: 260 }}>
                <InputLabel>Salon</InputLabel>
                <Select
                  label="Salon"
                  value={selectedSalonId}
                  onChange={(event) => setSelectedSalonId(event.target.value === '' ? '' : Number(event.target.value))}
                >
                  {orderedSalons.map((salon) => (
                    <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            <TextField
              size="small"
              label="Szukaj kod/nazwa"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              sx={{ flex: 1 }}
            />
          </Stack>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mt: 1 }}>
            <Typography variant="body2" color="text.secondary">Pozycji lacznie: {candidates.length}</Typography>
            <Typography variant="body2" color="text.secondary">Wpisane: {filledCount}</Typography>
            <Typography variant="body2" color="text.secondary">Oczekuje: {pendingCount}</Typography>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Kod</TableCell>
                <TableCell>Produkt</TableCell>
                <TableCell>Tryb</TableCell>
                <TableCell>Podpowiedz</TableCell>
                <TableCell>Wpisana ilosc</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredCandidates.map((row) => (
                <TableRow key={`legacy-${row.product_id}`}>
                  <TableCell>{row.product_code}</TableCell>
                  <TableCell>{row.product_name}</TableCell>
                  <TableCell>{row.measurement_mode === 'WEIGHT' ? 'WAGA' : 'SZTUKI'}</TableCell>
                  <TableCell>
                    {row.measurement_mode === 'WEIGHT'
                      ? `Waga brutto (g), tara: ${row.package_weight ?? '-'} g, doza: ${row.dose_weight ?? '-'} g`
                      : 'Sztuki (opak./szt.)'}
                  </TableCell>
                  <TableCell>
                    <TextField
                      size="small"
                      value={values[row.product_id] || ''}
                      onChange={(event) => {
                        setValues((prev) => ({
                          ...prev,
                          [row.product_id]: event.target.value,
                        }))
                      }}
                      placeholder={row.measurement_mode === 'WEIGHT' ? 'np. 845.5' : 'np. 3'}
                    />
                  </TableCell>
                </TableRow>
              ))}
              {!filteredCandidates.length && (
                <TableRow>
                  <TableCell colSpan={5}>Brak pozycji do wyswietlenia.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Stack>
  )
}

export default StocktakeLegacyPage
