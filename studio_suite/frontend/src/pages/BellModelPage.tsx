import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { ContentCopy, Delete, Edit, FileDownload, FileUpload, Refresh } from '@mui/icons-material'
import { useRef } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../services/api'

type ServiceRow = {
  service_id: number
  service_code: string
  service_name: string
  service_segment: ServiceSegment
  salon_id: number
  price: number
  duration_minutes: number
  is_active: boolean
  is_formula: boolean
  formula_products: FormulaProductRow[]
}

type FormulaProductRow = {
  product_id: number
  product_code: string
  product_name: string
  brand?: string | null
}

type CatalogResponse = {
  service_prices: ServiceRow[]
}

type LegacySyncDiffResponse = {
  salon_id: number
  salon_code: string
  salon_name: string
  diff: {
    services_missing_in_db: number
    services_name_diff: number
    services_duration_diff: number
    services_price_diff: number
    bundles_missing_in_db: number
    bundles_name_diff: number
    bundles_price_diff: number
    bundles_items_diff: number
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

type SalonRow = { id: number; code: string; name: string; is_active: boolean }

type ServiceForm = {
  service_code: string
  service_name: string
  service_segment: ServiceSegment | ''
  duration_minutes: string
  default_price: string
  is_active: boolean
}

type ServiceSegment = 'PANI' | 'PAN' | 'ESTETYKA' | 'SPRZEDAZ'

type RecipeItemRow = {
  id: number
  service_id: number
  variant_code?: string | null
  position?: number
  product_family?: string | null
  product_id?: number | null
  product_name?: string | null
  product_label_snapshot?: string | null
  is_optional?: boolean
  is_required?: boolean
  quantity_mode?: string
  planned_quantity: number
  planned_min?: number | null
  planned_default?: number | null
  planned_max?: number | null
  unit: string
  recipe_unit_label?: string | null
  package_unit_count?: number | null
  package_unit_label?: string | null
  package_size_value?: number | null
  package_size_unit?: string | null
  inventory_mode?: string
  note?: string | null
  poj?: string | null
  iljedn?: string | null
  total_label?: string | null
}

type RecipeProductOption = {
  id: number
  code: string
  name: string
  family_code?: string | null
  brand?: string | null
}

type RecipeProductDetail = {
  id: number
  code: string
  name: string
  family_code?: string | null
  brand?: string | null
  poj?: string | null
  iljedn?: string | null
}

type RecipeFamilyOption = {
  id?: number | null
  value: string
  label: string
  product_count: number
}

const PREFERRED_SALON_CODE_ORDER: Record<string, number> = {
  '05': 0, // Pulawska
  '12': 1, // Krasinskiego
  '02': 2, // Odynca
  '07': 2, // Odynca (legacy alternate)
}

const sortSalonsPreferred = (rows: SalonRow[]) =>
  [...rows].sort((a, b) => {
    const aRank = PREFERRED_SALON_CODE_ORDER[(a.code || '').trim()] ?? 999
    const bRank = PREFERRED_SALON_CODE_ORDER[(b.code || '').trim()] ?? 999
    if (aRank !== bRank) return aRank - bRank
    return a.name.localeCompare(b.name)
  })

const emptyCreateForm: ServiceForm = {
  service_code: '',
  service_name: '',
  service_segment: '',
  duration_minutes: '0',
  default_price: '0',
  is_active: true,
}

const SERVICE_SEGMENT_OPTIONS: Array<{ value: ServiceSegment; label: string }> = [
  { value: 'PANI', label: 'Pani' },
  { value: 'PAN', label: 'Pan' },
  { value: 'ESTETYKA', label: 'Estetyka' },
  { value: 'SPRZEDAZ', label: 'Sprzedaz' },
]

const SERVICE_SEGMENT_LABELS: Record<ServiceSegment, string> = {
  PANI: 'Pani',
  PAN: 'Pan',
  ESTETYKA: 'Estetyka',
  SPRZEDAZ: 'Sprzedaz',
}

const normalizeServiceSegment = (raw: string | null | undefined, code?: string): ServiceSegment => {
  const value = (raw || '').trim().toUpperCase()
  if (value === 'PANI' || value === 'PAN' || value === 'ESTETYKA' || value === 'SPRZEDAZ') return value
  if (value === 'SPRZEDAŻ') return 'SPRZEDAZ'
  if (value === '1') return 'PANI'
  if (value === '2') return 'PAN'
  if (value === '3') return 'ESTETYKA'
  if (value === '4') return 'SPRZEDAZ'
  if (value.startsWith('PANI')) return 'PANI'
  if (value.startsWith('PAN') || value.startsWith('PATEL')) return 'PAN'
  if (value.startsWith('ESTET')) return 'ESTETYKA'
  if (value.startsWith('SPRZED')) return 'SPRZEDAZ'
  return inferServiceSegmentFromCode(code || '') || 'PANI'
}

const inferServiceSegmentFromCode = (code: string): ServiceSegment | '' => {
  const normalized = code.trim()
  if (!/^\d+$/.test(normalized)) return ''
  const numeric = Number(normalized)
  if (numeric >= 1 && numeric <= 99) return 'PANI'
  if (numeric >= 101 && numeric <= 199) return 'PAN'
  if (numeric >= 200 && numeric <= 299) return 'SPRZEDAZ'
  if (numeric >= 300 && numeric <= 399) return 'ESTETYKA'
  return ''
}

const renderHighlightedText = (text: string, query: string) => {
  const haystack = text || ''
  const needle = query.trim()
  if (!needle) return haystack
  const lowerHaystack = haystack.toLowerCase()
  const lowerNeedle = needle.toLowerCase()
  const startIndex = lowerHaystack.indexOf(lowerNeedle)
  if (startIndex < 0) return haystack
  const endIndex = startIndex + needle.length
  return (
    <>
      {haystack.slice(0, startIndex)}
      <Box component="span" sx={{ fontWeight: 700 }}>
        {haystack.slice(startIndex, endIndex)}
      </Box>
      {haystack.slice(endIndex)}
    </>
  )
}

const parsePackageLabel = (value: string) => {
  const match = value.trim().match(/^([0-9]+(?:[.,][0-9]+)?)\s*(.+)$/)
  if (!match) return { amount: null as number | null, unit: null as string | null }
  return {
    amount: Number(match[1].replace(',', '.')),
    unit: match[2].trim().toUpperCase() || null,
  }
}

const parseUnitCountLabel = (value: string) => {
  const match = value.trim().match(/^([0-9]+(?:[.,][0-9]+)?)\s*(.+)$/)
  if (!match) return { count: null as number | null, label: null as string | null }
  return {
    count: Number(match[1].replace(',', '.')),
    label: match[2].trim().toLowerCase() || null,
  }
}

const normalizeRecipeFamilyValue = (value: string) => {
  const normalized = (value || '').trim()
  if (!normalized) return ''
  const upper = normalized.toUpperCase()
  if (upper === 'ARTYKUŁY JEDNORAZOWE' || upper === 'ARTYKULY JEDNORAZOWE') return 'ARTYKULY_JEDNORAZOWE'
  return normalized
}

const QUANTITY_MODE_LABELS: Record<string, string> = {
  EXACT: 'Dokladna',
  RANGE: 'Zakres',
  ESTIMATE: 'Szacunkowa',
}

const INVENTORY_MODE_LABELS: Record<string, string> = {
  PER_SERVICE: 'Na kazdej usludze',
  BATCH_ESTIMATE: 'Szacunek zbiorczy',
  STOCKTAKE_ONLY: 'Tylko remanent',
}

const UNIT_OPTIONS = ['PCS', 'G', 'ML', 'DOZA'] as const

const getQuantityModeLabel = (mode?: string) => QUANTITY_MODE_LABELS[(mode || '').toUpperCase()] || (mode || 'Dokladna')
const getInventoryModeLabel = (mode?: string) => INVENTORY_MODE_LABELS[(mode || '').toUpperCase()] || (mode || 'Na kazdej usludze')

const isRecipeOptionalByService = (row: ServiceRow) => {
  if (row.service_segment === 'SPRZEDAZ') return true
  const numericCode = Number(row.service_code)
  return Number.isFinite(numericCode) && numericCode >= 200 && numericCode <= 299
}

const ServicesPage = () => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [exportingRecipes, setExportingRecipes] = useState(false)
  const [importingRecipes, setImportingRecipes] = useState(false)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [query, setQuery] = useState('')
  const [services, setServices] = useState<ServiceRow[]>([])
  const [priceDraftByServiceId, setPriceDraftByServiceId] = useState<Record<number, string>>({})
  const [savingPriceByServiceId, setSavingPriceByServiceId] = useState<Record<number, boolean>>({})
  const [salons, setSalons] = useState<SalonRow[]>([])
  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')
  const [syncDiff, setSyncDiff] = useState<LegacySyncDiffResponse | null>(null)
  const [syncBusy, setSyncBusy] = useState(false)

  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState<ServiceForm>(emptyCreateForm)

  const [editOpen, setEditOpen] = useState(false)
  const [editServiceId, setEditServiceId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState<ServiceForm>(emptyCreateForm)
  const [formulaOpen, setFormulaOpen] = useState(false)
  const [formulaService, setFormulaService] = useState<ServiceRow | null>(null)
  const [recipeItems, setRecipeItems] = useState<RecipeItemRow[]>([])
  const [recipeEditingId, setRecipeEditingId] = useState<number | null>(null)
  const [recipePosition, setRecipePosition] = useState('1')
  const [recipeProductFamily, setRecipeProductFamily] = useState('')
  const [recipeFamilyOptions, setRecipeFamilyOptions] = useState<RecipeFamilyOption[]>([])
  const [recipeProduct, setRecipeProduct] = useState<RecipeProductOption | null>(null)
  const [recipeProductOptions, setRecipeProductOptions] = useState<RecipeProductOption[]>([])
  const [recipeProductQuery, setRecipeProductQuery] = useState('')
  const [debouncedRecipeProductQuery, setDebouncedRecipeProductQuery] = useState('')
  const [recipeValidationError, setRecipeValidationError] = useState('')
  const [recipeQuantityMode, setRecipeQuantityMode] = useState<'EXACT' | 'RANGE' | 'ESTIMATE'>('EXACT')
  const [recipeQuantity, setRecipeQuantity] = useState('1')
  const [recipePlannedMin, setRecipePlannedMin] = useState('')
  const [recipePlannedDefault, setRecipePlannedDefault] = useState('1')
  const [recipePlannedMax, setRecipePlannedMax] = useState('')
  const [recipeUnit, setRecipeUnit] = useState('PCS')
  const [recipeNote, setRecipeNote] = useState('')
  const [recipePackageLabel, setRecipePackageLabel] = useState('')
  const [recipeUnitLabel, setRecipeUnitLabel] = useState('szt')
  const [recipeIsRequired, setRecipeIsRequired] = useState(true)
  const [recipeInventoryMode, setRecipeInventoryMode] = useState<'PER_SERVICE' | 'BATCH_ESTIMATE' | 'STOCKTAKE_ONLY'>('PER_SERVICE')
  const [recipeEditingOptional, setRecipeEditingOptional] = useState(false)
  const [recipeIsOptional, setRecipeIsOptional] = useState(false)
  const [recipeOptionalFamily, setRecipeOptionalFamily] = useState('ARTYKULY_JEDNORAZOWE')
  const [recipeOptionalFamilyOptions, setRecipeOptionalFamilyOptions] = useState<RecipeFamilyOption[]>([])
  const [recipeOptionalProduct, setRecipeOptionalProduct] = useState<RecipeProductOption | null>(null)
  const [recipeOptionalProductOptions, setRecipeOptionalProductOptions] = useState<RecipeProductOption[]>([])
  const [recipeOptionalProductQuery, setRecipeOptionalProductQuery] = useState('')
  const [debouncedRecipeOptionalProductQuery, setDebouncedRecipeOptionalProductQuery] = useState('')
  const recipeImportInputRef = useRef<HTMLInputElement | null>(null)

  const canEditRecipe = ['admin', 'manager', 'manager_main', 'manager_salon'].includes(user?.role || '')
  const selectedRecipeFamilyOption = useMemo(
    () => recipeFamilyOptions.find((family) => family.value === recipeProductFamily) || null,
    [recipeFamilyOptions, recipeProductFamily],
  )
  const selectedOptionalFamilyOption = useMemo(
    () => recipeOptionalFamilyOptions.find((family) => family.value === recipeOptionalFamily) || null,
    [recipeOptionalFamilyOptions, recipeOptionalFamily],
  )

  const closeFormulaDialog = () => {
    setFormulaOpen(false)
    setFormulaService(null)
    setRecipeItems([])
    setRecipeValidationError('')
    setRecipeEditingId(null)
    setRecipeProduct(null)
    setRecipeProductOptions([])
    setRecipeProductQuery('')
    setDebouncedRecipeProductQuery('')
    setRecipeOptionalProduct(null)
    setRecipeOptionalProductOptions([])
    setRecipeOptionalProductQuery('')
    setDebouncedRecipeOptionalProductQuery('')
  }

  const loadRecipeFamilyOptions = async () => {
    const res = await api.get<RecipeFamilyOption[]>('/colors/families', {
      params: { backbar: true },
    })
    const rows = res.data || []
    setRecipeFamilyOptions(rows)
    setRecipeOptionalFamilyOptions(rows)
  }

  const loadSalons = async () => {
    const res = await api.get<SalonRow[]>('/resources/salons')
    const rows = sortSalonsPreferred(res.data || [])
    setSalons(rows)
    if (selectedSalonId === '' && rows.length) {
      const preferredSalonId = rows.find((salon) => user?.assigned_salon_ids?.includes(salon.id))?.id ?? rows[0].id
      setSelectedSalonId(preferredSalonId)
    }
  }

  const loadCatalog = async (salonId: number) => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get<CatalogResponse>('/legacy/catalog', { params: { salon_id: salonId } })
      const rows = [...(res.data?.service_prices || [])]
        .map((row) => ({
          ...row,
          service_segment: normalizeServiceSegment((row as any).service_segment, row.service_code),
        }))
        .sort((a, b) => a.service_code.localeCompare(b.service_code))
      setServices(rows)
      setPriceDraftByServiceId(
        rows.reduce<Record<number, string>>((acc, row) => {
          acc[row.service_id] = String(Number(row.price).toFixed(2))
          return acc
        }, {})
      )
      try {
        const diffRes = await api.get<LegacySyncDiffResponse>('/legacy/catalog/sync/diff', { params: { salon_id: salonId } })
        setSyncDiff(diffRes.data || null)
      } catch {
        setSyncDiff(null)
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac cennika uslug.')
    } finally {
      setLoading(false)
    }
  }

  const syncFromLegacy = async () => {
    if (selectedSalonId === '') return
    setError('')
    setInfo('')
    setSyncBusy(true)
    try {
      const res = await api.post<LegacySyncApplyResponse>('/legacy/catalog/sync/apply', null, {
        params: { salon_id: selectedSalonId },
      })
      const payload = res.data
      const d = payload?.report?.diff
      setInfo(
        `Synchronizacja zakonczona. Dodane uslugi: ${payload?.created_services ?? 0}, zaktualizowane nazwy/czasy/ceny: ${payload?.updated_service_names ?? 0}/${payload?.updated_service_durations ?? 0}/${payload?.updated_service_prices ?? 0}. Pozostale roznice: ${d?.total ?? 0}.`,
      )
      await loadCatalog(selectedSalonId)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zsynchronizowac cennika z legacy.')
    } finally {
      setSyncBusy(false)
    }
  }

  useEffect(() => {
    ;(async () => {
      await loadSalons()
    })()
  }, [])

  useEffect(() => {
    if (selectedSalonId === '') return
    loadCatalog(selectedSalonId)
  }, [selectedSalonId])

  useEffect(() => {
    const inferred = inferServiceSegmentFromCode(createForm.service_code)
    if (!inferred) return
    setCreateForm((prev) => (prev.service_segment === inferred ? prev : { ...prev, service_segment: inferred }))
  }, [createForm.service_code])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return services
    return services.filter((row) => {
      return row.service_code.toLowerCase().includes(q) || row.service_name.toLowerCase().includes(q)
    })
  }, [services, query])

  const orderedSalons = useMemo(() => sortSalonsPreferred(salons), [salons])

  const openEdit = (row: ServiceRow) => {
    setEditServiceId(row.service_id)
    setEditForm({
      service_code: row.service_code,
      service_name: row.service_name,
      service_segment: normalizeServiceSegment(row.service_segment, row.service_code),
      duration_minutes: String(row.duration_minutes),
      default_price: String(row.price),
      is_active: row.is_active,
    })
    setEditOpen(true)
  }

  const createService = async () => {
    if (selectedSalonId === '') return
    setError('')
    setInfo('')
    try {
      await api.post('/legacy/catalog/services', {
        service_code: createForm.service_code.trim(),
        service_name: createForm.service_name.trim(),
        service_segment: createForm.service_segment,
        duration_minutes: Number(createForm.duration_minutes),
        default_price: Number(createForm.default_price),
        salon_id: selectedSalonId,
      })
      setInfo('Usluga zostala dodana.')
      setCreateOpen(false)
      setCreateForm(emptyCreateForm)
      await loadCatalog(selectedSalonId)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie dodac uslugi.')
    }
  }

  const saveEdit = async () => {
    if (!editServiceId || selectedSalonId === '') return
    setError('')
    setInfo('')
    try {
      await api.patch('/legacy/catalog/services/' + editServiceId, {
        service_name: editForm.service_name.trim(),
        service_segment: editForm.service_segment,
        duration_minutes: Number(editForm.duration_minutes),
        default_price: Number(editForm.default_price),
        is_active: editForm.is_active,
      }, { params: { salon_id: selectedSalonId } })
      setInfo('Usluga zostala zaktualizowana.')
      setEditOpen(false)
      setEditServiceId(null)
      await loadCatalog(selectedSalonId)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac zmian.')
    }
  }

  const removeService = async (row: ServiceRow) => {
    if (selectedSalonId === '') return
    if (!window.confirm('Usunac usluge ' + row.service_code + ' - ' + row.service_name + '?')) return
    setError('')
    setInfo('')
    try {
      await api.delete('/legacy/catalog/services/' + row.service_id, { params: { salon_id: selectedSalonId } })
      setInfo('Usluga zostala usunieta z salonu.')
      await loadCatalog(selectedSalonId)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie usunac uslugi.')
    }
  }

  const openFormulaDialog = (row: ServiceRow) => {
    setFormulaService(row)
    setRecipeItems([])
    setRecipeEditingId(null)
    setRecipePosition('1')
    setRecipeProductFamily('')
    setRecipeProduct(null)
    setRecipeProductOptions([])
    setRecipeProductQuery('')
    setDebouncedRecipeProductQuery('')
    setRecipeValidationError('')
    setRecipeQuantityMode('EXACT')
    setRecipeQuantity('1')
    setRecipePlannedMin('')
    setRecipePlannedDefault('1')
    setRecipePlannedMax('')
    setRecipeUnit('PCS')
    setRecipeNote('')
    setRecipePackageLabel('')
    setRecipeUnitLabel('szt')
    setRecipeIsRequired(true)
    setRecipeInventoryMode('PER_SERVICE')
    setRecipeEditingOptional(false)
    setRecipeIsOptional(false)
    setRecipeOptionalFamily('ARTYKULY_JEDNORAZOWE')
    setRecipeOptionalProduct(null)
    setRecipeOptionalProductOptions([])
    setRecipeOptionalProductQuery('')
    setDebouncedRecipeOptionalProductQuery('')
    setFormulaOpen(true)
    void loadRecipeItems(row.service_id)
  }

  const loadRecipeItems = async (serviceId: number) => {
    try {
      const res = await api.get<RecipeItemRow[]>(`/services/${serviceId}/recipe`)
      setRecipeItems(res.data || [])
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac receptury.')
    }
  }

  const resetRecipeDraft = (items: RecipeItemRow[] = recipeItems) => {
    setRecipeEditingId(null)
    setRecipePosition(String((items.reduce((max, item) => Math.max(max, item.position || 0), 0) || 0) + 1))
    setRecipeProductFamily('')
    setRecipeProduct(null)
    setRecipeProductQuery('')
    setDebouncedRecipeProductQuery('')
    setRecipeValidationError('')
    setRecipeQuantityMode('EXACT')
    setRecipeQuantity('1')
    setRecipePlannedMin('')
    setRecipePlannedDefault('1')
    setRecipePlannedMax('')
    setRecipeUnit('PCS')
    setRecipeNote('')
    setRecipePackageLabel('')
    setRecipeUnitLabel('szt')
    setRecipeIsRequired(true)
    setRecipeInventoryMode('PER_SERVICE')
    setRecipeEditingOptional(false)
    setRecipeIsOptional(false)
    setRecipeOptionalFamily('ARTYKULY_JEDNORAZOWE')
    setRecipeOptionalProduct(null)
    setRecipeOptionalProductOptions([])
    setRecipeOptionalProductQuery('')
    setDebouncedRecipeOptionalProductQuery('')
  }

  const saveRecipeItem = async (closeAfterSave = false) => {
    if (selectedSalonId === '' || !formulaService) return
    setError('')
    setRecipeValidationError('')
    if (!recipeProductFamily.trim()) {
      setRecipeValidationError('Wymagana rodzina produktu')
      return
    }
    if (recipeIsOptional && !recipeOptionalProduct) {
      setRecipeValidationError('Wybierz dodatkowy zasob')
      return
    }
    const quantityMode = recipeQuantityMode
    const exactValue = Number(recipeQuantity)
    const defaultValue = Number(recipePlannedDefault)
    const minValue = recipePlannedMin === '' ? null : Number(recipePlannedMin)
    const maxValue = recipePlannedMax === '' ? null : Number(recipePlannedMax)
    if (quantityMode === 'RANGE') {
      if (!Number.isFinite(defaultValue) || defaultValue <= 0) {
        setRecipeValidationError('Dla zakresu podaj poprawna ilosc domyslna')
        return
      }
      if ((minValue !== null && (!Number.isFinite(minValue) || minValue <= 0)) || (maxValue !== null && (!Number.isFinite(maxValue) || maxValue <= 0))) {
        setRecipeValidationError('Zakres musi zawierac dodatnie wartosci')
        return
      }
      if (minValue !== null && minValue > defaultValue) {
        setRecipeValidationError('Minimum nie moze byc wieksze od domyslnej')
        return
      }
      if (maxValue !== null && maxValue < defaultValue) {
        setRecipeValidationError('Maksimum nie moze byc mniejsze od domyslnej')
        return
      }
    } else {
      if (!Number.isFinite(exactValue) || exactValue <= 0) {
        setRecipeValidationError('Podaj dodatnia ilosc')
        return
      }
    }
    if (recipeIsRequired && recipeInventoryMode === 'STOCKTAKE_ONLY') {
      setRecipeValidationError('Pozycja wymagana nie moze miec trybu tylko remanent')
      return
    }
    const packageSize = parsePackageLabel(recipePackageLabel)
    const packageUnits = parseUnitCountLabel(recipeUnitLabel)
    const plannedDefaultValue = quantityMode === 'RANGE' ? defaultValue : exactValue
    try {
      const payload = {
        position: Math.max(1, Number(recipePosition) || 1),
        product_family: normalizeRecipeFamilyValue(recipeProductFamily) || null,
        product_id: recipeProduct?.id ?? null,
        product_label_snapshot: recipeProduct?.name ?? null,
        is_optional: recipeEditingId ? recipeEditingOptional : false,
        is_required: recipeIsRequired,
        quantity_mode: quantityMode,
        planned_quantity: plannedDefaultValue,
        planned_min: quantityMode === 'RANGE' ? minValue : null,
        planned_default: plannedDefaultValue,
        planned_max: quantityMode === 'RANGE' ? maxValue : null,
        unit: recipeUnit,
        recipe_unit_label: recipeUnit,
        package_unit_count: packageUnits.count,
        package_unit_label: packageUnits.label,
        package_size_value: packageSize.amount,
        package_size_unit: packageSize.unit,
        inventory_mode: recipeInventoryMode,
        note: recipeNote.trim() || null,
      }
      if (recipeEditingId) {
        const res = await api.patch<RecipeItemRow>(
          `/services/${formulaService.service_id}/recipe/${recipeEditingId}`,
          payload,
        )
        setRecipeItems((prev) => prev.map((item) => (item.id === recipeEditingId ? res.data : item)))
      } else {
        const res = await api.post<RecipeItemRow>(`/services/${formulaService.service_id}/recipe`, payload)
        const nextItems: RecipeItemRow[] = [res.data]
        if (recipeIsOptional && recipeOptionalProduct) {
          const optionalRes = await api.post<RecipeItemRow>(`/services/${formulaService.service_id}/recipe`, {
            product_family: normalizeRecipeFamilyValue(recipeOptionalFamily) || 'ARTYKULY_JEDNORAZOWE',
            product_id: recipeOptionalProduct.id,
            product_label_snapshot: recipeOptionalProduct.name,
            is_optional: true,
            is_required: false,
            quantity_mode: 'ESTIMATE',
            planned_quantity: 1,
            planned_default: 1,
            unit: 'PCS',
            recipe_unit_label: 'PCS',
            inventory_mode: 'BATCH_ESTIMATE',
            note: recipeNote.trim() || recipeOptionalProduct.name,
          })
          nextItems.push(optionalRes.data)
        }
        setRecipeItems((prev) => [...prev, ...nextItems])
      }
      resetRecipeDraft()
      if (closeAfterSave) {
        closeFormulaDialog()
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac receptury.')
    }
  }

  const editRecipeItem = (item: RecipeItemRow) => {
    setRecipeEditingId(item.id)
    setRecipePosition(String(item.position || 1))
    setRecipeProductFamily(normalizeRecipeFamilyValue(item.product_family || ''))
    setRecipeProduct(
      item.product_id
        ? {
            id: item.product_id,
            code: '',
            name: item.product_name || `#${item.product_id}`,
            family_code: item.product_family || null,
          }
        : null,
    )
    setRecipeProductQuery('')
    setDebouncedRecipeProductQuery('')
    setRecipeValidationError('')
    setRecipeQuantityMode(((item.quantity_mode || 'EXACT').toUpperCase() as 'EXACT' | 'RANGE' | 'ESTIMATE'))
    setRecipeQuantity(String(item.planned_default ?? item.planned_quantity))
    setRecipePlannedMin(item.planned_min != null ? String(item.planned_min) : '')
    setRecipePlannedDefault(String(item.planned_default ?? item.planned_quantity))
    setRecipePlannedMax(item.planned_max != null ? String(item.planned_max) : '')
    setRecipeUnit((item.recipe_unit_label || item.unit || 'PCS').toUpperCase())
    setRecipeNote(item.note || '')
    setRecipePackageLabel(item.poj || '')
    setRecipeUnitLabel(item.iljedn || '1 szt')
    setRecipeIsRequired(item.is_required ?? true)
    setRecipeInventoryMode(((item.inventory_mode || 'PER_SERVICE').toUpperCase() as 'PER_SERVICE' | 'BATCH_ESTIMATE' | 'STOCKTAKE_ONLY'))
    setRecipeEditingOptional(Boolean(item.is_optional))
    setRecipeIsOptional(false)
    setRecipeOptionalFamily('ARTYKULY_JEDNORAZOWE')
    setRecipeOptionalProduct(null)
    setRecipeOptionalProductOptions([])
    setRecipeOptionalProductQuery('')
    setDebouncedRecipeOptionalProductQuery('')
  }

  const duplicateRecipeItem = (item: RecipeItemRow) => {
    setRecipeEditingId(null)
    setRecipePosition(String((recipeItems.reduce((max, row) => Math.max(max, row.position || 0), 0) || 0) + 1))
    setRecipeProductFamily(normalizeRecipeFamilyValue(item.product_family || ''))
    setRecipeProduct(
      item.product_id
        ? {
            id: item.product_id,
            code: '',
            name: item.product_name || `#${item.product_id}`,
            family_code: item.product_family || null,
          }
        : null,
    )
    setRecipeProductQuery('')
    setDebouncedRecipeProductQuery('')
    setRecipeValidationError('')
    setRecipeQuantityMode(((item.quantity_mode || 'EXACT').toUpperCase() as 'EXACT' | 'RANGE' | 'ESTIMATE'))
    setRecipeQuantity(String(item.planned_default ?? item.planned_quantity))
    setRecipePlannedMin(item.planned_min != null ? String(item.planned_min) : '')
    setRecipePlannedDefault(String(item.planned_default ?? item.planned_quantity))
    setRecipePlannedMax(item.planned_max != null ? String(item.planned_max) : '')
    setRecipeUnit((item.recipe_unit_label || item.unit || 'PCS').toUpperCase())
    setRecipeNote(item.note || '')
    setRecipePackageLabel(item.poj || '')
    setRecipeUnitLabel(item.iljedn || '1 szt')
    setRecipeIsRequired(item.is_required ?? true)
    setRecipeInventoryMode(((item.inventory_mode || 'PER_SERVICE').toUpperCase() as 'PER_SERVICE' | 'BATCH_ESTIMATE' | 'STOCKTAKE_ONLY'))
    setRecipeEditingOptional(false)
    setRecipeIsOptional(false)
    setRecipeOptionalFamily('ARTYKULY_JEDNORAZOWE')
    setRecipeOptionalProduct(null)
    setRecipeOptionalProductOptions([])
    setRecipeOptionalProductQuery('')
    setDebouncedRecipeOptionalProductQuery('')
  }

  const getRecipeTypeLabel = (item: RecipeItemRow) => {
    if ((item.inventory_mode || '').toUpperCase() === 'STOCKTAKE_ONLY') return 'Remanentowa'
    if ((item.quantity_mode || '').toUpperCase() === 'ESTIMATE' || item.is_required === false) return 'Szacunkowa'
    if (item.is_optional) return 'Dodatkowa'
    return 'Glowna'
  }

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedRecipeProductQuery(recipeProductQuery.trim())
    }, 300)
    return () => window.clearTimeout(timeout)
  }, [recipeProductQuery])

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedRecipeOptionalProductQuery(recipeOptionalProductQuery.trim())
    }, 300)
    return () => window.clearTimeout(timeout)
  }, [recipeOptionalProductQuery])

  useEffect(() => {
    if (!formulaOpen || selectedSalonId === '') return
    loadRecipeFamilyOptions()
      .catch((err: any) => setError(err?.response?.data?.detail || 'Nie udalo sie pobrac rodzin produktow.'))
  }, [formulaOpen, selectedSalonId])

  useEffect(() => {
    if (!formulaOpen || selectedSalonId === '') return
    api.get<RecipeProductOption[]>('/colors', {
      params: {
        salon_id: selectedSalonId,
        family: recipeProductFamily.trim() || undefined,
        backbar: true,
        search: debouncedRecipeProductQuery || undefined,
      },
    })
      .then((res) => setRecipeProductOptions(res.data || []))
      .catch((err: any) => setError(err?.response?.data?.detail || 'Nie udalo sie pobrac listy zasobow.'))
  }, [debouncedRecipeProductQuery, formulaOpen, recipeProductFamily, selectedSalonId])

  useEffect(() => {
    if (!formulaOpen || selectedSalonId === '' || !recipeIsOptional) return
    api.get<RecipeProductOption[]>('/colors', {
      params: {
        salon_id: selectedSalonId,
        family: recipeOptionalFamily.trim() || undefined,
        backbar: true,
        search: debouncedRecipeOptionalProductQuery || undefined,
      },
    })
      .then((res) => setRecipeOptionalProductOptions(res.data || []))
      .catch((err: any) => setError(err?.response?.data?.detail || 'Nie udalo sie pobrac listy dodatkowych zasobow.'))
  }, [debouncedRecipeOptionalProductQuery, formulaOpen, recipeIsOptional, recipeOptionalFamily, selectedSalonId])

  useEffect(() => {
    if (!formulaOpen || !recipeProduct) {
      setRecipePackageLabel('')
      setRecipeUnitLabel('szt')
      return
    }
    api.get<RecipeProductDetail>(`/colors/${recipeProduct.id}`, {
      params: { backbar: true },
    })
      .then((res) => {
        setRecipePackageLabel(res.data?.poj || '')
        const unitLabel = (res.data?.iljedn || '1 szt').toLowerCase().includes('szt') ? 'szt' : (res.data?.iljedn || '1 szt')
        setRecipeUnitLabel(unitLabel)
      })
      .catch((err: any) => setError(err?.response?.data?.detail || 'Nie udalo sie pobrac szczegolow zasobu.'))
  }, [formulaOpen, recipeProduct])

  const deleteRecipeItem = async (item: RecipeItemRow) => {
    if (!formulaService) return
    setError('')
    try {
      await api.delete(`/services/${formulaService.service_id}/recipe/${item.id}`)
      const nextItems = recipeItems.filter((row) => row.id !== item.id)
      setRecipeItems(nextItems)
      if (recipeEditingId === item.id) {
        resetRecipeDraft(nextItems)
      } else {
        setRecipePosition(String((nextItems.reduce((max, row) => Math.max(max, row.position || 0), 0) || 0) + 1))
        setRecipeValidationError('')
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie usunac pozycji receptury.')
    }
  }

  const saveInlinePrice = async (row: ServiceRow) => {
    if (selectedSalonId === '') return
    const raw = (priceDraftByServiceId[row.service_id] ?? '').trim().replace(',', '.')
    if (raw === '') {
      setPriceDraftByServiceId((prev) => ({ ...prev, [row.service_id]: String(Number(row.price).toFixed(2)) }))
      return
    }
    const parsed = Number(raw)
    if (!Number.isFinite(parsed) || parsed < 0) {
      setError('Niepoprawna cena. Wpisz liczbe >= 0.')
      setPriceDraftByServiceId((prev) => ({ ...prev, [row.service_id]: String(Number(row.price).toFixed(2)) }))
      return
    }
    const normalized = Number(parsed.toFixed(2))
    if (Number(row.price.toFixed(2)) === normalized) return

    setSavingPriceByServiceId((prev) => ({ ...prev, [row.service_id]: true }))
    setError('')
    try {
      await api.patch(`/legacy/catalog/services/${row.service_id}/price`, { price: normalized }, { params: { salon_id: selectedSalonId } })
      setServices((prev) =>
        prev.map((item) => (item.service_id === row.service_id ? { ...item, price: normalized } : item))
      )
      setPriceDraftByServiceId((prev) => ({ ...prev, [row.service_id]: String(normalized.toFixed(2)) }))
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac ceny uslugi.')
      setPriceDraftByServiceId((prev) => ({ ...prev, [row.service_id]: String(Number(row.price).toFixed(2)) }))
    } finally {
      setSavingPriceByServiceId((prev) => ({ ...prev, [row.service_id]: false }))
    }
  }

  const exportRecipes = async () => {
    setError('')
    setInfo('')
    setExportingRecipes(true)
    try {
      const response = await api.get('/recipes/export/xlsx', { responseType: 'blob' })
      const disposition = response.headers['content-disposition'] as string | undefined
      const matched = disposition?.match(/filename=\"?([^\";]+)\"?/)
      const filename = matched?.[1] || `service_recipes_${new Date().toISOString().slice(0, 10)}.xlsx`
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      setInfo('Eksport receptur zakonczony.')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie wyeksportowac receptur.')
    } finally {
      setExportingRecipes(false)
    }
  }

  const importRecipes = async (file: File) => {
    setError('')
    setInfo('')
    setImportingRecipes(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const response = await api.post('/recipes/import/xlsx', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const payload = response.data || {}
      setInfo(
        `Import receptur: uslugi ${payload.imported_services ?? 0}, pozycje ${payload.imported_rows ?? 0}, pominiete ${payload.skipped_rows ?? 0}.`,
      )
      if (selectedSalonId !== '') {
        await loadCatalog(selectedSalonId)
      }
      if (formulaService) {
        await loadRecipeItems(formulaService.service_id)
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zaimportowac receptur.')
    } finally {
      setImportingRecipes(false)
      if (recipeImportInputRef.current) {
        recipeImportInputRef.current.value = ''
      }
    }
  }

  return (
    <Box>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent='space-between' spacing={1.5} sx={{ mb: 2 }}>
        <Typography variant='h4'>Cennik uslug</Typography>
        <Stack direction='row' spacing={1}>
          <Button variant='outlined' startIcon={<Refresh />} onClick={() => selectedSalonId !== '' && loadCatalog(selectedSalonId)}>Odswiez</Button>
          <Button
            variant='outlined'
            color={(syncDiff?.diff?.total || 0) > 0 ? 'warning' : 'success'}
            onClick={() => selectedSalonId !== '' && loadCatalog(selectedSalonId)}
            disabled={selectedSalonId === '' || syncBusy}
          >
            Roznice legacy: {syncDiff?.diff?.total ?? '-'}
          </Button>
          <Button
            variant='contained'
            color='secondary'
            onClick={syncFromLegacy}
            disabled={selectedSalonId === '' || syncBusy}
          >
            {syncBusy ? 'Synchronizacja...' : 'Synchronizuj z legacy'}
          </Button>
          {canEditRecipe && (
            <>
              <input
                ref={recipeImportInputRef}
                type='file'
                accept='.xlsx,.xls'
                style={{ display: 'none' }}
                onChange={(event) => {
                  const file = event.target.files?.[0]
                  if (!file) return
                  importRecipes(file).catch(() => undefined)
                }}
              />
              <Button
                variant='outlined'
                startIcon={<FileDownload />}
                onClick={() => exportRecipes().catch(() => undefined)}
                disabled={exportingRecipes || importingRecipes}
              >
                {exportingRecipes ? 'Eksport...' : 'Eksport XLSX'}
              </Button>
              <Button
                variant='outlined'
                startIcon={<FileUpload />}
                onClick={() => recipeImportInputRef.current?.click()}
                disabled={exportingRecipes || importingRecipes}
              >
                {importingRecipes ? 'Import...' : 'Import XLS/XLSX'}
              </Button>
            </>
          )}
          <Button variant='contained' onClick={() => setCreateOpen(true)} disabled={selectedSalonId === ''}>Dodaj usluge</Button>
        </Stack>
      </Stack>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mb: 2 }}>
        <FormControl size='small' sx={{ minWidth: 260 }}>
          <InputLabel>Salon</InputLabel>
          <Select
            label='Salon'
            value={selectedSalonId}
            onChange={(e) => setSelectedSalonId(e.target.value === '' ? '' : Number(e.target.value))}
          >
            {orderedSalons.map((s) => (
              <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          size='small'
          label='Szukaj po kodzie lub nazwie'
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          sx={{ minWidth: 320 }}
        />
      </Stack>
      <Typography variant='caption' color='text.secondary' sx={{ display: 'block', mb: 1.5 }}>
        Rozliczanie materialow wynika z pozycji receptury: pusta receptura = brak rozliczania, uzupelniona receptura = rozliczanie wlaczone.
      </Typography>

      {error && <Alert severity='error' sx={{ mb: 2 }}>{error}</Alert>}
      {info && <Alert severity='success' sx={{ mb: 2 }}>{info}</Alert>}

      <TableContainer component={Paper}>
        <Table size='small'>
          <TableHead>
            <TableRow>
              <TableCell>Kod</TableCell>
              <TableCell>Nazwa</TableCell>
              <TableCell>Znacznik</TableCell>
              <TableCell align='right'>Czas (min)</TableCell>
              <TableCell align='right'>Cena</TableCell>
              <TableCell align='center'>Receptura</TableCell>
              <TableCell align='right'>Akcje</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map((row) => (
              <TableRow key={row.service_id}>
                <TableCell>{row.service_code}</TableCell>
                <TableCell>{row.service_name}</TableCell>
                <TableCell>{SERVICE_SEGMENT_LABELS[row.service_segment] || row.service_segment}</TableCell>
                <TableCell align='right'>{row.duration_minutes}</TableCell>
                <TableCell align='right' sx={{ minWidth: 170 }}>
                  <TextField
                    size='small'
                    type='number'
                    inputProps={{ step: 0.01, min: 0 }}
                    value={priceDraftByServiceId[row.service_id] ?? String(Number(row.price).toFixed(2))}
                    disabled={!!savingPriceByServiceId[row.service_id]}
                    onFocus={(event) => event.target.select()}
                    onChange={(event) =>
                      setPriceDraftByServiceId((prev) => ({ ...prev, [row.service_id]: event.target.value }))
                    }
                    onBlur={() => saveInlinePrice(row)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') {
                        event.preventDefault()
                        ;(event.target as HTMLInputElement).blur()
                      }
                    }}
                  />
                </TableCell>
                <TableCell align='center'>
                  <Stack direction='row' spacing={1} justifyContent='center' alignItems='center'>
                    {(() => {
                      const isOptional = isRecipeOptionalByService(row)
                      const hasRecipe = !!row.is_formula
                      const color = isOptional ? 'inherit' : hasRecipe ? 'success' : 'error'
                      const variant = isOptional ? 'outlined' : 'contained'
                      return (
                        <Button
                          size='small'
                          variant={variant}
                          color={color}
                          tabIndex={-1}
                          onClick={() => openFormulaDialog(row)}
                          sx={isOptional ? { color: 'text.secondary', borderColor: 'divider' } : undefined}
                        >
                          Receptura
                        </Button>
                      )
                    })()}
                  </Stack>
                </TableCell>
                <TableCell align='right'>
                  <Stack direction='row' spacing={1} justifyContent='flex-end'>
                    <Button size='small' variant='outlined' startIcon={<Edit />} tabIndex={-1} onClick={() => openEdit(row)}>
                      Edytuj
                    </Button>
                    <Button size='small' variant='outlined' color='error' startIcon={<Delete />} tabIndex={-1} onClick={() => removeService(row)}>
                      Usun
                    </Button>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {!filtered.length && !loading && (
              <TableRow>
                <TableCell colSpan={7}>Brak danych.</TableCell>
              </TableRow>
            )}
            {loading && (
              <TableRow>
                <TableCell colSpan={7}>Ladowanie...</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} fullWidth maxWidth='sm'>
        <DialogTitle>Nowa usluga</DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 0.5 }}>
            <TextField
              size='small'
              label='Kod uslugi'
              value={createForm.service_code}
              onChange={(e) => setCreateForm((prev) => ({ ...prev, service_code: e.target.value }))}
            />
            <TextField
              size='small'
              label='Nazwa uslugi'
              value={createForm.service_name}
              onChange={(e) => setCreateForm((prev) => ({ ...prev, service_name: e.target.value }))}
            />
            <FormControl size='small'>
              <InputLabel>Znacznik</InputLabel>
              <Select
                label='Znacznik'
                value={createForm.service_segment}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, service_segment: e.target.value as ServiceSegment }))}
              >
                {SERVICE_SEGMENT_OPTIONS.map((segment) => (
                  <MenuItem key={segment.value} value={segment.value}>
                    {segment.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              size='small'
              type='number'
              label='Czas trwania (min)'
              value={createForm.duration_minutes}
              onChange={(e) => setCreateForm((prev) => ({ ...prev, duration_minutes: e.target.value }))}
            />
            <TextField
              size='small'
              type='number'
              label='Cena'
              value={createForm.default_price}
              onChange={(e) => setCreateForm((prev) => ({ ...prev, default_price: e.target.value }))}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Anuluj</Button>
          <Button
            variant='contained'
            onClick={createService}
            disabled={
              selectedSalonId === '' ||
              createForm.service_code.trim().length === 0 ||
              createForm.service_name.trim().length === 0 ||
              createForm.service_segment === '' ||
              Number(createForm.duration_minutes) < 0 ||
              Number(createForm.default_price) < 0
            }
          >
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={editOpen} onClose={() => setEditOpen(false)} fullWidth maxWidth='sm'>
        <DialogTitle>Edycja uslugi</DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 0.5 }}>
            <TextField size='small' label='Kod uslugi' value={editForm.service_code} disabled />
            <TextField
              size='small'
              label='Nazwa uslugi'
              value={editForm.service_name}
              onChange={(e) => setEditForm((prev) => ({ ...prev, service_name: e.target.value }))}
            />
            <FormControl size='small'>
              <InputLabel>Znacznik</InputLabel>
              <Select
                label='Znacznik'
                value={editForm.service_segment}
                onChange={(e) => setEditForm((prev) => ({ ...prev, service_segment: e.target.value as ServiceSegment }))}
              >
                {SERVICE_SEGMENT_OPTIONS.map((segment) => (
                  <MenuItem key={segment.value} value={segment.value}>
                    {segment.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              size='small'
              type='number'
              label='Czas trwania (min)'
              value={editForm.duration_minutes}
              onChange={(e) => setEditForm((prev) => ({ ...prev, duration_minutes: e.target.value }))}
            />
            <TextField
              size='small'
              type='number'
              label='Cena'
              value={editForm.default_price}
              onChange={(e) => setEditForm((prev) => ({ ...prev, default_price: e.target.value }))}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditOpen(false)}>Anuluj</Button>
          <Button
            variant='contained'
            onClick={saveEdit}
            disabled={
              editForm.service_name.trim().length === 0 ||
              editForm.service_segment === '' ||
              Number(editForm.duration_minutes) < 0 ||
              Number(editForm.default_price) < 0
            }
          >
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={formulaOpen}
        onClose={closeFormulaDialog}
        fullWidth
        maxWidth='xl'
        PaperProps={{
          sx: {
            width: '92vw',
            maxWidth: 1400,
          },
        }}
      >
        <DialogTitle>
          Receptura uslugi {formulaService ? `${formulaService.service_code} - ${formulaService.service_name}` : ''}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 0.5 }}>
            <TableContainer component={Paper} variant='outlined' sx={{ maxWidth: '100%', overflowX: 'auto' }}>
              <Table size='small'>
                <TableHead>
                  <TableRow>
                    <TableCell>Typ</TableCell>
                    <TableCell>Rodzina</TableCell>
                    <TableCell>Domyslny produkt</TableCell>
                    <TableCell align='right'>Poz.</TableCell>
                    <TableCell>Tryb</TableCell>
                    <TableCell align='right'>Min</TableCell>
                    <TableCell align='right'>Domyslna</TableCell>
                    <TableCell align='right'>Max</TableCell>
                    <TableCell>JM</TableCell>
                    <TableCell>Razem</TableCell>
                    <TableCell>Wymagana</TableCell>
                    <TableCell>Rozliczanie</TableCell>
                    <TableCell>Notatka</TableCell>
                    <TableCell align='right' sx={{ position: 'sticky', right: 0, backgroundColor: 'background.paper', zIndex: 1 }}>
                      Akcje
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recipeItems.map((item) => (
                    <TableRow
                      key={item.id}
                      hover={canEditRecipe}
                      onClick={() => {
                        if (canEditRecipe) editRecipeItem(item)
                      }}
                      sx={canEditRecipe ? { cursor: 'pointer' } : undefined}
                    >
                      <TableCell>{getRecipeTypeLabel(item)}</TableCell>
                      <TableCell>{item.product_family || '-'}</TableCell>
                      <TableCell>{item.product_name || 'Brak (wybierasz przy wykonaniu)'}</TableCell>
                      <TableCell align='right'>{item.position || 1}</TableCell>
                      <TableCell>{getQuantityModeLabel(item.quantity_mode)}</TableCell>
                      <TableCell align='right'>{item.planned_min != null ? Number(item.planned_min).toFixed(2) : '-'}</TableCell>
                      <TableCell align='right'>{Number(item.planned_default ?? item.planned_quantity).toFixed(2)}</TableCell>
                      <TableCell align='right'>{item.planned_max != null ? Number(item.planned_max).toFixed(2) : '-'}</TableCell>
                      <TableCell>{item.recipe_unit_label || item.unit}</TableCell>
                      <TableCell>{item.total_label || '-'}</TableCell>
                      <TableCell>{item.is_required === false ? 'Nie' : 'Tak'}</TableCell>
                      <TableCell>{getInventoryModeLabel(item.inventory_mode)}</TableCell>
                      <TableCell>{item.note || '-'}</TableCell>
                      <TableCell
                        align='right'
                        sx={{ position: 'sticky', right: 0, backgroundColor: 'background.paper', zIndex: 1 }}
                      >
                        {canEditRecipe && (
                          <Stack direction='row' spacing={0.75} justifyContent='flex-end'>
                            <Button
                              size='small'
                              variant='outlined'
                              startIcon={<Edit fontSize='small' />}
                              onClick={(event) => {
                                event.stopPropagation()
                                editRecipeItem(item)
                              }}
                            >
                              Edytuj
                            </Button>
                            <Button
                              size='small'
                              variant='outlined'
                              startIcon={<ContentCopy fontSize='small' />}
                              onClick={(event) => {
                                event.stopPropagation()
                                duplicateRecipeItem(item)
                              }}
                            >
                              Duplikuj
                            </Button>
                            <Button
                              size='small'
                              variant='outlined'
                              color='error'
                              startIcon={<Delete fontSize='small' />}
                              onClick={(event) => {
                                event.stopPropagation()
                                deleteRecipeItem(item)
                              }}
                            >
                              Usun
                            </Button>
                          </Stack>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {!recipeItems.length && (
                    <TableRow>
                      <TableCell colSpan={14}>Brak pozycji receptury.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            {recipeValidationError && <Alert severity='error'>{recipeValidationError}</Alert>}
            <Paper variant='outlined' sx={{ p: 1.5 }}>
              <Stack spacing={1.5}>
                <Typography variant='subtitle2'>Glowny skladnik</Typography>
                <Autocomplete
                  options={recipeFamilyOptions}
                  value={selectedRecipeFamilyOption}
                  onChange={(_, value) => {
                    setRecipeProductFamily(value?.value || '')
                    setRecipeProduct(null)
                    setRecipeValidationError('')
                  }}
                  getOptionLabel={(option) => option.label}
                  isOptionEqualToValue={(option, value) => option.value === value.value}
                  renderOption={(props, option) => (
                    <Box component="li" {...props}>
                      <Stack spacing={0} sx={{ width: '100%' }}>
                        <Typography variant='body2'>{option.label}</Typography>
                        <Typography variant='caption' color='text.secondary'>
                          Kod: {option.value} • Produkty: {option.product_count}
                        </Typography>
                      </Stack>
                    </Box>
                  )}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      size='small'
                      label='Rodzina produktu'
                      placeholder='Wyszukaj lub wybierz rodzine'
                    />
                  )}
                  disabled={!canEditRecipe}
                />
                <Autocomplete
                  options={recipeProductOptions}
                  value={recipeProduct}
                  inputValue={recipeProductQuery}
                  onInputChange={(_, value) => setRecipeProductQuery(value)}
                  onChange={(_, value) => {
                    setRecipeProduct(value)
                    setRecipeValidationError('')
                  }}
                  getOptionLabel={(option) => `${option.code} - ${option.name}${option.brand ? ` - ${option.brand}` : ''}`}
                  isOptionEqualToValue={(option, value) => option.id === value.id}
                  renderOption={(props, option) => (
                    <Box component="li" {...props}>
                      <Stack spacing={0} sx={{ width: '100%' }}>
                        <Typography variant='body2'>
                          {renderHighlightedText(`${option.code} - ${option.name}${option.brand ? ` - ${option.brand}` : ''}`, recipeProductQuery)}
                        </Typography>
                        <Typography variant='caption' color='text.secondary'>
                          {option.family_code || '-'}{option.brand ? ` • ${option.brand}` : ''}
                        </Typography>
                      </Stack>
                    </Box>
                  )}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      size='small'
                      label='Konkretny produkt (opcjonalnie)'
                      error={!!recipeValidationError}
                    />
                  )}
                  disabled={!canEditRecipe}
                />
                <TextField size='small' label='Jednostka operacyjna (info)' value={recipeUnitLabel || 'szt'} disabled fullWidth />
              </Stack>
            </Paper>
            <Paper variant='outlined' sx={{ p: 1.5 }}>
              <Stack spacing={1.5}>
                <Typography variant='subtitle2'>Norma i rozliczanie</Typography>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                  <TextField
                    size='small'
                    type='number'
                    label='Pozycja'
                    value={recipePosition}
                    onChange={(e) => setRecipePosition(e.target.value)}
                    disabled={!canEditRecipe}
                    sx={{ maxWidth: 140 }}
                  />
                  <FormControl size='small' disabled={!canEditRecipe} sx={{ minWidth: 220 }}>
                    <InputLabel>Tryb ilosci</InputLabel>
                    <Select
                      label='Tryb ilosci'
                      value={recipeQuantityMode}
                      onChange={(e) => setRecipeQuantityMode(e.target.value as 'EXACT' | 'RANGE' | 'ESTIMATE')}
                    >
                      <MenuItem value='EXACT'>Dokladna</MenuItem>
                      <MenuItem value='RANGE'>Zakres</MenuItem>
                      <MenuItem value='ESTIMATE'>Szacunkowa</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl size='small' disabled={!canEditRecipe} sx={{ minWidth: 220 }}>
                    <InputLabel>Sposob rozliczania</InputLabel>
                    <Select
                      label='Sposob rozliczania'
                      value={recipeInventoryMode}
                      onChange={(e) =>
                        setRecipeInventoryMode(e.target.value as 'PER_SERVICE' | 'BATCH_ESTIMATE' | 'STOCKTAKE_ONLY')
                      }
                    >
                      <MenuItem value='PER_SERVICE'>Na kazdej usludze</MenuItem>
                      <MenuItem value='BATCH_ESTIMATE'>Szacunek zbiorczy</MenuItem>
                      <MenuItem value='STOCKTAKE_ONLY'>Tylko remanent</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl size='small' disabled={!canEditRecipe} sx={{ minWidth: 160 }}>
                    <InputLabel>Jednostka</InputLabel>
                    <Select
                      label='Jednostka'
                      value={recipeUnit}
                      onChange={(e) => setRecipeUnit(String(e.target.value))}
                    >
                      {UNIT_OPTIONS.map((unit) => (
                        <MenuItem key={unit} value={unit}>
                          {unit}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Stack>
                {recipeQuantityMode === 'RANGE' ? (
                  <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                    <TextField
                      size='small'
                      type='number'
                      label={`Min (${recipeUnit})`}
                      value={recipePlannedMin}
                      onChange={(e) => setRecipePlannedMin(e.target.value)}
                      disabled={!canEditRecipe}
                    />
                    <TextField
                      size='small'
                      type='number'
                      label={`Domyslna (${recipeUnit})`}
                      value={recipePlannedDefault}
                      onChange={(e) => setRecipePlannedDefault(e.target.value)}
                      disabled={!canEditRecipe}
                    />
                    <TextField
                      size='small'
                      type='number'
                      label={`Max (${recipeUnit})`}
                      value={recipePlannedMax}
                      onChange={(e) => setRecipePlannedMax(e.target.value)}
                      disabled={!canEditRecipe}
                    />
                  </Stack>
                ) : (
                  <TextField
                    size='small'
                    type='number'
                    label={`${recipeQuantityMode === 'ESTIMATE' ? 'Ilosc domyslna' : 'Ilosc'} (${recipeUnit})`}
                    value={recipeQuantity}
                    onChange={(e) => setRecipeQuantity(e.target.value)}
                    disabled={!canEditRecipe}
                  />
                )}
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} alignItems={{ xs: 'flex-start', md: 'center' }}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={recipeIsRequired}
                        onChange={(_, checked) => setRecipeIsRequired(checked)}
                        disabled={!canEditRecipe}
                      />
                    }
                    label='Pozycja wymagana'
                  />
                  <TextField
                    size='small'
                    label='Notatka'
                    value={recipeNote}
                    onChange={(e) => setRecipeNote(e.target.value)}
                    disabled={!canEditRecipe}
                    fullWidth
                  />
                </Stack>
              </Stack>
            </Paper>
            <Paper variant='outlined' sx={{ p: 1.5 }}>
              <Stack spacing={1.5}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={recipeIsOptional}
                      onChange={(_, checked) => {
                        setRecipeIsOptional(checked)
                        setRecipeValidationError('')
                        if (checked) {
                          setRecipeOptionalFamily((prev) => prev || 'ARTYKULY_JEDNORAZOWE')
                        } else {
                          setRecipeOptionalProduct(null)
                          setRecipeOptionalProductQuery('')
                          setDebouncedRecipeOptionalProductQuery('')
                        }
                      }}
                      disabled={!canEditRecipe}
                    />
                  }
                  label='Dodatkowy zasob'
                />
                {recipeIsOptional && (
                  <>
                    <Typography variant='subtitle2'>Dodatkowy skladnik</Typography>
                    <Alert severity='warning'>Ta opcja zapisze druga pozycje receptury jako zasob dodatkowy.</Alert>
                <Autocomplete
                  options={recipeOptionalFamilyOptions}
                  value={selectedOptionalFamilyOption}
                  onChange={(_, value) => {
                    setRecipeOptionalFamily(value?.value || '')
                    setRecipeOptionalProduct(null)
                    setRecipeOptionalProductQuery('')
                    setRecipeValidationError('')
                  }}
                  getOptionLabel={(option) => option.label}
                  isOptionEqualToValue={(option, value) => option.value === value.value}
                  renderOption={(props, option) => (
                    <Box component="li" {...props}>
                      <Stack spacing={0} sx={{ width: '100%' }}>
                        <Typography variant='body2'>{option.label}</Typography>
                        <Typography variant='caption' color='text.secondary'>
                          Kod: {option.value} • Produkty: {option.product_count}
                        </Typography>
                      </Stack>
                    </Box>
                  )}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      size='small'
                      label='Rodzina dodatkowego zasobu'
                      placeholder='Wyszukaj lub wybierz rodzine'
                    />
                  )}
                  disabled={!canEditRecipe}
                />
                <Autocomplete
                  options={recipeOptionalProductOptions}
                  value={recipeOptionalProduct}
                  inputValue={recipeOptionalProductQuery}
                  onInputChange={(_, value) => setRecipeOptionalProductQuery(value)}
                  onChange={(_, value) => {
                    setRecipeOptionalProduct(value)
                    setRecipeValidationError('')
                  }}
                  getOptionLabel={(option) => `${option.code} - ${option.name}`}
                  isOptionEqualToValue={(option, value) => option.id === value.id}
                  renderOption={(props, option) => (
                    <Box component="li" {...props}>
                      <Stack spacing={0} sx={{ width: '100%' }}>
                        <Typography variant='body2'>
                          {renderHighlightedText(`${option.code} - ${option.name}`, recipeOptionalProductQuery)}
                        </Typography>
                        <Typography variant='caption' color='text.secondary'>
                          {option.family_code || '-'}{option.brand ? ` • ${option.brand}` : ''}
                        </Typography>
                      </Stack>
                    </Box>
                  )}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      size='small'
                      label='Konkretny dodatkowy zasob'
                    />
                  )}
                  disabled={!canEditRecipe}
                />
                  </>
                )}
              </Stack>
            </Paper>
          </Stack>
        </DialogContent>
        <DialogActions>
          {canEditRecipe && (
            <Button onClick={() => resetRecipeDraft()}>
              Wyczysc formularz
            </Button>
          )}
          <Button
            onClick={closeFormulaDialog}
          >
            Anuluj
          </Button>
          {canEditRecipe && (
            <>
              <Button
                variant='outlined'
                onClick={() => {
                  if (!recipeEditingId && !recipeProductFamily.trim()) {
                    closeFormulaDialog()
                    return
                  }
                  saveRecipeItem(true)
                }}
              >
                Zapisz i zamknij
              </Button>
              <Button
                variant='contained'
                onClick={() => saveRecipeItem(false)}
                disabled={
                  recipeQuantityMode === 'RANGE'
                    ? Number(recipePlannedDefault) <= 0
                    : Number(recipeQuantity) <= 0
                }
              >
                {recipeEditingId ? 'Zapisz pozycje' : 'Dodaj pozycje'}
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>

    </Box>
  )
}

export default ServicesPage
