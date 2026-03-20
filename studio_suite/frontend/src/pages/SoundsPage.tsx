import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import DeleteOutline from '@mui/icons-material/DeleteOutline'
import AddCircleOutline from '@mui/icons-material/AddCircleOutline'

import { api } from '../services/api'

type ServicePriceRow = {
  service_id: number
  service_code: string
  service_name: string
  salon_id: number
  price: number
}

type BundleItemRow = {
  position: number
  service_id: number | null
  service_code: string
  service_name: string
  override_price: number | null
}

type BundleRow = {
  bundle_id: number
  salon_id: number | null
  bundle_code: string
  bundle_name: string
  price: number
  items: BundleItemRow[]
}

type SalonRow = { id: number; code: string; name: string; is_active: boolean }

type LegacySyncDiffResponse = {
  salon_id: number
  salon_code: string
  salon_name: string
  diff: {
    total: number
  }
}

type LegacySyncApplyResponse = {
  report: LegacySyncDiffResponse
  created_services: number
  updated_service_names: number
  updated_service_durations: number
  updated_service_prices: number
  created_bundles: number
  updated_bundle_names: number
  rebuilt_bundle_items: number
}

const formatPrice = (value: number) => `${value.toFixed(2)} PLN`

const SoundsPage = () => {
  const [query, setQuery] = useState('')
  const [bundles, setBundles] = useState<BundleRow[]>([])
  const [serviceRows, setServiceRows] = useState<ServicePriceRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newCode, setNewCode] = useState('')
  const [newName, setNewName] = useState('')
  const [addServiceIdByBundle, setAddServiceIdByBundle] = useState<Record<number, number>>({})
  const [salons, setSalons] = useState<SalonRow[]>([])
  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')
  const [syncDiff, setSyncDiff] = useState<LegacySyncDiffResponse | null>(null)
  const [syncBusy, setSyncBusy] = useState(false)

  const load = async (salonId: number) => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get('/legacy/catalog', { params: { salon_id: salonId } })
      setBundles((response.data.bundles || []) as BundleRow[])
      setServiceRows((response.data.service_prices || []) as ServicePriceRow[])
      try {
        const diffRes = await api.get<LegacySyncDiffResponse>('/legacy/catalog/sync/diff', { params: { salon_id: salonId } })
        setSyncDiff(diffRes.data || null)
      } catch {
        setSyncDiff(null)
      }
    } catch (err) {
      console.error(err)
      setError('Nie udalo sie pobrac cennika forfaitow z bazy.')
    } finally {
      setLoading(false)
    }
  }

  const syncFromLegacy = async () => {
    if (selectedSalonId === '') return
    setSyncBusy(true)
    setError('')
    try {
      const response = await api.post<LegacySyncApplyResponse>('/legacy/catalog/sync/apply', null, {
        params: { salon_id: selectedSalonId },
      })
      const payload = response.data
      setError('')
      await load(selectedSalonId)
      alert(
        `Synchronizacja zakonczona. Dodane uslugi: ${payload?.created_services ?? 0}, dodane forfety: ${payload?.created_bundles ?? 0}, przebudowane pozycje forfetow: ${payload?.rebuilt_bundle_items ?? 0}.`,
      )
    } catch (err: any) {
      console.error(err)
      setError(err?.response?.data?.detail || 'Nie udalo sie zsynchronizowac z legacy.')
    } finally {
      setSyncBusy(false)
    }
  }

  useEffect(() => {
    ;(async () => {
      try {
        const salonsRes = await api.get<SalonRow[]>('/resources/salons')
        const rows = salonsRes.data || []
        setSalons(rows)
        if (rows.length) {
          setSelectedSalonId(rows[0].id)
        }
      } catch (err) {
        console.error(err)
        setError('Nie udalo sie pobrac listy salonow.')
      }
    })()
  }, [])

  useEffect(() => {
    if (selectedSalonId === '') return
    load(selectedSalonId)
  }, [selectedSalonId])

  const servicePriceById = useMemo(() => new Map(serviceRows.map((row) => [row.service_id, row.price])), [serviceRows])

  const filteredBundles = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return bundles
    return bundles.filter((bundle) => `${bundle.bundle_code} ${bundle.bundle_name}`.toLowerCase().includes(q))
  }, [bundles, query])

  const updateBundleItemOverride = async (bundle: BundleRow, item: BundleItemRow, rawValue: string) => {
    if (selectedSalonId === '') return
    try {
      const normalizedValue = rawValue.trim() === '' ? null : Math.round((Number(rawValue) || 0) * 100) / 100
      await api.patch(`/legacy/catalog/bundles/${bundle.bundle_id}/items/${item.position}`, { override_price: normalizedValue })
      await load(selectedSalonId)
    } catch (err) {
      console.error(err)
      setError('Nie udalo sie zapisac ceny pozycji forfaitu.')
    }
  }

  const createBundle = async () => {
    if (!newCode.trim() || !newName.trim() || selectedSalonId === '') return
    try {
      await api.post('/legacy/catalog/bundles', {
        bundle_code: newCode.trim(),
        bundle_name: newName.trim(),
        salon_id: selectedSalonId,
      })
      setNewCode('')
      setNewName('')
      await load(selectedSalonId)
    } catch (err) {
      console.error(err)
      setError('Nie udalo sie dodac forfaitu.')
    }
  }

  const removeBundle = async (bundleId: number) => {
    if (selectedSalonId === '') return
    try {
      await api.delete(`/legacy/catalog/bundles/${bundleId}`)
      await load(selectedSalonId)
    } catch (err) {
      console.error(err)
      setError('Nie udalo sie usunac forfaitu.')
    }
  }

  const addItemToBundle = async (bundleId: number) => {
    if (selectedSalonId === '') return
    const serviceId = addServiceIdByBundle[bundleId]
    if (!serviceId) return
    try {
      await api.post(`/legacy/catalog/bundles/${bundleId}/items`, { service_id: serviceId, override_price: null })
      await load(selectedSalonId)
    } catch (err) {
      console.error(err)
      setError('Nie udalo sie dodac uslugi do forfaitu.')
    }
  }

  const removeItemFromBundle = async (bundleId: number, position: number) => {
    if (selectedSalonId === '') return
    try {
      await api.delete(`/legacy/catalog/bundles/${bundleId}/items/${position}`)
      await load(selectedSalonId)
    } catch (err) {
      console.error(err)
      setError('Nie udalo sie usunac uslugi z forfaitu.')
    }
  }

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Pakiety (forfety) - na bazie</Typography>

      <Card>
        <CardContent>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ xs: 'stretch', md: 'center' }}>
            <TextField
              select
              label="Salon"
              value={selectedSalonId}
              onChange={(event) => setSelectedSalonId(event.target.value === '' ? '' : Number(event.target.value))}
              size="small"
              sx={{ minWidth: 300 }}
            >
              {salons.map((salon) => (
                <MenuItem key={salon.id} value={salon.id}>
                  {salon.code} - {salon.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField label="Kod nowego forfaitu" value={newCode} onChange={(event) => setNewCode(event.target.value)} size="small" />
            <TextField label="Nazwa nowego forfaitu" value={newName} onChange={(event) => setNewName(event.target.value)} size="small" sx={{ minWidth: 320 }} />
            <Button variant="contained" startIcon={<AddCircleOutline />} onClick={createBundle} disabled={selectedSalonId === ''}>
              Dodaj forfait
            </Button>
            <Button
              variant="outlined"
              color={(syncDiff?.diff?.total || 0) > 0 ? 'warning' : 'success'}
              onClick={() => selectedSalonId !== '' && load(selectedSalonId)}
              disabled={selectedSalonId === '' || syncBusy}
            >
              Roznice legacy: {syncDiff?.diff?.total ?? '-'}
            </Button>
            <Button
              variant="contained"
              color="secondary"
              onClick={syncFromLegacy}
              disabled={selectedSalonId === '' || syncBusy}
            >
              {syncBusy ? 'Synchronizacja...' : 'Synchronizuj z legacy'}
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
        <TextField
          label="Szukaj pakietu (kod / nazwa)"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          size="small"
          sx={{ maxWidth: 420 }}
        />
        <Chip label={`Pakiety: ${filteredBundles.length}`} />
      </Stack>

      {error && <Alert severity="warning">{error}</Alert>}
      {loading && <CircularProgress size={28} />}

      {!loading &&
        filteredBundles.map((bundle) => {
          const sumOfLines = bundle.items.reduce((sum, item) => {
            const base = item.service_id ? servicePriceById.get(item.service_id) || 0 : 0
            return sum + (item.override_price ?? base)
          }, 0)
          return (
            <Card key={bundle.bundle_id}>
              <CardContent>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} justifyContent="space-between">
                  <Typography variant="h6">
                    {bundle.bundle_code} - {bundle.bundle_name}
                  </Typography>
                  <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                    <Chip color="success" label={`Cena forfaitu: ${formatPrice(bundle.price)}`} />
                    <Chip label={`Pozycje: ${bundle.items.length}`} />
                    <Chip label={`Suma uslug: ${formatPrice(sumOfLines)}`} />
                    <IconButton color="error" onClick={() => removeBundle(bundle.bundle_id)} title="Usun forfait">
                      <DeleteOutline />
                    </IconButton>
                  </Stack>
                </Stack>

                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} sx={{ mt: 1.5 }}>
                  <TextField
                    select
                    size="small"
                    label="Dodaj usluge do forfaitu"
                    value={addServiceIdByBundle[bundle.bundle_id] ?? ''}
                    onChange={(event) =>
                      setAddServiceIdByBundle((prev) => ({ ...prev, [bundle.bundle_id]: Number(event.target.value) }))
                    }
                    sx={{ minWidth: 360 }}
                  >
                    {serviceRows.map((service) => (
                      <MenuItem key={service.service_id} value={service.service_id}>
                        {service.service_code} - {service.service_name}
                      </MenuItem>
                    ))}
                  </TextField>
                  <Button variant="outlined" onClick={() => addItemToBundle(bundle.bundle_id)}>
                    Dodaj pozycje
                  </Button>
                </Stack>

                <Divider sx={{ my: 1.5 }} />
                <Stack spacing={1}>
                  {bundle.items.map((item) => {
                    const basePrice = item.service_id ? servicePriceById.get(item.service_id) || 0 : 0
                    return (
                      <Stack key={`${bundle.bundle_id}-${item.position}`} direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={2}>
                        <Typography variant="body2">
                          {item.position}. {item.service_code} {item.service_name}
                        </Typography>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Typography variant="body2" color="text.secondary">
                            baza {formatPrice(basePrice)}
                          </Typography>
                          <TextField
                            size="small"
                            label="Override PLN"
                            type="number"
                            inputProps={{ step: 1, min: 0 }}
                            defaultValue={item.override_price ?? ''}
                            placeholder="(brak)"
                            onFocus={(event) => event.target.select()}
                            onBlur={(event) => updateBundleItemOverride(bundle, item, event.target.value)}
                            sx={{ width: 150 }}
                          />
                          <IconButton
                            color="error"
                            onClick={() => removeItemFromBundle(bundle.bundle_id, item.position)}
                            title="Usun pozycje"
                          >
                            <DeleteOutline />
                          </IconButton>
                        </Stack>
                      </Stack>
                    )
                  })}
                </Stack>
              </CardContent>
            </Card>
          )
        })}
    </Stack>
  )
}

export default SoundsPage
