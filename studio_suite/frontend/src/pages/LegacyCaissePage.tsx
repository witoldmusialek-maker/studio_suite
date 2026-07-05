import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'

type StaffRow = { staff_id: number; staff_code: string; staff_name: string; role_name?: string }
type ServiceRow = {
  service_id: number
  service_code: string
  service_name: string
  service_segment: string
  price: number
  duration_minutes: number
  is_product_shortcut: boolean
}
type BundleRow = {
  bundle_id: number
  bundle_code: string
  bundle_name: string
  price: number
  items: Array<{ position: number; service_id?: number; service_code: string; service_name: string; price: number }>
}
type ProductRow = { product_id: number; product_code: string; product_name: string; price: number; fiscal_code?: string }
type CashSession = { id?: number; salon_id: number; business_date: string; opening_cash: number; closing_cash?: number; status: string }
type DailySummary = {
  salon_id: number
  business_date: string
  cash_session?: CashSession
  opening_cash: number
  service_gross: number
  retail_gross: number
  discount_total: number
  payments_by_method: Record<string, number>
  cash_payments: number
  expenses_total: number
  expected_cash: number
  closing_cash?: number
  cash_difference?: number
}
type ContextResponse = {
  salon_id: number
  business_date: string
  staff: StaffRow[]
  services: ServiceRow[]
  bundles: BundleRow[]
  products: ProductRow[]
  payment_methods: string[]
  cash_session?: CashSession
}
type FicheLine = {
  id: string
  staffCode: string
  staffName: string
  staffId?: number
  serviceCode: string
  serviceName: string
  serviceId?: number
  productId?: number
  bundleId?: number
  lineKind: 'service' | 'product' | 'bundle'
  price: number
  discount: number
}
type FicheRead = { sale_id: number; sale_time: string; status: string; total_gross: number; payment_method?: string }
type FicheAuditRead = {
  id: number
  sale_id: number
  actor_user_id: number
  action_type: string
  reason: string
  previous_status: string
  new_status: string
  created_at: string
}
type ExpenseRead = { id: number; expense_date: string; label: string; amount_gross: number; expense_type: string }
type PresenceRead = { id: number; staff_id: number; presence_date: string; status: string; time_from?: string; time_to?: string }

type ModalKind = 'service' | 'bundle' | 'discount' | 'payment' | 'product' | 'expenses' | 'presence' | 'closing' | 'fiches' | null

const staffPad = (value: string) => value.trim().replace(/\D/g, '').padStart(2, '0')
const codePad = (value: string) => value.trim().replace(/\D/g, '').padStart(4, '0')
const money = (value: number) => Number.isFinite(value) ? value.toFixed(3).replace('.', ',') : '0,000'
const currentMonth = () => new Date().toISOString().slice(0, 7)
const todayDate = () => new Date().toISOString().slice(0, 10)
const makeEmptyLine = (): FicheLine => ({
  id: `${Date.now()}-${Math.random()}`,
  staffCode: '',
  staffName: '',
  serviceCode: '',
  serviceName: '',
  lineKind: 'service',
  price: 0,
  discount: 0,
})

const LegacyLabel = ({ pl, fr }: { pl: string; fr: string }) => (
  <Box component="span" sx={{ display: 'inline-flex', flexDirection: 'column', lineHeight: 1.05 }}>
    <Box component="span" sx={{ fontWeight: 800 }}>{pl}</Box>
    <Box component="span" sx={{ fontSize: 10, opacity: 0.75, fontWeight: 600 }}>{fr}</Box>
  </Box>
)

