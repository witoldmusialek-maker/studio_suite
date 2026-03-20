import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { Download, Refresh } from '@mui/icons-material'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { api } from '../services/api'
import { useBooking } from '../contexts/BookingContext'

type LegacySummary = {
  salons: number
  services: number
  bundles: number
  forfait_transactions: number
  fiche_lines: number
  edition1_days: number
}

type LegacyForfaitRow = { bundle_code: string; bundle_name: string; count: number; revenue: number }
type LegacyForfaitTxRow = { date_token: string; bundle_code: string; bundle_name: string; price: number }
type LegacyServiceWorkerRow = { worker_code: string; worker_name: string; service_code: string; service_name: string; qty: number; revenue: number }
type LegacyServiceAggregateRow = { service_code: string; service_name: string; qty: number; revenue: number }
type LegacyMonthlyRow = { month: string; days_count: number; gross_total: number; net_total: number; vat_total: number; tickets_count: number }
type LegacyDailyRow = { date: string; day_name: string; gross_total: number; net_total: number; vat_total: number; tickets_count: number }
type LegacyCashflowRow = { date: string; payment_hint: string; count: number; revenue: number }
type LegacyStat7WorkerRow = { worker_code: string; worker_name: string; total: number; payment_a: string; payment_b: string; payment_c: string }
type LegacyFicheServiceLineRow = {
  date_token: string
  time_label: string
  ticket_code: string
  line_code: string
  worker_code: string
  worker_name: string
  service_code: string
  service_name: string
  amount: number
  payment_hint: string
}

type MaterialByStaffRow = { staff_id?: number | null; staff_name?: string | null; services_count: number; lines_count: number; total_quantity: number; total_cost: number }
type MaterialByServiceRow = { service_id?: number | null; service_name?: string | null; lines_count: number; total_quantity: number; total_cost: number }
type MaterialDeviationRow = { staff_id?: number | null; staff_name?: string | null; lines_count: number; total_planned: number; total_actual: number; deviation: number }
type SalesBySalonRow = { salon_id: number; salon_name?: string | null; sales_count: number; transactions_count: number; lines_count: number; total_gross: number }
type PaymentsReportRow = { method: string; client_id?: number | null; client_name?: string | null; payments_count: number; total_amount: number; card_payments_count: number }
type ServiceDemandRow = { service_id?: number | null; service_name?: string | null; performed_count: number; avg_sold_price: number; avg_list_price: number; avg_discount: number; total_revenue: number }
type ServiceMarginRow = { service_id?: number | null; service_name?: string | null; performed_count: number; total_revenue: number; total_material_cost: number; total_margin: number; avg_margin_per_service: number }
type StaffPerformanceRow = { staff_id?: number | null; staff_name?: string | null; performed_count: number; total_revenue: number; total_material_cost: number; total_margin: number; avg_revenue_per_service: number; avg_margin_per_service: number }
type MaterialFamilyRow = { product_family?: string | null; lines_count: number; total_quantity: number; total_cost: number }
type BundleMarginRow = { bundle_id?: number | null; bundle_name?: string | null; performed_lines: number; appointments_count: number; total_revenue: number; total_material_cost: number; total_margin: number; avg_margin_per_appointment: number }
type RecipeDeviationServiceRow = { service_id?: number | null; service_name?: string | null; lines_count: number; total_planned: number; total_actual: number; deviation: number }
type PromotionRow = {
  id: number
  name: string
  promotion_type: string
  value: number
  salon_id?: number | null
  service_id?: number | null
  bundle_id?: number | null
  customer_tier?: string | null
  valid_from?: string | null
  valid_to?: string | null
  is_active: boolean
}

type PromotionForm = {
  name: string
  promotion_type: string
  value: string
  salon_id: number | ''
  service_id: number | ''
  bundle_id: number | ''
  customer_tier: string
  valid_from: string
  valid_to: string
  is_active: boolean
}

type ReportKey = 'forfaits_analysis' | 'forfaits_list' | 'services_worker' | 'services_lines' | 'services_aggregate' | 'daily_ed1' | 'monthly_ed1' | 'cashflow' | 'stat7'
type MainTab = 'legacy' | 'materials' | 'sales' | 'payments' | 'analytics'
type MaterialMode = 'by-staff' | 'by-service' | 'deviations'
type AnalyticsMode = 'demand' | 'margin' | 'bundle' | 'staff' | 'family' | 'deviation_staff' | 'deviation_service'
type AnalyticsSort = 'value_desc' | 'value_asc' | 'name_asc'
type LegacyWorkerSortBy = 'worker' | 'code' | 'service'
type LegacyWorkerSortDir = 'asc' | 'desc'
type LegacyForfaitSortBy = 'code' | 'name' | 'count' | 'revenue'
type LegacyAggregateSortBy = 'code' | 'name' | 'qty' | 'revenue'

const TABLE_SX = {
  '& .MuiTableHead-root .MuiTableCell-root': {
    backgroundColor: '#3a6ea5',
    color: '#fff',
    fontWeight: 700,
    borderBottom: '1px solid #98b3d1',
  },
  '& .MuiTableBody-root .MuiTableCell-root': {
    borderBottom: '1px solid #c5d5e6',
    fontSize: 13,
    paddingTop: '6px',
    paddingBottom: '6px',
  },
}