const LegacyCaissePage = () => {
  const { user } = useAuth()
  const { salons } = useBooking()
  const salonId = user?.linked_salon_id || user?.assigned_salon_ids?.[0] || salons[0]?.id || 1
  const salonName = salons.find((row) => row.id === salonId)?.name || user?.linked_salon_name || 'Salon'
  const [ctx, setCtx] = useState<ContextResponse | null>(null)
  const [lines, setLines] = useState<FicheLine[]>([makeEmptyLine()])
  const [modal, setModal] = useState<ModalKind>(null)
  const [filter, setFilter] = useState('')
  const [activeRow, setActiveRow] = useState(0)
  const [message, setMessage] = useState<string | null>(null)
  const [paymentMethod, setPaymentMethod] = useState('cash')
  const [paymentAmount, setPaymentAmount] = useState('0')
  const [discountMode, setDiscountMode] = useState<'percent' | 'amount'>('percent')
  const [discountValue, setDiscountValue] = useState('')
  const [fiches, setFiches] = useState<FicheRead[]>([])
  const [ficheAudit, setFicheAudit] = useState<Record<number, FicheAuditRead[]>>({})
  const [activeFicheId, setActiveFicheId] = useState<number | null>(null)
  const [expenses, setExpenses] = useState<ExpenseRead[]>([])
  const [presence, setPresence] = useState<PresenceRead[]>([])
  const [summary, setSummary] = useState<DailySummary | null>(null)
  const [expenseLabel, setExpenseLabel] = useState('')
  const [expenseAmount, setExpenseAmount] = useState('')
  const [openingCash, setOpeningCash] = useState('0')
  const [closingCash, setClosingCash] = useState('0')
  const firstInputRef = useRef<HTMLInputElement | null>(null)

  const total = useMemo(() => lines.reduce((sum, row) => sum + Math.max(row.price - row.discount, 0), 0), [lines])
  const completedLines = useMemo(() => lines.filter((row) => row.staffId && (row.serviceId || row.productId || row.bundleId) && row.serviceName), [lines])
  const workingLines = useMemo(() => lines.filter((row) => row.staffId || row.serviceId || row.productId || row.bundleId || row.staffCode || row.serviceCode), [lines])

  const loadContext = useCallback(async () => {
    const res = await api.get<ContextResponse>('/legacy/caisse/context', { params: { salon_id: salonId } })
    setCtx(res.data)
    setOpeningCash(String(res.data.cash_session?.opening_cash ?? 0))
    setClosingCash(String(res.data.cash_session?.closing_cash ?? 0))
  }, [salonId])

  const loadFiches = useCallback(async () => {
    const res = await api.get<FicheRead[]>('/legacy/caisse/fiches', { params: { salon_id: salonId, month: currentMonth() } })
    setFiches(res.data || [])
  }, [salonId])

  const loadExpenses = useCallback(async () => {
    const res = await api.get<ExpenseRead[]>('/legacy/caisse/expenses', { params: { salon_id: salonId, month: currentMonth() } })
    setExpenses(res.data || [])
  }, [salonId])

  const loadPresence = useCallback(async () => {
    const res = await api.get<PresenceRead[]>('/legacy/caisse/presence', { params: { salon_id: salonId } })
    setPresence(res.data || [])
  }, [salonId])

  const loadSummary = useCallback(async () => {
    const res = await api.get<DailySummary>('/legacy/caisse/cash-session/summary', { params: { salon_id: salonId, business_date: todayDate() } })
    setSummary(res.data)
  }, [salonId])

  const loadFicheAudit = useCallback(async (saleId: number) => {
    const res = await api.get<FicheAuditRead[]>(`/legacy/caisse/fiches/${saleId}/audit`)
    setFicheAudit((current) => ({ ...current, [saleId]: res.data || [] }))
    setActiveFicheId(saleId)
  }, [])

  useEffect(() => { void loadContext(); void loadFiches(); void loadSummary() }, [loadContext, loadFiches, loadSummary])
  useEffect(() => { firstInputRef.current?.focus() }, [ctx?.salon_id])

  const setLine = (index: number, patch: Partial<FicheLine>) => {
    setLines((current) => current.map((row, idx) => idx === index ? { ...row, ...patch } : row))
  }

  const ensureNextLine = (index: number) => {
    setLines((current) => index >= current.length - 1 ? [...current, makeEmptyLine()] : current)
  }

  const focusField = (index: number, field: 'staff' | 'service') => {
    window.setTimeout(() => document.getElementById(`caisse-${field}-${index}`)?.focus(), 0)
  }

  const resolveStaff = (index: number) => {
    const raw = lines[index]?.staffCode || ''
    if (!ctx || !raw.trim()) return false
    const normalized = staffPad(raw)
    const row = ctx.staff.find((item) => staffPad(item.staff_code) === normalized)
    if (!row) {
      setMessage(`Nie znaleziono pracownika / Collaborateur: ${normalized}`)
      return false
    }
    setLine(index, { staffCode: row.staff_code, staffName: row.staff_name, staffId: row.staff_id })
    focusField(index, 'service')
    return true
  }

  const addCompletedService = (index: number, service: ServiceRow, staffLine = lines[index]) => {
    if (!staffLine?.staffId) {
      setMessage('Najpierw wpisz kod pracownika / Collaborateur')
      focusField(index, 'staff')
      return
    }
    if (service.is_product_shortcut) {
      const directProduct = ctx?.products.find((item) => codePad(item.product_code) === codePad(service.service_code))
      if (directProduct) {
        addCompletedProduct(index, directProduct, service, staffLine)
        return
      }
      setActiveRow(index)
      setFilter(service.service_code)
      setModal('product')
      return
    }
    setLine(index, {
      serviceCode: service.service_code,
      serviceName: service.service_name,
      serviceId: service.service_id,
      productId: undefined,
      lineKind: 'service',
      price: Number(service.price || 0),
      discount: 0,
    })
    ensureNextLine(index)
    focusField(index + 1, 'staff')
  }

  const addCompletedProduct = (index: number, product: ProductRow, sourceService?: ServiceRow, staffLine = lines[index]) => {
    if (!staffLine?.staffId) return
    setLine(index, {
      serviceCode: sourceService?.service_code || product.product_code,
      serviceName: product.product_name,
      serviceId: sourceService?.service_id,
      productId: product.product_id,
      lineKind: 'product',
      price: Number(product.price || sourceService?.price || 0),
      discount: 0,
    })
    ensureNextLine(index)
    setModal(null)
    focusField(index + 1, 'staff')
  }

  const resolveService = (index: number) => {
    const raw = lines[index]?.serviceCode || ''
    if (!ctx || !raw.trim()) return false
    const normalized = codePad(raw)
    const row = ctx.services.find((item) => codePad(item.service_code) === normalized)
    if (!row) {
      setActiveRow(index)
      setFilter(raw)
      setModal('service')
      return false
    }
    addCompletedService(index, row)
    return true
  }

  const addBundle = (bundle: BundleRow) => {
    const source = lines[activeRow]
    if (!source?.staffId) {
      setMessage('Najpierw wpisz kod pracownika / Collaborateur')
      setModal(null)
      return
    }
    const nextRows = bundle.items.length > 0
      ? bundle.items.map((item) => ({
          id: `${Date.now()}-${bundle.bundle_id}-${item.position}`,
          staffCode: source.staffCode,
          staffName: source.staffName,
          staffId: source.staffId,
          serviceCode: item.service_code,
          serviceName: item.service_name || bundle.bundle_name,
          serviceId: item.service_id,
          bundleId: bundle.bundle_id,
          lineKind: 'bundle' as const,
          price: Number(item.price || 0),
          discount: 0,
        }))
      : [{
          id: `${Date.now()}-${bundle.bundle_id}`,
          staffCode: source.staffCode,
          staffName: source.staffName,
          staffId: source.staffId,
          serviceCode: bundle.bundle_code,
          serviceName: bundle.bundle_name,
          bundleId: bundle.bundle_id,
          lineKind: 'bundle' as const,
          price: Number(bundle.price || 0),
          discount: 0,
        }]
    setLines((current) => {
      const before = current.slice(0, activeRow)
      const after = current.slice(activeRow + 1).filter((row) => row.staffId || row.serviceId || row.productId || row.staffCode || row.serviceCode)
      return [...before, ...nextRows, ...after, makeEmptyLine()]
    })
    setModal(null)
    focusField(activeRow + nextRows.length, 'staff')
  }

  const openModal = (kind: ModalKind, row = activeRow) => {
    setActiveRow(row)
    setFilter(kind === 'service' ? lines[row]?.serviceCode || '' : '')
    if (kind === 'payment') setPaymentAmount(String(total.toFixed(2)))
    if (kind === 'expenses') void loadExpenses()
    if (kind === 'presence') void loadPresence()
    if (kind === 'fiches') void loadFiches()
    setModal(kind)
  }

  const applyDiscount = () => {
    const value = Number(discountValue.replace(',', '.')) || 0
    if (value <= 0) return
    const hasDiscount = completedLines.some((row) => row.discount > 0)
    if (hasDiscount && !window.confirm('Rabat juz naliczony. Kontynuowac? / Discount already done. Proceed?')) return
    setLines((current) => current.map((row) => {
      if (!row.staffId || !(row.serviceId || row.productId || row.bundleId)) return row
      const discount = discountMode === 'percent' ? row.price * value / 100 : value
      return { ...row, discount: Math.min(row.price, Number(discount.toFixed(2))) }
    }))
    setModal(null)
    setDiscountValue('')
  }

  const saveFiche = async () => {
    if (completedLines.length === 0) {
      setMessage('Brak linii fiszki / Aucune fiche')
      return
    }
    const amount = Number(paymentAmount.replace(',', '.')) || total
    await api.post('/legacy/caisse/fiches', {
      salon_id: salonId,
      sale_time: new Date().toISOString(),
      payment_method: paymentMethod,
      status: paymentMethod === 'credit' || paymentMethod === 'attente' ? 'PENDING' : 'COMPLETED',
      lines: completedLines.map((row) => ({
        line_kind: row.lineKind,
        staff_id: row.staffId,
        service_id: row.serviceId,
        product_id: row.productId,
        bundle_id: row.bundleId,
        legacy_worker_code: row.staffCode,
        legacy_service_code: row.serviceCode,
        label: row.serviceName,
        quantity: 1,
        unit_price: row.price,
        discount_amount: row.discount,
      })),
      allocations: [{ method: paymentMethod, amount }],
    })
    setLines([makeEmptyLine()])
    setModal(null)
    setMessage('Fiszka zapisana / Fiche enregistree')
    await loadFiches()
    await loadSummary()
    window.setTimeout(() => firstInputRef.current?.focus(), 0)
  }

  const saveExpense = async () => {
    const amount = Number(expenseAmount.replace(',', '.')) || 0
    if (!expenseLabel.trim() || amount <= 0) return
    await api.post('/legacy/caisse/expenses', { salon_id: salonId, label: expenseLabel, amount_gross: amount, vat_amount: 0, expense_type: 'misc' })
    setExpenseLabel('')
    setExpenseAmount('')
    await loadExpenses()
    await loadSummary()
  }

  const togglePresence = async (staff: StaffRow) => {
    await api.post('/legacy/caisse/presence', { salon_id: salonId, staff_id: staff.staff_id, status: 'PRESENT', presence_date: todayDate() })
    await loadPresence()
  }

  const voidFiche = async (fiche: FicheRead) => {
    setActiveFicheId(fiche.sale_id)
    if (fiche.status === 'VOID') {
      await loadFicheAudit(fiche.sale_id)
      setMessage('Fiszka juz anulowana / Fiche deja annulee')
      return
    }
    const reason = window.prompt(`Powod anulowania fiszki #${fiche.sale_id} / Motif d'annulation`, '')?.trim()
    if (!reason) {
      setMessage('Powod anulowania jest wymagany / Motif obligatoire')
      return
    }
    await api.post(`/legacy/caisse/fiches/${fiche.sale_id}/void`, { reason })
    await loadFiches()
    await loadSummary()
    await loadFicheAudit(fiche.sale_id)
    setMessage('Fiszka anulowana z historia korekty / Fiche annulee avec historique')
  }

  const saveCashSession = async (status: 'OPEN' | 'CLOSED') => {
    await api.post('/legacy/caisse/cash-session', {
      salon_id: salonId,
      business_date: todayDate(),
      opening_cash: Number(openingCash.replace(',', '.')) || 0,
      closing_cash: status === 'CLOSED' ? Number(closingCash.replace(',', '.')) || 0 : undefined,
      status,
    })
    await loadContext()
    await loadSummary()
    setMessage(status === 'CLOSED' ? 'Dzien zamkniety / Journee fermee' : 'Kasa otwarta / Caisse ouverte')
  }

  const serviceRows = useMemo(() => {
    const value = filter.trim().toLowerCase()
    const list = ctx?.services || []
    if (!value) return list.slice(0, 80)
    const padded = codePad(value)
    return list.filter((row) => codePad(row.service_code).includes(padded) || row.service_name.toLowerCase().includes(value)).slice(0, 120)
  }, [ctx, filter])

  const bundleRows = useMemo(() => {
    const value = filter.trim().toLowerCase()
    const list = ctx?.bundles || []
    if (!value) return list.slice(0, 80)
    const padded = codePad(value)
    return list.filter((row) => codePad(row.bundle_code).includes(padded) || row.bundle_name.toLowerCase().includes(value)).slice(0, 120)
  }, [ctx, filter])

  const productRows = useMemo(() => {
    const value = filter.trim().toLowerCase()
    const list = ctx?.products || []
    if (!value) return list.slice(0, 80)
    return list.filter((row) => row.product_code.toLowerCase().includes(value) || row.product_name.toLowerCase().includes(value)).slice(0, 120)
  }, [ctx, filter])

  const keyShortcut = (event: React.KeyboardEvent) => {
    if (event.key === 'F2') { event.preventDefault(); openModal('fiches') }
    if (event.key === 'F4') { event.preventDefault(); openModal('bundle') }
    if (event.key === 'F6') { event.preventDefault(); openModal('payment') }
    if (event.key === 'F9') { event.preventDefault(); openModal('discount') }
  }

  if (!ctx) {
    return <Box sx={{ p: 3 }}><Typography>Ladowanie CAISSE...</Typography></Box>
  }

  return (
    <Box onKeyDown={keyShortcut} sx={{ maxWidth: 1180, mx: 'auto', color: '#071427' }}>
      <Typography variant="h4" sx={{ fontWeight: 900, mb: 1 }}>Legacy CAISSE8</Typography>
      {message && <Alert severity="info" onClose={() => setMessage(null)} sx={{ mb: 1 }}>{message}</Alert>}

      <Paper sx={{ overflow: 'hidden', borderRadius: 2, border: '1px solid #1d4e7d', mb: 1 }}>
        <Box sx={{ bgcolor: '#1169d8', color: 'white', px: 1.5, py: 0.5, fontWeight: 900 }}>CAISSE</Box>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', bgcolor: '#b9c7e3' }}>
          {['Caisse', 'Depenses', 'Presences', 'Fermeture', 'Gestion', 'Stock', 'Rendez-vous', 'Sortie'].map((item) => (
            <Button key={item} onClick={() => item === 'Depenses' ? openModal('expenses') : item === 'Presences' ? openModal('presence') : item === 'Fermeture' ? openModal('closing') : undefined} sx={{ borderRadius: 0, borderRight: '1px solid #244d74', color: item === 'Caisse' ? '#b00090' : '#06131e', fontWeight: 900 }}>
              {item}
            </Button>
          ))}
        </Box>
        <Box sx={{ bgcolor: '#b5c7e5', px: 1.5, py: 0.9, fontStyle: 'italic', fontWeight: 900 }}>
          Salon: {salonName} / {ctx.business_date}
        </Box>
      </Paper>

      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 250px', gap: 1.5 }}>
        <Paper sx={{ overflow: 'hidden', borderRadius: 2, bgcolor: '#9fc5ea', border: '1px solid #6a99c0' }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: '210px 1fr 130px', bgcolor: '#67a9d7', borderBottom: '1px solid #6a99c0' }}>
            <Box sx={{ p: 1, textAlign: 'center' }}><LegacyLabel pl="Pracownik" fr="Collaborateur" /></Box>
            <Box sx={{ p: 1, textAlign: 'center' }}><LegacyLabel pl="Usluga" fr="Service" /></Box>
            <Box sx={{ p: 1, textAlign: 'center' }}><LegacyLabel pl="Cena" fr="Prix" /></Box>
          </Box>
          <Box sx={{ height: 430, overflow: 'hidden', borderBottom: '2px solid #17b85d' }}>
            {lines.slice(0, 12).map((row, index) => (
              <Box key={row.id} sx={{ display: 'grid', gridTemplateColumns: '210px 1fr 130px', minHeight: 34, borderBottom: '1px solid rgba(255,255,255,0.35)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, px: 1 }}>
                  <input
                    ref={index === 0 ? firstInputRef : undefined}
                    id={`caisse-staff-${index}`}
                    value={row.staffCode}
                    onChange={(e) => setLine(index, { staffCode: e.target.value, staffName: '', staffId: undefined })}
                    onKeyDown={(e) => {
                      if (e.key === 'Tab' || e.key === 'Enter') { e.preventDefault(); resolveStaff(index) }
                    }}
                    style={{ width: 52, height: 24, border: '1px solid #7eaad0', background: '#d8ffff', fontWeight: 700 }}
                  />
                  <Box sx={{ fontWeight: row.staffId ? 800 : 400, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{row.staffName}</Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, px: 1 }}>
                  <input
                    id={`caisse-service-${index}`}
                    value={row.serviceCode}
                    onChange={(e) => setLine(index, { serviceCode: e.target.value, serviceName: '', serviceId: undefined, productId: undefined })}
                    onKeyDown={(e) => {
                      if (e.key === 'Tab' || e.key === 'Enter') { e.preventDefault(); resolveService(index) }
                      if (e.key === 'F4') { e.preventDefault(); setActiveRow(index); setModal('bundle') }
                    }}
                    style={{ width: 64, height: 24, border: '1px solid #7eaad0', background: '#d8ffff', fontWeight: 700 }}
                  />
                  <Box sx={{ color: row.lineKind === 'product' ? '#6a008a' : row.bundleId ? '#c70000' : '#001c54', fontWeight: row.serviceName ? 800 : 400 }}>{row.serviceName}</Box>
                </Box>
                <Box sx={{ p: 1, textAlign: 'right', fontWeight: 900 }}>{row.price ? money(Math.max(row.price - row.discount, 0)) : ''}</Box>
              </Box>
            ))}
          </Box>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', bgcolor: '#5aa7dc' }}>
            <Button onClick={() => openModal('fiches')} sx={{ color: '#041326', fontWeight: 900 }}>[F2] Fiszki</Button>
            <Button onClick={() => openModal('payment')} sx={{ color: '#041326', fontWeight: 900 }}>[F6] Suma</Button>
            <Button onClick={() => openModal('bundle')} sx={{ color: '#041326', fontWeight: 900 }}>[F4] Forfaits</Button>
            <Button onClick={() => openModal('discount')} sx={{ color: '#041326', fontWeight: 900 }}>[F9] Rabat</Button>
            <Button onClick={() => setLines([makeEmptyLine()])} sx={{ color: '#041326', fontWeight: 900 }}>Nowa</Button>
            <Button onClick={() => openModal('payment')} sx={{ color: '#041326', fontWeight: 900 }}>OK</Button>
          </Box>
        </Paper>

        <Stack spacing={0} sx={{ bgcolor: '#61afe2', borderRadius: 2, overflow: 'hidden', border: '1px solid #5c95bd' }}>
          {[
            ['Pomoc', 'Aide', () => setMessage('F2 fiszki, F4 forfait, F6 platnosc, F9 rabat')],
            ['Fiszki', 'Fiches', () => openModal('fiches')],
            ['Klienci', 'Clients', () => setMessage('Klienci sa w nowej kartotece aplikacji')],
            ['Forfaits', 'Forfaits', () => openModal('bundle')],
            ['Rendez-vous', 'Rendez-vous', () => setMessage('Wizyty pozostaja w nowym kalendarzu')],
            ['Sous-Total', 'Sous-Total', () => openModal('payment')],
            ['Fiche Suiveuse', 'Fiche Suiveuse', () => setMessage('Opcja wydruku bedzie podlaczona po fiskalizacji')],
            ['Kalkulator', 'Calculatrice', () => window.alert(String(total.toFixed(2)))],
            ['Rabaty', 'Remises', () => openModal('discount')],
            ['Abonament', 'Abonnement', () => setMessage('Abonamenty beda osobnym krokiem')],
            ['Devis', 'Devis', () => setMessage('Devis beda osobnym krokiem')],
            ['Kredyt/Attente', 'Credits/Attente', () => { setPaymentMethod('credit'); openModal('payment') }],
          ].map(([pl, fr, action], idx) => (
            <Button key={String(pl)} onClick={action as () => void} sx={{ minHeight: 51, borderRadius: 0, borderBottom: '1px solid #4385ad', color: '#06131e' }}>
              <LegacyLabel pl={`[F${idx === 9 ? 10 : idx === 10 ? 11 : idx === 11 ? 12 : idx + 1}] ${pl}`} fr={String(fr)} />
            </Button>
          ))}
        </Stack>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 260px', gap: 1.5, mt: 1.5 }}>
        <Paper sx={{ p: 1.5 }}>
          <Typography sx={{ fontWeight: 900 }}>Biezaca fiszka <Box component="span" sx={{ fontSize: 11, opacity: 0.65 }}>Fiche en cours</Box></Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
            {workingLines.length === 0 ? <Typography variant="body2">Wpisz kod pracownika i kod uslugi.</Typography> : workingLines.map((row) => (
              <Box key={row.id} sx={{ px: 1, py: 0.5, bgcolor: '#eef6ff', borderRadius: 1, border: '1px solid #c7d8ea' }}>
                {row.staffCode} {row.staffName} | {row.serviceCode} {row.serviceName} | {money(Math.max(row.price - row.discount, 0))}
              </Box>
            ))}
          </Box>
        </Paper>
        <Paper sx={{ p: 1.5 }}>
          <Typography sx={{ fontWeight: 900 }}>PLN</Typography>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}><span>Sous-total</span><b>{money(total)}</b></Box>
          {summary && (
            <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid #d6e1ee', fontSize: 13 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><span>Fond</span><b>{money(summary.opening_cash)}</b></Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><span>Especes</span><b>{money(summary.cash_payments)}</b></Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><span>Depenses</span><b>{money(summary.expenses_total)}</b></Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><span>Theorique</span><b>{money(summary.expected_cash)}</b></Box>
              {summary.closing_cash !== undefined && <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><span>Final</span><b>{money(summary.closing_cash)}</b></Box>}
              {summary.cash_difference !== undefined && <Box sx={{ display: 'flex', justifyContent: 'space-between', color: summary.cash_difference === 0 ? 'success.main' : 'error.main' }}><span>Ecart</span><b>{money(summary.cash_difference)}</b></Box>}
            </Box>
          )}
          <Button fullWidth variant="contained" sx={{ mt: 1 }} onClick={() => openModal('payment')}>Platnosc / Reglement</Button>
          <Button fullWidth sx={{ mt: 1 }} onClick={() => setLines([makeEmptyLine()])}>Nowa fiszka</Button>
        </Paper>
      </Box>

      <Dialog open={modal === 'service'} onClose={() => setModal(null)} maxWidth="md" fullWidth>
        <DialogTitle>Wybor uslugi <Typography component="span" sx={{ fontSize: 12, ml: 1 }}>Selection d'un Service</Typography></DialogTitle>
        <DialogContent sx={{ height: 560 }}>
          <TextField autoFocus label="Kod lub nazwa" value={filter} onChange={(e) => setFilter(e.target.value)} size="small" sx={{ mb: 1 }} />
          <LegacyTable rows={serviceRows} columns={['Code', 'Libelle', 'Type', 'Prix']} render={(row: ServiceRow) => [row.service_code, row.service_name, row.service_segment, money(row.price)]} onPick={(row) => { addCompletedService(activeRow, row); setModal(null) }} />
        </DialogContent>
      </Dialog>

      <Dialog open={modal === 'bundle'} onClose={() => setModal(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Wybor forfaitu <Typography component="span" sx={{ fontSize: 12, ml: 1 }}>Selection d'un forfait</Typography></DialogTitle>
        <DialogContent sx={{ height: 520 }}>
          <TextField autoFocus label="Kod lub nazwa" value={filter} onChange={(e) => setFilter(e.target.value)} size="small" sx={{ mb: 1 }} />
          <LegacyTable rows={bundleRows} columns={['Co', 'Forfait', 'Tarif']} render={(row: BundleRow) => [row.bundle_code, row.bundle_name, money(row.price)]} onPick={addBundle} />
        </DialogContent>
      </Dialog>

      <Dialog open={modal === 'product'} onClose={() => setModal(null)} maxWidth="md" fullWidth>
        <DialogTitle>Sprzedaz produktu <Typography component="span" sx={{ fontSize: 12, ml: 1 }}>Vente</Typography></DialogTitle>
        <DialogContent sx={{ height: 520 }}>
          <TextField autoFocus label="Produkt" value={filter} onChange={(e) => setFilter(e.target.value)} size="small" sx={{ mb: 1 }} />
          <LegacyTable rows={productRows} columns={['Code', 'Produit', 'Prix']} render={(row: ProductRow) => [row.product_code, row.product_name, money(row.price)]} onPick={(row) => addCompletedProduct(activeRow, row)} />
        </DialogContent>
      </Dialog>

      <Dialog open={modal === 'discount'} onClose={() => setModal(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Rabaty <Typography component="span" sx={{ fontSize: 12, ml: 1 }}>Remises</Typography></DialogTitle>
        <DialogContent>
          <Select value={discountMode} onChange={(e) => setDiscountMode(e.target.value as 'percent' | 'amount')} size="small" sx={{ mr: 1 }}>
            <MenuItem value="percent">Procent / Pourcentage</MenuItem>
            <MenuItem value="amount">Kwota / Montant</MenuItem>
          </Select>
          <TextField autoFocus label="Wartosc" value={discountValue} onChange={(e) => setDiscountValue(e.target.value)} size="small" />
        </DialogContent>
        <DialogActions><Button onClick={() => setModal(null)}>Anuluj</Button><Button variant="contained" onClick={applyDiscount}>OK [F12]</Button></DialogActions>
      </Dialog>

      <Dialog open={modal === 'payment'} onClose={() => setModal(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Platnosc <Typography component="span" sx={{ fontSize: 12, ml: 1 }}>Reglement</Typography></DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 1 }}>Do zaplaty / A payer: <b>{money(total)}</b></Typography>
          <Select fullWidth value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} size="small" sx={{ mb: 1 }}>
            {(ctx.payment_methods || ['cash', 'card']).map((method) => <MenuItem key={method} value={method}>{method}</MenuItem>)}
          </Select>
          <TextField fullWidth label="Otrzymano / Recu" value={paymentAmount} onChange={(e) => setPaymentAmount(e.target.value)} size="small" />
        </DialogContent>
        <DialogActions><Button onClick={() => setModal(null)}>Anuluj</Button><Button variant="contained" onClick={saveFiche}>OK [F12]</Button></DialogActions>
      </Dialog>

      <Dialog open={modal === 'fiches'} onClose={() => setModal(null)} maxWidth="md" fullWidth>
        <DialogTitle>Lista fiszek <Typography component="span" sx={{ fontSize: 12, ml: 1 }}>Liste des fiches — kliknij fiszke aby anulowac/pokazac historie</Typography></DialogTitle>
        <DialogContent sx={{ height: 500 }}>
          <LegacyTable rows={fiches} columns={['Data', 'Total', 'Reglement', 'Status']} render={(row: FicheRead) => [row.sale_time.slice(0, 10), money(row.total_gross), row.payment_method || '-', row.status]} onPick={voidFiche} />
          {activeFicheId && (ficheAudit[activeFicheId] || []).length > 0 && (
            <Box sx={{ mt: 1, p: 1, bgcolor: '#eef6ff', borderRadius: 1 }}>
              <Typography sx={{ fontWeight: 900 }}>Historia korekt / Historique #{activeFicheId}</Typography>
              {(ficheAudit[activeFicheId] || []).map((audit) => (
                <Typography key={audit.id} variant="body2">
                  {audit.created_at.slice(0, 19).replace('T', ' ')} — {audit.action_type}: {audit.previous_status} → {audit.new_status}; {audit.reason}
                </Typography>
              ))}
            </Box>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={modal === 'expenses'} onClose={() => setModal(null)} maxWidth="md" fullWidth>
        <DialogTitle>Wydatki <Typography component="span" sx={{ fontSize: 12, ml: 1 }}>Depenses</Typography></DialogTitle>
        <DialogContent sx={{ height: 500 }}>
          <Stack direction="row" spacing={1} sx={{ mb: 1 }}><TextField label="Opis" value={expenseLabel} onChange={(e) => setExpenseLabel(e.target.value)} size="small" /><TextField label="Kwota" value={expenseAmount} onChange={(e) => setExpenseAmount(e.target.value)} size="small" /><Button variant="contained" onClick={saveExpense}>Dodaj</Button></Stack>
          <LegacyTable rows={expenses} columns={['Data', 'Opis', 'Typ', 'Kwota']} render={(row: ExpenseRead) => [row.expense_date, row.label, row.expense_type, money(row.amount_gross)]} onPick={() => undefined} />
        </DialogContent>
      </Dialog>

      <Dialog open={modal === 'presence'} onClose={() => setModal(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Obecnosci <Typography component="span" sx={{ fontSize: 12, ml: 1 }}>Presences</Typography></DialogTitle>
        <DialogContent sx={{ height: 500 }}>
          <LegacyTable rows={ctx.staff} columns={['Code', 'Pracownik', 'Status']} render={(row: StaffRow) => [row.staff_code, row.staff_name, presence.some((p) => p.staff_id === row.staff_id) ? 'PRESENT' : '-']} onPick={togglePresence} />
        </DialogContent>
      </Dialog>

      <Dialog open={modal === 'closing'} onClose={() => setModal(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Zamkniecie dnia <Typography component="span" sx={{ fontSize: 12, ml: 1 }}>Fermeture</Typography></DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Fond de caisse" value={openingCash} onChange={(e) => setOpeningCash(e.target.value)} size="small" sx={{ mb: 1 }} />
          <TextField fullWidth label="Cash final" value={closingCash} onChange={(e) => setClosingCash(e.target.value)} size="small" />
          {summary && (
            <Box sx={{ mt: 2, p: 1, bgcolor: '#eef6ff', borderRadius: 1 }}>
              <Typography sx={{ fontWeight: 900, mb: 0.5 }}>Resume journee</Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><span>Services</span><b>{money(summary.service_gross)}</b></Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><span>Ventes</span><b>{money(summary.retail_gross)}</b></Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><span>Remises</span><b>{money(summary.discount_total)}</b></Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><span>Theorique caisse</span><b>{money(summary.expected_cash)}</b></Box>
              {summary.cash_difference !== undefined && <Box sx={{ display: 'flex', justifyContent: 'space-between' }}><span>Ecart</span><b>{money(summary.cash_difference)}</b></Box>}
            </Box>
          )}
        </DialogContent>
        <DialogActions><Button onClick={() => saveCashSession('OPEN')}>Otworz</Button><Button variant="contained" onClick={() => saveCashSession('CLOSED')}>Zamknij</Button></DialogActions>
      </Dialog>
    </Box>
  )
}

function LegacyTable<T>({ rows, columns, render, onPick }: { rows: T[]; columns: string[]; render: (row: T) => Array<string | number>; onPick: (row: T) => void }) {
  return (
    <Box sx={{ border: '1px solid #1d4e7d', height: 'calc(100% - 48px)', overflow: 'auto', bgcolor: '#efc39f' }}>
      <Box sx={{ display: 'grid', gridTemplateColumns: `repeat(${columns.length}, minmax(90px, 1fr))`, position: 'sticky', top: 0, bgcolor: '#c8b391', zIndex: 1, fontWeight: 900 }}>
        {columns.map((col) => <Box key={col} sx={{ p: 0.8, borderRight: '1px solid #745d42' }}>{col}</Box>)}
      </Box>
      {rows.map((row, idx) => (
        <Box key={idx} onDoubleClick={() => onPick(row)} onClick={() => onPick(row)} sx={{ display: 'grid', gridTemplateColumns: `repeat(${columns.length}, minmax(90px, 1fr))`, cursor: 'pointer', bgcolor: idx === 0 ? '#251078' : idx % 2 ? '#e8bd99' : '#f1c9a7', color: idx === 0 ? 'white' : 'black', '&:hover': { bgcolor: '#2d198f', color: 'white' } }}>
          {render(row).map((cell, cellIdx) => <Box key={cellIdx} sx={{ p: 0.7, borderRight: '1px solid #8b6c4b', borderBottom: '1px dotted #8b6c4b', fontWeight: cellIdx === 0 ? 900 : 500 }}>{cell}</Box>)}
        </Box>
      ))}
    </Box>
  )
}

export default LegacyCaissePage