const downloadCsv = (filename: string, rows: Record<string, unknown>[]) => {
  if (!rows.length) return
  const headers = Object.keys(rows[0])
  const csv = [
    headers.join(','),
    ...rows.map((row) => headers.map((header) => JSON.stringify(row[header] ?? '')).join(',')),
  ].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

const moneyFmt = new Intl.NumberFormat('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const formatMoney = (value: number) => `${moneyFmt.format(Number.isFinite(value) ? value : 0)} PLN`

const formatDateToken = (value?: string) => {
  const token = (value || '').trim()
  if (/^\d{8}$/.test(token)) return `${token.slice(0, 4)}-${token.slice(4, 6)}-${token.slice(6, 8)}`
  return token
}

const isSalesServiceCode = (serviceCode?: string) => {
  const numeric = Number(String(serviceCode || '').replace(/\D/g, ''))
  return Number.isFinite(numeric) && numeric >= 200 && numeric <= 299
}

const emptyPromotionForm: PromotionForm = {
  name: '',
  promotion_type: 'fixed_discount',
  value: '0',
  salon_id: '',
  service_id: '',
  bundle_id: '',
  customer_tier: '',
  valid_from: '',
  valid_to: '',
  is_active: true,
}

const ReportsPage = () => {
  const today = new Date()
  const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`
  const todayToken = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  const { salons, services, bundles } = useBooking()
  const [mainTab, setMainTab] = useState<MainTab>('legacy')
  const [legacyMonth, setLegacyMonth] = useState(currentMonth)
  const [fromDate, setFromDate] = useState(todayToken.slice(0, 8) + '01')
  const [toDate, setToDate] = useState(todayToken)
  const [selectedReport, setSelectedReport] = useState<ReportKey>('forfaits_analysis')
  const [legacyWorkerSortBy, setLegacyWorkerSortBy] = useState<LegacyWorkerSortBy>('worker')
  const [legacyWorkerSortDir, setLegacyWorkerSortDir] = useState<LegacyWorkerSortDir>('asc')
  const [legacyWorkerFilter, setLegacyWorkerFilter] = useState<string>('')
  const [legacyServiceFilter, setLegacyServiceFilter] = useState<string>('')
  const [legacyLineSortBy, setLegacyLineSortBy] = useState<'date' | 'worker' | 'service' | 'ticket'>('date')
  const [legacyLineSortDir, setLegacyLineSortDir] = useState<'asc' | 'desc'>('desc')
  const [legacyTicketFilter, setLegacyTicketFilter] = useState<string>('')
  const [legacySalesFilter, setLegacySalesFilter] = useState<'all' | 'exclude_sales' | 'only_sales'>('all')
  const [legacyForfaitSortBy, setLegacyForfaitSortBy] = useState<LegacyForfaitSortBy>('revenue')
  const [legacyForfaitSortDir, setLegacyForfaitSortDir] = useState<'asc' | 'desc'>('desc')
  const [legacyForfaitSearch, setLegacyForfaitSearch] = useState<string>('')
  const [legacyAggSortBy, setLegacyAggSortBy] = useState<LegacyAggregateSortBy>('revenue')
  const [legacyAggSortDir, setLegacyAggSortDir] = useState<'asc' | 'desc'>('desc')
  const [legacyAggSearch, setLegacyAggSearch] = useState<string>('')
  const [materialMode, setMaterialMode] = useState<MaterialMode>('by-staff')
  const [analyticsMode, setAnalyticsMode] = useState<AnalyticsMode>('demand')
  const [analyticsTopN, setAnalyticsTopN] = useState<number>(10)
  const [analyticsSort, setAnalyticsSort] = useState<AnalyticsSort>('value_desc')
  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')

  const [legacyLoading, setLegacyLoading] = useState(false)
  const [legacyError, setLegacyError] = useState('')
  const [legacyImportBusy, setLegacyImportBusy] = useState(false)
  const [legacyImportInfo, setLegacyImportInfo] = useState('')
  const [legacyAvailableMonths, setLegacyAvailableMonths] = useState<string[]>([])
  const [legacyMonthTouched, setLegacyMonthTouched] = useState(false)
  const [opsLoading, setOpsLoading] = useState(false)
  const [opsError, setOpsError] = useState('')

  const [summary, setSummary] = useState<LegacySummary | null>(null)
  const [forfaits, setForfaits] = useState<LegacyForfaitRow[]>([])
  const [forfaitTx, setForfaitTx] = useState<LegacyForfaitTxRow[]>([])
  const [servicesWorker, setServicesWorker] = useState<LegacyServiceWorkerRow[]>([])
  const [servicesAgg, setServicesAgg] = useState<LegacyServiceAggregateRow[]>([])
  const [monthly, setMonthly] = useState<LegacyMonthlyRow[]>([])
  const [daily, setDaily] = useState<LegacyDailyRow[]>([])
  const [cashflow, setCashflow] = useState<LegacyCashflowRow[]>([])
  const [stat7, setStat7] = useState<LegacyStat7WorkerRow[]>([])
  const [ficheServiceLines, setFicheServiceLines] = useState<LegacyFicheServiceLineRow[]>([])

  const [materialByStaff, setMaterialByStaff] = useState<MaterialByStaffRow[]>([])
  const [materialByService, setMaterialByService] = useState<MaterialByServiceRow[]>([])
  const [materialDeviation, setMaterialDeviation] = useState<MaterialDeviationRow[]>([])
  const [salesBySalon, setSalesBySalon] = useState<SalesBySalonRow[]>([])
  const [paymentsReport, setPaymentsReport] = useState<PaymentsReportRow[]>([])
  const [serviceDemand, setServiceDemand] = useState<ServiceDemandRow[]>([])
  const [serviceMargin, setServiceMargin] = useState<ServiceMarginRow[]>([])
  const [bundleMargin, setBundleMargin] = useState<BundleMarginRow[]>([])
  const [staffPerformance, setStaffPerformance] = useState<StaffPerformanceRow[]>([])
  const [materialByFamily, setMaterialByFamily] = useState<MaterialFamilyRow[]>([])
  const [recipeDeviationStaff, setRecipeDeviationStaff] = useState<MaterialDeviationRow[]>([])
  const [recipeDeviationService, setRecipeDeviationService] = useState<RecipeDeviationServiceRow[]>([])
  const [promotions, setPromotions] = useState<PromotionRow[]>([])
  const [promotionLoading, setPromotionLoading] = useState(false)
  const [promotionError, setPromotionError] = useState('')
  const [promotionInfo, setPromotionInfo] = useState('')
  const [promotionEditingId, setPromotionEditingId] = useState<number | null>(null)
  const [promotionForm, setPromotionForm] = useState<PromotionForm>(emptyPromotionForm)

  useEffect(() => {
    if (selectedSalonId === '' && salons.length) {
      const preferred = salons.find((row) => (row.code || '').trim() === '05') || salons[0]
      setSelectedSalonId(preferred.id)
    }
  }, [salons, selectedSalonId])

  useEffect(() => {
    setLegacyMonthTouched(false)
  }, [selectedSalonId])

  useEffect(() => {
    const [yearRaw, monthRaw] = legacyMonth.split('-')
    const year = Number(yearRaw)
    const month = Number(monthRaw)
    if (!year || !month) return
    const firstDay = `${yearRaw}-${monthRaw}-01`
    const isCurrentMonth = legacyMonth === currentMonth
    if (isCurrentMonth) {
      setFromDate(firstDay)
      setToDate(todayToken)
      return
    }
    const lastDate = new Date(year, month, 0).getDate()
    const lastDay = `${yearRaw}-${monthRaw}-${String(lastDate).padStart(2, '0')}`
    setFromDate(firstDay)
    setToDate(lastDay)
  }, [legacyMonth, currentMonth, todayToken])

  const fetchLegacyMonths = useCallback(async () => {
    if (selectedSalonId === '') {
      setLegacyAvailableMonths([])
      return
    }
    try {
      const params = { salon_id: selectedSalonId }
      const res = await api.get<{ months: string[] }>('/legacy/reports/available-months', { params })
      const months = (res.data?.months || []).filter(Boolean)
      setLegacyAvailableMonths(months)
      if (months.length && (!legacyMonthTouched || !months.includes(legacyMonth))) {
        setLegacyMonth(months[0])
      }
    } catch (error) {
      console.error(error)
      setLegacyAvailableMonths([])
    }
  }, [legacyMonth, legacyMonthTouched, selectedSalonId])

  useEffect(() => {
    fetchLegacyMonths()
  }, [fetchLegacyMonths])

  const fetchLegacyReports = useCallback(async () => {
    if (selectedSalonId === '') return
    setLegacyLoading(true)
    setLegacyError('')
    try {
      const params = {
        from_date: fromDate,
        to_date: toDate,
        salon_id: selectedSalonId,
      }
      const [summaryRes, forfaitsRes, forfaitTxRes, servicesWorkerRes, servicesAggRes, monthlyRes, dailyRes, cashflowRes, stat7Res, ficheServiceLinesRes] = await Promise.all([
        api.get('/legacy/reports/summary'),
        api.get('/legacy/reports/forfaits', { params }),
        api.get('/legacy/reports/forfait-transactions', { params }),
        api.get('/legacy/reports/services-by-worker', { params }),
        api.get('/legacy/reports/services-aggregate', { params }),
        api.get('/legacy/reports/monthly-summary', { params }),
        api.get('/legacy/reports/daily-summary', { params }),
        api.get('/legacy/reports/cashflow', { params }),
        api.get('/legacy/reports/stat7-worker'),
        api.get('/legacy/reports/fiche-service-lines', { params }),
      ])
      setSummary(summaryRes.data)
      setForfaits(forfaitsRes.data.rows || [])
      setForfaitTx(forfaitTxRes.data.rows || [])
      setServicesWorker(servicesWorkerRes.data.rows || [])
      setServicesAgg(servicesAggRes.data.rows || [])
      setMonthly(monthlyRes.data.rows || [])
      setDaily(dailyRes.data.rows || [])
      setCashflow(cashflowRes.data.rows || [])
      setStat7(stat7Res.data.rows || [])
      setFicheServiceLines(ficheServiceLinesRes.data.rows || [])
    } catch (error) {
      console.error(error)
      setLegacyError('Nie udalo sie pobrac raportow legacy.')
    } finally {
      setLegacyLoading(false)
    }
  }, [fromDate, toDate, selectedSalonId])

  useEffect(() => {
    if (mainTab !== 'legacy') return
    fetchLegacyReports()
  }, [fetchLegacyReports, mainTab])

  const fetchOperational = async () => {
    setOpsLoading(true)
    setOpsError('')
    try {
      const params = {
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
        salon_id: selectedSalonId === '' ? undefined : selectedSalonId,
      }
      const [staffRes, serviceRes, deviationRes, salesRes, paymentsRes, demandRes, marginRes, bundleRes, perfRes, familyRes, recipeDeviationStaffRes, recipeDeviationServiceRes] = await Promise.all([
        api.get('/reports/material-usage/by-staff', { params }),
        api.get('/reports/material-cost/by-service', { params }),
        api.get('/reports/deviation/by-staff', { params }),
        api.get('/reports/sales/by-salon', { params }),
        api.get('/reports/payments', { params }),
        api.get('/reports/service-demand', { params }),
        api.get('/reports/service-margin', { params }),
        api.get('/reports/bundle-margin', { params }),
        api.get('/reports/staff-performance', { params }),
        api.get('/reports/material-usage/by-family', { params }),
        api.get('/reports/recipe-deviation/by-staff', { params }),
        api.get('/reports/recipe-deviation/by-service', { params }),
      ])
      setMaterialByStaff(staffRes.data.rows || [])
      setMaterialByService(serviceRes.data.rows || [])
      setMaterialDeviation(deviationRes.data.rows || [])
      setSalesBySalon(salesRes.data.rows || [])
      setPaymentsReport(paymentsRes.data.rows || [])
      setServiceDemand(demandRes.data.rows || [])
      setServiceMargin(marginRes.data.rows || [])
      setBundleMargin(bundleRes.data.rows || [])
      setStaffPerformance(perfRes.data.rows || [])
      setMaterialByFamily(familyRes.data.rows || [])
      setRecipeDeviationStaff(recipeDeviationStaffRes.data.rows || [])
      setRecipeDeviationService(recipeDeviationServiceRes.data.rows || [])
    } catch (error: any) {
      console.error(error)
      setOpsError(error?.response?.data?.detail || 'Nie udalo sie pobrac raportow operacyjnych.')
    } finally {
      setOpsLoading(false)
    }
  }

  const fetchPromotions = async () => {
    setPromotionLoading(true)
    setPromotionError('')
    try {
      const params = {
        salon_id: selectedSalonId === '' ? undefined : selectedSalonId,
      }
      const res = await api.get<PromotionRow[]>('/payments/promotions', { params })
      setPromotions(res.data || [])
    } catch (error: any) {
      console.error(error)
      setPromotionError(error?.response?.data?.detail || 'Nie udalo sie pobrac promocji.')
      setPromotions([])
    } finally {
      setPromotionLoading(false)
    }
  }

  useEffect(() => {
    if (mainTab === 'legacy') return
    if (selectedSalonId === '') return
    fetchOperational()
  }, [fromDate, toDate, selectedSalonId, mainTab])

  useEffect(() => {
    if (mainTab !== 'payments') return
    if (selectedSalonId === '') return
    fetchPromotions().catch(() => undefined)
  }, [selectedSalonId, mainTab])

  const rebuildLegacyFiche = async () => {
    setLegacyImportBusy(true)
    setLegacyImportInfo('')
    setLegacyError('')
    try {
      const res = await api.post<{ fiche_lines: number; forfait_transactions: number }>('/legacy/reports/rebuild-fiche')
      setLegacyImportInfo(
        `Import fiszek zakonczony. Linie fiszek: ${res.data.fiche_lines}, transakcje forfetow: ${res.data.forfait_transactions}.`,
      )
      await fetchLegacyReports()
      await fetchLegacyMonths()
    } catch (error) {
      console.error(error)
      setLegacyError('Nie udalo sie przebudowac bazy fiszek legacy.')
    } finally {
      setLegacyImportBusy(false)
    }
  }

  const resetPromotionForm = () => {
    setPromotionEditingId(null)
    setPromotionForm(emptyPromotionForm)
  }

  const startEditPromotion = (row: PromotionRow) => {
    setPromotionEditingId(row.id)
    setPromotionForm({
      name: row.name,
      promotion_type: row.promotion_type,
      value: String(row.value),
      salon_id: row.salon_id ?? '',
      service_id: row.service_id ?? '',
      bundle_id: row.bundle_id ?? '',
      customer_tier: row.customer_tier || '',
      valid_from: row.valid_from || '',
      valid_to: row.valid_to || '',
      is_active: row.is_active,
    })
    setPromotionError('')
    setPromotionInfo('')
  }

  const savePromotion = async () => {
    setPromotionError('')
    setPromotionInfo('')
    try {
      const payload = {
        name: promotionForm.name.trim(),
        promotion_type: promotionForm.promotion_type,
        value: Number(promotionForm.value),
        salon_id: promotionForm.salon_id === '' ? null : promotionForm.salon_id,
        service_id: promotionForm.service_id === '' ? null : promotionForm.service_id,
        bundle_id: promotionForm.bundle_id === '' ? null : promotionForm.bundle_id,
        customer_tier: promotionForm.customer_tier.trim() || null,
        valid_from: promotionForm.valid_from || null,
        valid_to: promotionForm.valid_to || null,
        is_active: promotionForm.is_active,
      }
      if (promotionEditingId) {
        await api.patch(`/payments/promotions/${promotionEditingId}`, payload)
        setPromotionInfo('Promocja zostala zaktualizowana.')
      } else {
        await api.post('/payments/promotions', payload)
        setPromotionInfo('Promocja zostala dodana.')
      }
      resetPromotionForm()
      await fetchPromotions()
    } catch (error: any) {
      console.error(error)
      setPromotionError(error?.response?.data?.detail || 'Nie udalo sie zapisac promocji.')
    }
  }

  const deletePromotion = async (promotionId: number) => {
    if (!window.confirm('Usunac promocje?')) return
    setPromotionError('')
    setPromotionInfo('')
    try {
      await api.delete(`/payments/promotions/${promotionId}`)
      setPromotionInfo('Promocja zostala usunieta.')
      if (promotionEditingId === promotionId) resetPromotionForm()
      await fetchPromotions()
    } catch (error: any) {
      console.error(error)
      setPromotionError(error?.response?.data?.detail || 'Nie udalo sie usunac promocji.')
    }
  }

  const renderLegacyReport = () => {
    if (selectedReport === 'forfaits_analysis') {
      return filteredForfaits.map((row) => ({ Kod: row.bundle_code, Nazwa: row.bundle_name, Ilosc: row.count, Suma: formatMoney(row.revenue) }))
    }
    if (selectedReport === 'forfaits_list') {
      return forfaitTx.map((row) => ({ Data: formatDateToken(row.date_token), Kod: row.bundle_code, Nazwa: row.bundle_name, Cena: formatMoney(row.price) }))
    }
    if (selectedReport === 'services_worker') {
      return filteredServicesWorker.map((row) => ({ Pracownik: row.worker_name || row.worker_code, Kod: row.service_code, Usluga: row.service_name, Ilosc: row.qty, Suma: formatMoney(row.revenue) }))
    }
    if (selectedReport === 'services_lines') {
      return filteredFicheServiceLines.map((row) => ({
        Data: formatDateToken(row.date_token),
        Godzina: row.time_label || '-',
        Fiszka: row.ticket_code,
        Linia: row.line_code,
        Pracownik: row.worker_name || row.worker_code,
        Kod: row.service_code,
        Usluga: row.service_name,
        Typ: isSalesServiceCode(row.service_code) ? 'Sprzedaż (200-299)' : 'Usługa',
        Kwota: formatMoney(row.amount),
        Platnosc: row.payment_hint || '-',
      }))
    }
    if (selectedReport === 'services_aggregate') {
      return filteredServicesAgg.map((row) => ({ Kod: row.service_code, Usluga: row.service_name, Ilosc: row.qty, Suma: formatMoney(row.revenue) }))
    }
    if (selectedReport === 'daily_ed1') {
      return daily.map((row) => ({ Data: formatDateToken(row.date), Dzien: row.day_name, Brutto: formatMoney(row.gross_total), Netto: formatMoney(row.net_total), VAT: formatMoney(row.vat_total), Paragony: row.tickets_count }))
    }
    if (selectedReport === 'monthly_ed1') {
      return monthly.map((row) => ({ Miesiac: row.month, Dni: row.days_count, Brutto: formatMoney(row.gross_total), Netto: formatMoney(row.net_total), VAT: formatMoney(row.vat_total), Paragony: row.tickets_count }))
    }
    if (selectedReport === 'cashflow') {
      return cashflow.map((row) => ({ Data: formatDateToken(row.date), Platnosc: row.payment_hint, Ilosc: row.count, Suma: formatMoney(row.revenue) }))
    }
    return stat7.map((row) => ({ Kod: row.worker_code, Pracownik: row.worker_name, Suma: formatMoney(row.total), A: row.payment_a, B: row.payment_b, C: row.payment_c }))
  }

  const legacyMonthOptions = useMemo(() => {
    const source = Array.from(new Set([...(legacyAvailableMonths || []), ...(monthly || []).map((row) => row.month).filter(Boolean)]))
    return source.sort((a, b) => (a < b ? 1 : -1))
  }, [legacyAvailableMonths, monthly])

  const legacyRevenueTotal = useMemo(
    () => daily.reduce((sum, row) => sum + (row.gross_total || 0), 0),
    [daily],
  )
  const legacyTicketsTotal = useMemo(
    () => daily.reduce((sum, row) => sum + (row.tickets_count || 0), 0),
    [daily],
  )
  const legacyAverageTicket = useMemo(
    () => (legacyTicketsTotal > 0 ? legacyRevenueTotal / legacyTicketsTotal : 0),
    [legacyRevenueTotal, legacyTicketsTotal],
  )
  const legacyTopService = useMemo(
    () => (servicesAgg.length ? servicesAgg[0] : null),
    [servicesAgg],
  )
  const legacyTopBundle = useMemo(
    () => (forfaits.length ? forfaits[0] : null),
    [forfaits],
  )
  const legacyTopWorkers = useMemo(() => {
    const byWorker = new Map<string, { worker: string; qty: number; revenue: number }>()
    servicesWorker.forEach((row) => {
      const worker = row.worker_name || row.worker_code || '-'
      const current = byWorker.get(worker) || { worker, qty: 0, revenue: 0 }
      current.qty += row.qty || 0
      current.revenue += row.revenue || 0
      byWorker.set(worker, current)
    })
    return Array.from(byWorker.values()).sort((a, b) => b.revenue - a.revenue).slice(0, 5)
  }, [servicesWorker])
  const legacyPaymentMix = useMemo(() => {
    const byPayment = new Map<string, number>()
    cashflow.forEach((row) => {
      const key = (row.payment_hint || 'NIEOKRESLONA').toUpperCase()
      byPayment.set(key, (byPayment.get(key) || 0) + (row.revenue || 0))
    })
    return Array.from(byPayment.entries())
      .map(([payment, value]) => ({ payment, value }))
      .sort((a, b) => b.value - a.value)
  }, [cashflow])
  const legacyTopServices = useMemo(
    () => servicesAgg.slice(0, 10).map((row) => ({
      Usluga: row.service_name || row.service_code,
      Kod: row.service_code,
      Ilosc: row.qty,
      Przychod: formatMoney(row.revenue),
    })),
    [servicesAgg],
  )
  const legacyTopBundles = useMemo(
    () => forfaits.slice(0, 10).map((row) => ({
      Forfet: row.bundle_name || row.bundle_code,
      Kod: row.bundle_code,
      Ilosc: row.count,
      Przychod: formatMoney(row.revenue),
    })),
    [forfaits],
  )
  const legacyTopWorkersRows = useMemo(
    () =>
      legacyTopWorkers.map((row) => ({
        Pracownik: row.worker,
        Ilosc: row.qty,
        Przychod: formatMoney(row.revenue),
      })),
    [legacyTopWorkers],
  )

  const sortedServicesWorker = useMemo(() => {
    const rows = [...servicesWorker]
    rows.sort((a, b) => {
      let left = ''
      let right = ''
      if (legacyWorkerSortBy === 'worker') {
        left = String(a.worker_name || a.worker_code || '')
        right = String(b.worker_name || b.worker_code || '')
      } else if (legacyWorkerSortBy === 'code') {
        left = String(a.service_code || '')
        right = String(b.service_code || '')
      } else {
        left = String(a.service_name || '')
        right = String(b.service_name || '')
      }
      const cmp = left.localeCompare(right, 'pl', { numeric: true, sensitivity: 'base' })
      return legacyWorkerSortDir === 'asc' ? cmp : -cmp
    })
    return rows
  }, [servicesWorker, legacyWorkerSortBy, legacyWorkerSortDir])

  const workerFilterOptions = useMemo(
    () =>
      Array.from(
        new Set(
          [
            ...servicesWorker.map((row) => row.worker_name || row.worker_code),
            ...ficheServiceLines.map((row) => row.worker_name || row.worker_code),
          ].filter((row): row is string => Boolean(row)),
        ),
      ).sort((a, b) => a.localeCompare(b, 'pl', { sensitivity: 'base', numeric: true })),
    [servicesWorker, ficheServiceLines],
  )

  const serviceFilterOptions = useMemo(
    () =>
      Array.from(
        new Set(
          [
            ...servicesWorker.map((row) => row.service_name || row.service_code),
            ...ficheServiceLines.map((row) => row.service_name || row.service_code),
          ].filter((row): row is string => Boolean(row)),
        ),
      ).sort((a, b) => a.localeCompare(b, 'pl', { sensitivity: 'base', numeric: true })),
    [servicesWorker, ficheServiceLines],
  )

  const filteredServicesWorker = useMemo(() => {
    return sortedServicesWorker.filter((row) => {
      const worker = row.worker_name || row.worker_code || ''
      const service = row.service_name || row.service_code || ''
      const workerOk = !legacyWorkerFilter || worker === legacyWorkerFilter
      const serviceOk = !legacyServiceFilter || service === legacyServiceFilter
      const isSales = isSalesServiceCode(row.service_code)
      const salesOk =
        legacySalesFilter === 'all'
          ? true
          : legacySalesFilter === 'only_sales'
          ? isSales
          : !isSales
      return workerOk && serviceOk && salesOk
    })
  }, [sortedServicesWorker, legacyWorkerFilter, legacyServiceFilter, legacySalesFilter])

  const filteredFicheServiceLines = useMemo(() => {
    const filtered = ficheServiceLines.filter((row) => {
      const worker = row.worker_name || row.worker_code || ''
      const service = row.service_name || row.service_code || ''
      const workerOk = !legacyWorkerFilter || worker === legacyWorkerFilter
      const serviceOk = !legacyServiceFilter || service === legacyServiceFilter
      const ticketOk = !legacyTicketFilter || (row.ticket_code || '').toLowerCase().includes(legacyTicketFilter.toLowerCase())
      const isSales = isSalesServiceCode(row.service_code)
      const salesOk =
        legacySalesFilter === 'all'
          ? true
          : legacySalesFilter === 'only_sales'
          ? isSales
          : !isSales
      return workerOk && serviceOk && ticketOk && salesOk
    })
    filtered.sort((a, b) => {
      const left =
        legacyLineSortBy === 'worker'
          ? (a.worker_name || a.worker_code || '')
          : legacyLineSortBy === 'service'
          ? (a.service_name || a.service_code || '')
          : legacyLineSortBy === 'ticket'
          ? `${a.date_token || ''}-${a.ticket_code || ''}`
          : `${a.date_token || ''}-${a.ticket_code || ''}-${a.line_code || ''}`
      const right =
        legacyLineSortBy === 'worker'
          ? (b.worker_name || b.worker_code || '')
          : legacyLineSortBy === 'service'
          ? (b.service_name || b.service_code || '')
          : legacyLineSortBy === 'ticket'
          ? `${b.date_token || ''}-${b.ticket_code || ''}`
          : `${b.date_token || ''}-${b.ticket_code || ''}-${b.line_code || ''}`
      const cmp = String(left).localeCompare(String(right), 'pl', { sensitivity: 'base', numeric: true })
      return legacyLineSortDir === 'asc' ? cmp : -cmp
    })
    return filtered
  }, [ficheServiceLines, legacyLineSortBy, legacyLineSortDir, legacyWorkerFilter, legacyServiceFilter, legacyTicketFilter, legacySalesFilter])

  const filteredForfaits = useMemo(() => {
    const q = legacyForfaitSearch.trim().toLowerCase()
    const filtered = forfaits.filter((row) => {
      if (!q) return true
      return (
        (row.bundle_code || '').toLowerCase().includes(q) ||
        (row.bundle_name || '').toLowerCase().includes(q)
      )
    })
    filtered.sort((a, b) => {
      const left =
        legacyForfaitSortBy === 'code'
          ? a.bundle_code
          : legacyForfaitSortBy === 'name'
          ? a.bundle_name
          : legacyForfaitSortBy === 'count'
          ? String(a.count)
          : String(a.revenue)
      const right =
        legacyForfaitSortBy === 'code'
          ? b.bundle_code
          : legacyForfaitSortBy === 'name'
          ? b.bundle_name
          : legacyForfaitSortBy === 'count'
          ? String(b.count)
          : String(b.revenue)
      const cmp =
        legacyForfaitSortBy === 'count' || legacyForfaitSortBy === 'revenue'
          ? Number(left) - Number(right)
          : String(left).localeCompare(String(right), 'pl', { numeric: true, sensitivity: 'base' })
      return legacyForfaitSortDir === 'asc' ? cmp : -cmp
    })
    return filtered
  }, [forfaits, legacyForfaitSearch, legacyForfaitSortBy, legacyForfaitSortDir])

  const filteredServicesAgg = useMemo(() => {
    const q = legacyAggSearch.trim().toLowerCase()
    const filtered = servicesAgg.filter((row) => {
      const qOk =
        !q ||
        (row.service_code || '').toLowerCase().includes(q) ||
        (row.service_name || '').toLowerCase().includes(q)
      const isSales = isSalesServiceCode(row.service_code)
      const salesOk =
        legacySalesFilter === 'all'
          ? true
          : legacySalesFilter === 'only_sales'
          ? isSales
          : !isSales
      return qOk && salesOk
    })
    filtered.sort((a, b) => {
      const left =
        legacyAggSortBy === 'code'
          ? a.service_code
          : legacyAggSortBy === 'name'
          ? a.service_name
          : legacyAggSortBy === 'qty'
          ? String(a.qty)
          : String(a.revenue)
      const right =
        legacyAggSortBy === 'code'
          ? b.service_code
          : legacyAggSortBy === 'name'
          ? b.service_name
          : legacyAggSortBy === 'qty'
          ? String(b.qty)
          : String(b.revenue)
      const cmp =
        legacyAggSortBy === 'qty' || legacyAggSortBy === 'revenue'
          ? Number(left) - Number(right)
          : String(left).localeCompare(String(right), 'pl', { numeric: true, sensitivity: 'base' })
      return legacyAggSortDir === 'asc' ? cmp : -cmp
    })
    return filtered
  }, [servicesAgg, legacyAggSearch, legacyAggSortBy, legacyAggSortDir, legacySalesFilter])

  const servicesWorkerSummary = useMemo(() => {
    const rowsCount = filteredServicesWorker.length
    const qtyTotal = filteredServicesWorker.reduce((sum, row) => sum + (row.qty || 0), 0)
    const amountTotal = filteredServicesWorker.reduce((sum, row) => sum + (row.revenue || 0), 0)
    return { rowsCount, qtyTotal, amountTotal }
  }, [filteredServicesWorker])

  const materialRows = useMemo(() => {
    if (materialMode === 'by-staff') return materialByStaff.map((row) => ({ Pracownik: row.staff_name || row.staff_id || '-', Uslugi: row.services_count, Linie: row.lines_count, Ilosc: row.total_quantity.toFixed(2), Koszt: row.total_cost.toFixed(2) }))
    if (materialMode === 'by-service') return materialByService.map((row) => ({ Usluga: row.service_name || row.service_id || '-', Linie: row.lines_count, Ilosc: row.total_quantity.toFixed(2), Koszt: row.total_cost.toFixed(2) }))
    return materialDeviation.map((row) => ({ Pracownik: row.staff_name || row.staff_id || '-', Linie: row.lines_count, Plan: row.total_planned.toFixed(2), Faktycznie: row.total_actual.toFixed(2), Odchylenie: row.deviation.toFixed(2) }))
  }, [materialByService, materialByStaff, materialDeviation, materialMode])

  const salesTotal = useMemo(() => salesBySalon.reduce((sum, row) => sum + row.total_gross, 0), [salesBySalon])
  const paymentsTotal = useMemo(() => paymentsReport.reduce((sum, row) => sum + row.total_amount, 0), [paymentsReport])
  const analyticsSourceRows = useMemo<Record<string, unknown>[]>(() => {
    if (analyticsMode === 'demand') {
      return serviceDemand.map((row) => ({
        Usluga: row.service_name || row.service_id || '-',
        Wykonania: row.performed_count,
        SredniaSprzedaz: row.avg_sold_price.toFixed(2),
        SredniaCennik: row.avg_list_price.toFixed(2),
        SredniRabat: row.avg_discount.toFixed(2),
        Przychod: row.total_revenue.toFixed(2),
      }))
    }
    if (analyticsMode === 'margin') {
      return serviceMargin.map((row) => ({
        Usluga: row.service_name || row.service_id || '-',
        Wykonania: row.performed_count,
        Przychod: row.total_revenue.toFixed(2),
        KosztMaterialow: row.total_material_cost.toFixed(2),
        Marza: row.total_margin.toFixed(2),
        SredniaMarza: row.avg_margin_per_service.toFixed(2),
      }))
    }
    if (analyticsMode === 'bundle') {
      return bundleMargin.map((row) => ({
        Forfet: row.bundle_name || row.bundle_id || '-',
        Wizyty: row.appointments_count,
        Linie: row.performed_lines,
        Przychod: row.total_revenue.toFixed(2),
        KosztMaterialow: row.total_material_cost.toFixed(2),
        Marza: row.total_margin.toFixed(2),
        SredniaMarzaNaWizyte: row.avg_margin_per_appointment.toFixed(2),
      }))
    }
    if (analyticsMode === 'staff') {
      return staffPerformance.map((row) => ({
        Pracownik: row.staff_name || row.staff_id || '-',
        Wykonania: row.performed_count,
        Przychod: row.total_revenue.toFixed(2),
        KosztMaterialow: row.total_material_cost.toFixed(2),
        Marza: row.total_margin.toFixed(2),
        SredniPrzychod: row.avg_revenue_per_service.toFixed(2),
        SredniaMarza: row.avg_margin_per_service.toFixed(2),
      }))
    }
    if (analyticsMode === 'deviation_staff') {
      return recipeDeviationStaff.map((row) => ({
        Pracownik: row.staff_name || row.staff_id || '-',
        Linie: row.lines_count,
        Plan: row.total_planned.toFixed(2),
        Faktycznie: row.total_actual.toFixed(2),
        Odchylenie: row.deviation.toFixed(2),
      }))
    }
    if (analyticsMode === 'deviation_service') {
      return recipeDeviationService.map((row) => ({
        Usluga: row.service_name || row.service_id || '-',
        Linie: row.lines_count,
        Plan: row.total_planned.toFixed(2),
        Faktycznie: row.total_actual.toFixed(2),
        Odchylenie: row.deviation.toFixed(2),
      }))
    }
    return materialByFamily.map((row) => ({
      Rodzina: row.product_family || '-',
      Linie: row.lines_count,
      Ilosc: row.total_quantity.toFixed(2),
      Koszt: row.total_cost.toFixed(2),
    }))
  }, [analyticsMode, bundleMargin, materialByFamily, recipeDeviationService, recipeDeviationStaff, serviceDemand, serviceMargin, staffPerformance])
  const analyticsRows = useMemo(() => {
    const rows = [...analyticsSourceRows]
    const getNumericValue = (row: Record<string, unknown>) => {
      const key = analyticsMode === 'demand'
        ? 'Przychod'
        : analyticsMode === 'margin'
        ? 'Marza'
        : analyticsMode === 'bundle'
        ? 'Marza'
        : analyticsMode === 'staff'
        ? 'Marza'
        : analyticsMode === 'deviation_staff' || analyticsMode === 'deviation_service'
        ? 'Odchylenie'
        : 'Koszt'
      return Number(String(row[key] ?? '0').replace(',', '.'))
    }
    const getNameValue = (row: Record<string, unknown>) => {
      const key =
        analyticsMode === 'staff' || analyticsMode === 'deviation_staff'
          ? 'Pracownik'
          : analyticsMode === 'family'
          ? 'Rodzina'
          : analyticsMode === 'bundle'
          ? 'Forfet'
          : 'Usluga'
      return String(row[key] ?? '')
    }
    rows.sort((a, b) => {
      if (analyticsSort === 'name_asc') return getNameValue(a).localeCompare(getNameValue(b), 'pl')
      if (analyticsSort === 'value_asc') return getNumericValue(a) - getNumericValue(b)
      return getNumericValue(b) - getNumericValue(a)
    })
    return rows.slice(0, Math.max(1, analyticsTopN))
  }, [analyticsMode, analyticsSort, analyticsSourceRows, analyticsTopN])
  const analyticsChartData = useMemo(() => {
    if (analyticsMode === 'demand') {
      return serviceDemand.slice(0, analyticsTopN).map((row) => ({
        name: row.service_name || String(row.service_id || '-'),
        revenue: row.total_revenue,
        sold: row.avg_sold_price,
        list: row.avg_list_price,
      }))
    }
    if (analyticsMode === 'margin') {
      return serviceMargin.slice(0, analyticsTopN).map((row) => ({
        name: row.service_name || String(row.service_id || '-'),
        margin: row.total_margin,
        cost: row.total_material_cost,
      }))
    }
    if (analyticsMode === 'bundle') {
      return bundleMargin.slice(0, analyticsTopN).map((row) => ({
        name: row.bundle_name || String(row.bundle_id || '-'),
        margin: row.total_margin,
        revenue: row.total_revenue,
      }))
    }
    if (analyticsMode === 'staff') {
      return staffPerformance.slice(0, analyticsTopN).map((row) => ({
        name: row.staff_name || String(row.staff_id || '-'),
        revenue: row.total_revenue,
        margin: row.total_margin,
      }))
    }
    if (analyticsMode === 'deviation_staff') {
      return recipeDeviationStaff.slice(0, analyticsTopN).map((row) => ({
        name: row.staff_name || String(row.staff_id || '-'),
        planned: row.total_planned,
        actual: row.total_actual,
        deviation: row.deviation,
      }))
    }
    if (analyticsMode === 'deviation_service') {
      return recipeDeviationService.slice(0, analyticsTopN).map((row) => ({
        name: row.service_name || String(row.service_id || '-'),
        planned: row.total_planned,
        actual: row.total_actual,
        deviation: row.deviation,
      }))
    }
    return materialByFamily.slice(0, analyticsTopN).map((row) => ({
      name: row.product_family || '-',
      cost: row.total_cost,
      qty: row.total_quantity,
    }))
  }, [analyticsMode, analyticsTopN, bundleMargin, materialByFamily, recipeDeviationService, recipeDeviationStaff, serviceDemand, serviceMargin, staffPerformance])

  const renderGenericTable = (rows: Record<string, unknown>[]) => {
    if (!rows.length) return <Typography color="text.secondary">Brak danych dla wybranego zakresu.</Typography>
    const headers = Object.keys(rows[0])
    return (
      <TableContainer>
        <Table size="small" sx={TABLE_SX}>
          <TableHead>
            <TableRow>
              {headers.map((header) => <TableCell key={header}>{header}</TableCell>)}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, index) => (
              <TableRow key={index}>
                {headers.map((header) => <TableCell key={header}>{String(row[header] ?? '')}</TableCell>)}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    )
  }

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1.5}>
        <Typography variant="h4">Raporty</Typography>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
          {mainTab === 'legacy' ? (
            <>
              <FormControl size="small" sx={{ minWidth: 180 }}>
                <InputLabel>Miesiac legacy</InputLabel>
                <Select
                  label="Miesiac legacy"
                  value={legacyMonth}
                  onChange={(e) => {
                    setLegacyMonthTouched(true)
                    setLegacyMonth(String(e.target.value))
                  }}
                >
                  {legacyMonthOptions.map((month) => (
                    <MenuItem key={month} value={month}>{month}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField size="small" type="date" label="Od" InputLabelProps={{ shrink: true }} value={fromDate} disabled />
              <TextField size="small" type="date" label="Do" InputLabelProps={{ shrink: true }} value={toDate} disabled />
            </>
          ) : (
            <>
              <TextField size="small" type="date" label="Od" InputLabelProps={{ shrink: true }} value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
              <TextField size="small" type="date" label="Do" InputLabelProps={{ shrink: true }} value={toDate} onChange={(e) => setToDate(e.target.value)} />
            </>
          )}
          <FormControl size="small" sx={{ minWidth: 220 }}>
            <InputLabel>Salon</InputLabel>
            <Select label="Salon" value={selectedSalonId} onChange={(e) => setSelectedSalonId(e.target.value === '' ? '' : Number(e.target.value))}>
              <MenuItem value="">Wszystkie</MenuItem>
              {salons.map((salon) => <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>)}
            </Select>
          </FormControl>
          <Button startIcon={<Refresh />} onClick={fetchOperational}>Odswiez</Button>
        </Stack>
      </Stack>

      <Tabs value={mainTab} onChange={(_, value) => setMainTab(value)}>
        <Tab value="legacy" label="Legacy" />
        <Tab value="materials" label="Materialy" />
        <Tab value="sales" label="Sprzedaz" />
        <Tab value="payments" label="Rozliczenia" />
        <Tab value="analytics" label="Analityka" />
      </Tabs>

      {legacyError && mainTab === 'legacy' && <Alert severity="error">{legacyError}</Alert>}
      {legacyImportInfo && mainTab === 'legacy' && <Alert severity="success">{legacyImportInfo}</Alert>}
      {opsError && mainTab !== 'legacy' && <Alert severity="error">{opsError}</Alert>}
      {legacyLoading && mainTab === 'legacy' && <Alert severity="info">Ladowanie raportow legacy...</Alert>}
      {opsLoading && mainTab !== 'legacy' && <Alert severity="info">Ladowanie raportow operacyjnych...</Alert>}

      {mainTab === 'legacy' && (
        <Stack spacing={2}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={2}><Card><CardContent><Typography variant="overline">Salony</Typography><Typography variant="h4">{summary?.salons ?? 0}</Typography></CardContent></Card></Grid>
            <Grid item xs={12} md={2}><Card><CardContent><Typography variant="overline">Uslugi</Typography><Typography variant="h4">{summary?.services ?? 0}</Typography></CardContent></Card></Grid>
            <Grid item xs={12} md={2}><Card><CardContent><Typography variant="overline">Pakiety</Typography><Typography variant="h4">{summary?.bundles ?? 0}</Typography></CardContent></Card></Grid>
            <Grid item xs={12} md={3}><Card><CardContent><Typography variant="overline">Transakcje forfait</Typography><Typography variant="h4">{summary?.forfait_transactions ?? 0}</Typography></CardContent></Card></Grid>
            <Grid item xs={12} md={3}><Card><CardContent><Typography variant="overline">Fiche lines</Typography><Typography variant="h4">{summary?.fiche_lines ?? 0}</Typography></CardContent></Card></Grid>
          </Grid>

          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Manager KPI (legacy)</Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={2.4}><Card variant="outlined"><CardContent><Typography variant="overline">Przychod miesiaca</Typography><Typography variant="h5">{formatMoney(legacyRevenueTotal)}</Typography></CardContent></Card></Grid>
                <Grid item xs={12} md={2.4}><Card variant="outlined"><CardContent><Typography variant="overline">Liczba fiszek</Typography><Typography variant="h5">{legacyTicketsTotal}</Typography></CardContent></Card></Grid>
                <Grid item xs={12} md={2.4}><Card variant="outlined"><CardContent><Typography variant="overline">Srednia fiskza</Typography><Typography variant="h5">{formatMoney(legacyAverageTicket)}</Typography></CardContent></Card></Grid>
                <Grid item xs={12} md={2.4}><Card variant="outlined"><CardContent><Typography variant="overline">Top usluga</Typography><Typography variant="body1" sx={{ fontWeight: 700 }}>{legacyTopService?.service_name || '-'}</Typography><Typography color="text.secondary">{legacyTopService ? formatMoney(legacyTopService.revenue) : '-'}</Typography></CardContent></Card></Grid>
                <Grid item xs={12} md={2.4}><Card variant="outlined"><CardContent><Typography variant="overline">Top forfet</Typography><Typography variant="body1" sx={{ fontWeight: 700 }}>{legacyTopBundle?.bundle_name || '-'}</Typography><Typography color="text.secondary">{legacyTopBundle ? formatMoney(legacyTopBundle.revenue) : '-'}</Typography></CardContent></Card></Grid>
              </Grid>
            </CardContent>
          </Card>

          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 1 }}>Top pracownicy</Typography>
                  {renderGenericTable(legacyTopWorkersRows)}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 1 }}>Top uslugi</Typography>
                  {renderGenericTable(legacyTopServices)}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 1 }}>Top forfety</Typography>
                  {renderGenericTable(legacyTopBundles)}
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Mix platnosci (legacy)</Typography>
              <Box sx={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={legacyPaymentMix}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="payment" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="value" name="Przychod" fill="#3a6ea5" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mb: 2 }} spacing={1}>
                <FormControl size="small" sx={{ minWidth: 260 }}>
                  <InputLabel>Raport</InputLabel>
                  <Select label="Raport" value={selectedReport} onChange={(e) => setSelectedReport(e.target.value as ReportKey)}>
                    <MenuItem value="forfaits_analysis">Forfety - analiza</MenuItem>
                    <MenuItem value="forfaits_list">Forfety - lista</MenuItem>
                    <MenuItem value="services_worker">Uslugi wg pracownika</MenuItem>
                    <MenuItem value="services_lines">Wykonane uslugi (linie fiszek)</MenuItem>
                    <MenuItem value="services_aggregate">Uslugi - agregat</MenuItem>
                    <MenuItem value="daily_ed1">Dzienny</MenuItem>
                    <MenuItem value="monthly_ed1">Miesieczny</MenuItem>
                    <MenuItem value="cashflow">Cashflow</MenuItem>
                    <MenuItem value="stat7">Stat7</MenuItem>
                  </Select>
                </FormControl>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
                  {(selectedReport === 'services_worker' || selectedReport === 'services_lines' || selectedReport === 'services_aggregate') && (
                    <>
                      <FormControl size="small" sx={{ minWidth: 210 }}>
                        <InputLabel>Filtr pracownik</InputLabel>
                        <Select
                          label="Filtr pracownik"
                          value={legacyWorkerFilter}
                          onChange={(e) => setLegacyWorkerFilter(String(e.target.value))}
                        >
                          <MenuItem value="">Wszyscy</MenuItem>
                          {workerFilterOptions.map((row) => (
                            <MenuItem key={row} value={row}>{row}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <FormControl size="small" sx={{ minWidth: 240 }} disabled={selectedReport === 'services_aggregate'}>
                        <InputLabel>Filtr usługa</InputLabel>
                        <Select
                          label="Filtr usługa"
                          value={legacyServiceFilter}
                          onChange={(e) => setLegacyServiceFilter(String(e.target.value))}
                        >
                          <MenuItem value="">Wszystkie</MenuItem>
                          {serviceFilterOptions.map((row) => (
                            <MenuItem key={row} value={row}>{row}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <FormControl size="small" sx={{ minWidth: 220 }}>
                        <InputLabel>Kody 200-299</InputLabel>
                        <Select
                          label="Kody 200-299"
                          value={legacySalesFilter}
                          onChange={(e) => setLegacySalesFilter(e.target.value as 'all' | 'exclude_sales' | 'only_sales')}
                        >
                          <MenuItem value="all">Wszystkie</MenuItem>
                          <MenuItem value="exclude_sales">Bez sprzedaży (200-299)</MenuItem>
                          <MenuItem value="only_sales">Tylko sprzedaż (200-299)</MenuItem>
                        </Select>
                      </FormControl>
                    </>
                  )}
                  {selectedReport === 'forfaits_analysis' && (
                    <>
                      <TextField
                        size="small"
                        label="Filtr kod/nazwa"
                        value={legacyForfaitSearch}
                        onChange={(e) => setLegacyForfaitSearch(e.target.value)}
                      />
                      <FormControl size="small" sx={{ minWidth: 170 }}>
                        <InputLabel>Sortuj po</InputLabel>
                        <Select
                          label="Sortuj po"
                          value={legacyForfaitSortBy}
                          onChange={(e) => setLegacyForfaitSortBy(e.target.value as LegacyForfaitSortBy)}
                        >
                          <MenuItem value="revenue">Suma</MenuItem>
                          <MenuItem value="count">Ilość</MenuItem>
                          <MenuItem value="code">Kod</MenuItem>
                          <MenuItem value="name">Nazwa</MenuItem>
                        </Select>
                      </FormControl>
                      <FormControl size="small" sx={{ minWidth: 140 }}>
                        <InputLabel>Kierunek</InputLabel>
                        <Select
                          label="Kierunek"
                          value={legacyForfaitSortDir}
                          onChange={(e) => setLegacyForfaitSortDir(e.target.value as 'asc' | 'desc')}
                        >
                          <MenuItem value="asc">Rosnąco</MenuItem>
                          <MenuItem value="desc">Malejąco</MenuItem>
                        </Select>
                      </FormControl>
                    </>
                  )}
                  {selectedReport === 'services_worker' && (
                    <>
                      <FormControl size="small" sx={{ minWidth: 180 }}>
                        <InputLabel>Sortuj po</InputLabel>
                        <Select
                          label="Sortuj po"
                          value={legacyWorkerSortBy}
                          onChange={(e) => setLegacyWorkerSortBy(e.target.value as LegacyWorkerSortBy)}
                        >
                          <MenuItem value="worker">Pracownik</MenuItem>
                          <MenuItem value="code">Kod usługi</MenuItem>
                          <MenuItem value="service">Usługa</MenuItem>
                        </Select>
                      </FormControl>
                      <FormControl size="small" sx={{ minWidth: 140 }}>
                        <InputLabel>Kierunek</InputLabel>
                        <Select
                          label="Kierunek"
                          value={legacyWorkerSortDir}
                          onChange={(e) => setLegacyWorkerSortDir(e.target.value as LegacyWorkerSortDir)}
                        >
                          <MenuItem value="asc">Rosnąco</MenuItem>
                          <MenuItem value="desc">Malejąco</MenuItem>
                        </Select>
                      </FormControl>
                    </>
                  )}
                  {selectedReport === 'services_aggregate' && (
                    <>
                      <TextField
                        size="small"
                        label="Filtr kod/nazwa"
                        value={legacyAggSearch}
                        onChange={(e) => setLegacyAggSearch(e.target.value)}
                      />
                      <FormControl size="small" sx={{ minWidth: 170 }}>
                        <InputLabel>Sortuj po</InputLabel>
                        <Select
                          label="Sortuj po"
                          value={legacyAggSortBy}
                          onChange={(e) => setLegacyAggSortBy(e.target.value as LegacyAggregateSortBy)}
                        >
                          <MenuItem value="revenue">Suma</MenuItem>
                          <MenuItem value="qty">Ilość</MenuItem>
                          <MenuItem value="code">Kod</MenuItem>
                          <MenuItem value="name">Nazwa</MenuItem>
                        </Select>
                      </FormControl>
                      <FormControl size="small" sx={{ minWidth: 140 }}>
                        <InputLabel>Kierunek</InputLabel>
                        <Select
                          label="Kierunek"
                          value={legacyAggSortDir}
                          onChange={(e) => setLegacyAggSortDir(e.target.value as 'asc' | 'desc')}
                        >
                          <MenuItem value="asc">Rosnąco</MenuItem>
                          <MenuItem value="desc">Malejąco</MenuItem>
                        </Select>
                      </FormControl>
                    </>
                  )}
                  {selectedReport === 'services_lines' && (
                    <>
                      <TextField
                        size="small"
                        label="Filtr numer fiszki"
                        value={legacyTicketFilter}
                        onChange={(e) => setLegacyTicketFilter(e.target.value)}
                      />
                      <FormControl size="small" sx={{ minWidth: 180 }}>
                        <InputLabel>Sortuj po</InputLabel>
                        <Select
                          label="Sortuj po"
                          value={legacyLineSortBy}
                          onChange={(e) => setLegacyLineSortBy(e.target.value as 'date' | 'worker' | 'service' | 'ticket')}
                        >
                          <MenuItem value="date">Data/linia</MenuItem>
                          <MenuItem value="ticket">Fiszka</MenuItem>
                          <MenuItem value="worker">Pracownik</MenuItem>
                          <MenuItem value="service">Usługa</MenuItem>
                        </Select>
                      </FormControl>
                      <FormControl size="small" sx={{ minWidth: 140 }}>
                        <InputLabel>Kierunek</InputLabel>
                        <Select
                          label="Kierunek"
                          value={legacyLineSortDir}
                          onChange={(e) => setLegacyLineSortDir(e.target.value as 'asc' | 'desc')}
                        >
                          <MenuItem value="asc">Rosnąco</MenuItem>
                          <MenuItem value="desc">Malejąco</MenuItem>
                        </Select>
                      </FormControl>
                    </>
                  )}
                  <Button variant="outlined" onClick={rebuildLegacyFiche} disabled={legacyImportBusy}>
                    {legacyImportBusy ? 'Importowanie fiszek...' : 'Import fiszek'}
                  </Button>
                  <Button startIcon={<Download />} onClick={() => downloadCsv(`legacy-${selectedReport}.csv`, renderLegacyReport())}>Eksport CSV</Button>
                </Stack>
              </Stack>
              {renderGenericTable(renderLegacyReport())}
              {selectedReport === 'services_worker' && (
                <Stack
                  direction={{ xs: 'column', md: 'row' }}
                  spacing={2}
                  justifyContent="flex-end"
                  sx={{ mt: 1.5 }}
                >
                  <Typography variant="body2" color="text.secondary">Pozycje: {servicesWorkerSummary.rowsCount}</Typography>
                  <Typography variant="body2" color="text.secondary">Ilość łącznie: {servicesWorkerSummary.qtyTotal}</Typography>
                  <Typography variant="body1" sx={{ fontWeight: 700 }}>Suma: {formatMoney(servicesWorkerSummary.amountTotal)}</Typography>
                </Stack>
              )}
            </CardContent>
          </Card>
        </Stack>
      )}

      {mainTab === 'materials' && (
        <Card>
          <CardContent>
            <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mb: 2 }} spacing={1}>
              <FormControl size="small" sx={{ minWidth: 240 }}>
                <InputLabel>Grupowanie</InputLabel>
                <Select label="Grupowanie" value={materialMode} onChange={(e) => setMaterialMode(e.target.value as MaterialMode)}>
                  <MenuItem value="by-staff">by-staff</MenuItem>
                  <MenuItem value="by-service">by-service</MenuItem>
                  <MenuItem value="deviations">deviations</MenuItem>
                </Select>
              </FormControl>
              <Button startIcon={<Download />} onClick={() => downloadCsv(`materials-${materialMode}.csv`, materialRows)}>Eksport CSV</Button>
            </Stack>
            {renderGenericTable(materialRows)}
          </CardContent>
        </Card>
      )}

      {mainTab === 'sales' && (
        <Stack spacing={2}>
          <Grid container spacing={2}>
            {salesBySalon.map((row) => (
              <Grid item xs={12} md={4} key={row.salon_id}>
                <Card>
                  <CardContent>
                    <Typography variant="overline">{row.salon_name || `Salon ${row.salon_id}`}</Typography>
                    <Typography variant="h5">{row.total_gross.toFixed(2)} PLN</Typography>
                    <Typography color="text.secondary">Transakcje: {row.transactions_count}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
            {!salesBySalon.length && (
              <Grid item xs={12}><Alert severity="info">Brak danych sprzedazowych dla wybranego zakresu.</Alert></Grid>
            )}
          </Grid>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Sprzedaz detaliczna wg salonu</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>Laczna sprzedaz: {salesTotal.toFixed(2)} PLN</Typography>
              <Box sx={{ width: '100%', height: 320 }}>
                <ResponsiveContainer>
                  <BarChart data={salesBySalon}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="salon_name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="total_gross" name="Total gross" fill="#3a6ea5" radius={[6, 6, 0, 0]} />
                    <Bar dataKey="transactions_count" name="Transactions" fill="#57a773" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
              <Stack direction="row" justifyContent="flex-end" sx={{ mt: 2 }}>
                <Button startIcon={<Download />} onClick={() => downloadCsv('sales-by-salon.csv', salesBySalon.map((row) => ({ Salon: row.salon_name || row.salon_id, Transactions: row.transactions_count, Linie: row.lines_count, TotalGross: row.total_gross.toFixed(2) })))}>Eksport CSV</Button>
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      )}

      {mainTab === 'payments' && (
        <Stack spacing={2}>
          {promotionError && <Alert severity="error">{promotionError}</Alert>}
          {promotionInfo && <Alert severity="success">{promotionInfo}</Alert>}
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="overline">Laczne rozliczenia</Typography>
                  <Typography variant="h5">{paymentsTotal.toFixed(2)} PLN</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="overline">Platnosci</Typography>
                  <Typography variant="h5">{paymentsReport.reduce((sum, row) => sum + row.payments_count, 0)}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="overline">Transakcje z karta stalego</Typography>
                  <Typography variant="h5">{paymentsReport.reduce((sum, row) => sum + row.card_payments_count, 0)}</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Przychody wg metody i klienta</Typography>
              <Box sx={{ width: '100%', height: 320 }}>
                <ResponsiveContainer>
                  <BarChart data={paymentsReport}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="method" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="total_amount" name="Total amount" fill="#cc7a00" radius={[6, 6, 0, 0]} />
                    <Bar dataKey="payments_count" name="Payments" fill="#3a6ea5" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
              <Stack direction="row" justifyContent="flex-end" sx={{ mt: 2 }}>
                <Button
                  startIcon={<Download />}
                  onClick={() => downloadCsv('payments-report.csv', paymentsReport.map((row) => ({
                    Method: row.method,
                    Client: row.client_name || row.client_id || '-',
                    Payments: row.payments_count,
                    TotalAmount: row.total_amount.toFixed(2),
                    CardPayments: row.card_payments_count,
                  })))}
                >
                  Eksport CSV
                </Button>
              </Stack>
              <Box sx={{ mt: 2 }}>
                {renderGenericTable(
                  paymentsReport.map((row) => ({
                    Metoda: row.method,
                    Klient: row.client_name || row.client_id || '-',
                    Platnosci: row.payments_count,
                    Suma: row.total_amount.toFixed(2),
                    KartaStalego: row.card_payments_count,
                  })),
                )}
              </Box>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Stack spacing={2}>
                <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1}>
                  <Typography variant="h6">Promocje</Typography>
                  <Stack direction="row" spacing={1}>
                    <Button startIcon={<Refresh />} onClick={() => fetchPromotions()}>Odswiez promocje</Button>
                    <Button variant="outlined" onClick={resetPromotionForm}>Nowa promocja</Button>
                  </Stack>
                </Stack>
                <Grid container spacing={1.5}>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Nazwa promocji"
                      fullWidth
                      value={promotionForm.name}
                      onChange={(e) => setPromotionForm((prev) => ({ ...prev, name: e.target.value }))}
                    />
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      select
                      label="Typ"
                      fullWidth
                      value={promotionForm.promotion_type}
                      onChange={(e) => setPromotionForm((prev) => ({ ...prev, promotion_type: e.target.value }))}
                    >
                      <MenuItem value="fixed_discount">Kwota rabatu</MenuItem>
                      <MenuItem value="percent_discount">Rabat %</MenuItem>
                      <MenuItem value="fixed_price">Stala cena</MenuItem>
                      <MenuItem value="bundle_bonus">Bonus pakietu</MenuItem>
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      type="number"
                      label="Wartosc"
                      fullWidth
                      value={promotionForm.value}
                      onChange={(e) => setPromotionForm((prev) => ({ ...prev, value: e.target.value }))}
                    />
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      select
                      label="Salon"
                      fullWidth
                      value={promotionForm.salon_id}
                      onChange={(e) => setPromotionForm((prev) => ({ ...prev, salon_id: e.target.value === '' ? '' : Number(e.target.value) }))}
                    >
                      <MenuItem value="">Wszystkie</MenuItem>
                      {salons.map((salon) => <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>)}
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      select
                      label="Aktywna"
                      fullWidth
                      value={promotionForm.is_active ? 'yes' : 'no'}
                      onChange={(e) => setPromotionForm((prev) => ({ ...prev, is_active: e.target.value === 'yes' }))}
                    >
                      <MenuItem value="yes">Tak</MenuItem>
                      <MenuItem value="no">Nie</MenuItem>
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      select
                      label="Usluga (opcjonalnie)"
                      fullWidth
                      value={promotionForm.service_id}
                      onChange={(e) => setPromotionForm((prev) => ({ ...prev, service_id: e.target.value === '' ? '' : Number(e.target.value) }))}
                    >
                      <MenuItem value="">Brak</MenuItem>
                      {services.map((service) => <MenuItem key={service.id} value={service.id}>{service.code} - {service.name}</MenuItem>)}
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      select
                      label="Forfet (opcjonalnie)"
                      fullWidth
                      value={promotionForm.bundle_id}
                      onChange={(e) => setPromotionForm((prev) => ({ ...prev, bundle_id: e.target.value === '' ? '' : Number(e.target.value) }))}
                    >
                      <MenuItem value="">Brak</MenuItem>
                      {bundles.map((bundle) => <MenuItem key={bundle.id} value={bundle.id}>{bundle.code} - {bundle.name}</MenuItem>)}
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Segment klienta"
                      fullWidth
                      value={promotionForm.customer_tier}
                      onChange={(e) => setPromotionForm((prev) => ({ ...prev, customer_tier: e.target.value.toUpperCase() }))}
                      helperText="Np. VIP, LOYAL"
                    />
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <TextField
                      type="date"
                      label="Od"
                      fullWidth
                      InputLabelProps={{ shrink: true }}
                      value={promotionForm.valid_from}
                      onChange={(e) => setPromotionForm((prev) => ({ ...prev, valid_from: e.target.value }))}
                    />
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <TextField
                      type="date"
                      label="Do"
                      fullWidth
                      InputLabelProps={{ shrink: true }}
                      value={promotionForm.valid_to}
                      onChange={(e) => setPromotionForm((prev) => ({ ...prev, valid_to: e.target.value }))}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Stack direction="row" spacing={1} justifyContent="flex-end" sx={{ height: '100%', alignItems: 'center' }}>
                      {promotionEditingId && <Button onClick={resetPromotionForm}>Anuluj edycje</Button>}
                      <Button
                        variant="contained"
                        onClick={savePromotion}
                        disabled={promotionForm.name.trim().length === 0 || Number(promotionForm.value) < 0}
                      >
                        {promotionEditingId ? 'Zapisz promocje' : 'Dodaj promocje'}
                      </Button>
                    </Stack>
                  </Grid>
                </Grid>
                {promotionLoading ? (
                  <Typography color="text.secondary">Ladowanie promocji...</Typography>
                ) : (
                  renderGenericTable(
                    promotions.map((row) => ({
                      ID: row.id,
                      Nazwa: row.name,
                      Typ: row.promotion_type,
                      Wartosc: row.value.toFixed(2),
                      Salon: salons.find((salon) => salon.id === row.salon_id)?.name || 'Wszystkie',
                      Usluga: services.find((service) => service.id === row.service_id)?.name || '-',
                      Forfet: bundles.find((bundle) => bundle.id === row.bundle_id)?.name || '-',
                      Segment: row.customer_tier || '-',
                      Od: row.valid_from || '-',
                      Do: row.valid_to || '-',
                      Aktywna: row.is_active ? 'Tak' : 'Nie',
                    })),
                  )
                )}
                {!!promotions.length && (
                  <TableContainer>
                    <Table size="small" sx={TABLE_SX}>
                      <TableHead>
                        <TableRow>
                          <TableCell>ID</TableCell>
                          <TableCell>Nazwa</TableCell>
                          <TableCell>Typ</TableCell>
                          <TableCell align="right">Akcje</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {promotions.map((row) => (
                          <TableRow key={row.id}>
                            <TableCell>{row.id}</TableCell>
                            <TableCell>{row.name}</TableCell>
                            <TableCell>{row.promotion_type}</TableCell>
                            <TableCell align="right">
                              <Button size="small" onClick={() => startEditPromotion(row)}>Edytuj</Button>
                              <Button size="small" color="error" onClick={() => deletePromotion(row.id)}>Usun</Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      )}

      {mainTab === 'analytics' && (
        <Stack spacing={2}>
          <Card>
            <CardContent>
              <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mb: 2 }} spacing={1}>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
                  <FormControl size="small" sx={{ minWidth: 260 }}>
                    <InputLabel>Raport analityczny</InputLabel>
                    <Select label="Raport analityczny" value={analyticsMode} onChange={(e) => setAnalyticsMode(e.target.value as AnalyticsMode)}>
                      <MenuItem value="demand">Popyt i ceny</MenuItem>
                      <MenuItem value="margin">Marza uslug</MenuItem>
                      <MenuItem value="bundle">Marza forfetow</MenuItem>
                      <MenuItem value="staff">Wynik pracownikow</MenuItem>
                      <MenuItem value="deviation_staff">Odchylenia pracownikow</MenuItem>
                      <MenuItem value="deviation_service">Odchylenia uslug</MenuItem>
                      <MenuItem value="family">Zuzycie wg rodzin</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl size="small" sx={{ minWidth: 140 }}>
                    <InputLabel>Sortowanie</InputLabel>
                    <Select label="Sortowanie" value={analyticsSort} onChange={(e) => setAnalyticsSort(e.target.value as AnalyticsSort)}>
                      <MenuItem value="value_desc">Wartosc malejaco</MenuItem>
                      <MenuItem value="value_asc">Wartosc rosnaco</MenuItem>
                      <MenuItem value="name_asc">Nazwa A-Z</MenuItem>
                    </Select>
                  </FormControl>
                  <TextField
                    size="small"
                    type="number"
                    label="Top N"
                    InputLabelProps={{ shrink: true }}
                    value={analyticsTopN}
                    onChange={(e) => setAnalyticsTopN(Math.max(1, Number(e.target.value) || 10))}
                    sx={{ width: 120 }}
                  />
                </Stack>
                <Button startIcon={<Download />} onClick={() => downloadCsv(`analytics-${analyticsMode}.csv`, analyticsRows)}>Eksport CSV</Button>
              </Stack>
              <Box sx={{ width: '100%', height: 320, mb: 2 }}>
                <ResponsiveContainer>
                  <BarChart data={analyticsChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" hide />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    {analyticsMode === 'demand' && (
                      <>
                        <Bar dataKey="revenue" name="Przychod" fill="#3a6ea5" radius={[6, 6, 0, 0]} />
                        <Bar dataKey="sold" name="Srednia sprzedaz" fill="#57a773" radius={[6, 6, 0, 0]} />
                        <Bar dataKey="list" name="Sredni cennik" fill="#cc7a00" radius={[6, 6, 0, 0]} />
                      </>
                    )}
                    {analyticsMode === 'margin' && (
                      <>
                        <Bar dataKey="margin" name="Marza" fill="#57a773" radius={[6, 6, 0, 0]} />
                        <Bar dataKey="cost" name="Koszt materialow" fill="#cc7a00" radius={[6, 6, 0, 0]} />
                      </>
                    )}
                    {analyticsMode === 'bundle' && (
                      <>
                        <Bar dataKey="margin" name="Marza" fill="#57a773" radius={[6, 6, 0, 0]} />
                        <Bar dataKey="revenue" name="Przychod" fill="#3a6ea5" radius={[6, 6, 0, 0]} />
                      </>
                    )}
                    {analyticsMode === 'staff' && (
                      <>
                        <Bar dataKey="revenue" name="Przychod" fill="#3a6ea5" radius={[6, 6, 0, 0]} />
                        <Bar dataKey="margin" name="Marza" fill="#57a773" radius={[6, 6, 0, 0]} />
                      </>
                    )}
                    {analyticsMode === 'deviation_staff' && (
                      <>
                        <Bar dataKey="planned" name="Plan" fill="#3a6ea5" radius={[6, 6, 0, 0]} />
                        <Bar dataKey="actual" name="Faktycznie" fill="#57a773" radius={[6, 6, 0, 0]} />
                        <Bar dataKey="deviation" name="Odchylenie" fill="#cc7a00" radius={[6, 6, 0, 0]} />
                      </>
                    )}
                    {analyticsMode === 'deviation_service' && (
                      <>
                        <Bar dataKey="planned" name="Plan" fill="#3a6ea5" radius={[6, 6, 0, 0]} />
                        <Bar dataKey="actual" name="Faktycznie" fill="#57a773" radius={[6, 6, 0, 0]} />
                        <Bar dataKey="deviation" name="Odchylenie" fill="#cc7a00" radius={[6, 6, 0, 0]} />
                      </>
                    )}
                    {analyticsMode === 'family' && (
                      <>
                        <Bar dataKey="cost" name="Koszt" fill="#cc7a00" radius={[6, 6, 0, 0]} />
                        <Bar dataKey="qty" name="Ilosc" fill="#3a6ea5" radius={[6, 6, 0, 0]} />
                      </>
                    )}
                  </BarChart>
                </ResponsiveContainer>
              </Box>
              {renderGenericTable(analyticsRows)}
            </CardContent>
          </Card>
        </Stack>
      )}
    </Stack>
  )
}

export default ReportsPage
