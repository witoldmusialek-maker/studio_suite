import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  CardContent,
  Checkbox,
  FormControlLabel,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { api } from '../services/api'

type Tenant = {
  id: number
  code: string
  name: string
  is_active: boolean
  billing_plan: string
  billing_cycle: string
  monthly_base_price: number
  billing_email?: string | null
  description?: string | null
  legal_name?: string | null
  tax_id?: string | null
  billing_address_line1?: string | null
  billing_address_line2?: string | null
  billing_postal_code?: string | null
  billing_city?: string | null
  billing_country?: string | null
  billing_contact_name?: string | null
  billing_contact_phone?: string | null
  billing_due_days?: number
}

type License = {
  id?: number
  tenant_id?: number
  module_code: string
  is_enabled: boolean
  monthly_price: number
  notes?: string | null
}

type BillingInvoiceLine = {
  code: string
  label: string
  amount: number
}

type BillingInvoice = {
  id: number
  tenant_id: number
  period_year: number
  period_month: number
  issue_date: string
  due_date: string
  currency: string
  base_amount: number
  modules_amount: number
  total_amount: number
  status: string
  notes?: string | null
  sent_at?: string | null
  paid_at?: string | null
  line_items?: BillingInvoiceLine[]
}

const DEFAULT_MODULES = ['REPORTS', 'INVENTORY', 'BOOKING', 'PAYMENTS', 'PUBLIC_BOOKING'] as const

const TenantsPage = () => {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [selectedTenantId, setSelectedTenantId] = useState<number | null>(null)
  const [licenses, setLicenses] = useState<License[]>([])
  const [tenantCode, setTenantCode] = useState('')
  const [tenantName, setTenantName] = useState('')
  const [tenantPlan, setTenantPlan] = useState('BASIC')
  const [tenantCycle, setTenantCycle] = useState('monthly')
  const [tenantPrice, setTenantPrice] = useState('0')
  const [tenantEmail, setTenantEmail] = useState('')
  const [tenantDescription, setTenantDescription] = useState('')
  const [tenantLegalName, setTenantLegalName] = useState('')
  const [tenantTaxId, setTenantTaxId] = useState('')
  const [tenantAddressLine1, setTenantAddressLine1] = useState('')
  const [tenantAddressLine2, setTenantAddressLine2] = useState('')
  const [tenantPostalCode, setTenantPostalCode] = useState('')
  const [tenantCity, setTenantCity] = useState('')
  const [tenantCountry, setTenantCountry] = useState('PL')
  const [tenantContactName, setTenantContactName] = useState('')
  const [tenantContactPhone, setTenantContactPhone] = useState('')
  const [tenantDueDays, setTenantDueDays] = useState('14')
  const [tenantActive, setTenantActive] = useState(true)
  const [adminUsername, setAdminUsername] = useState('')
  const [adminPassword, setAdminPassword] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [invoices, setInvoices] = useState<BillingInvoice[]>([])
  const [invoiceYear, setInvoiceYear] = useState(String(new Date().getFullYear()))
  const [invoiceMonth, setInvoiceMonth] = useState(String(new Date().getMonth() + 1))
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const effectiveLicenses = useMemo(() => {
    const map = new Map<string, License>()
    for (const row of licenses) map.set(row.module_code, row)
    for (const code of DEFAULT_MODULES) {
      if (!map.has(code)) {
        map.set(code, { module_code: code, is_enabled: false, monthly_price: 0, notes: '' })
      }
    }
    return Array.from(map.values()).sort((a, b) => a.module_code.localeCompare(b.module_code))
  }, [licenses])

  const loadTenants = async () => {
    try {
      const res = await api.get<Tenant[]>('/tenants')
      setTenants(res.data || [])
      if (!selectedTenantId && res.data?.length) setSelectedTenantId(res.data[0].id)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac tenantow')
    }
  }

  const loadLicenses = async (tenantId: number) => {
    try {
      const res = await api.get<License[]>(`/tenants/${tenantId}/licenses`)
      setLicenses(res.data || [])
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac licencji')
    }
  }

  const loadInvoices = async (tenantId: number) => {
    try {
      const res = await api.get<BillingInvoice[]>(`/tenants/${tenantId}/billing/invoices`)
      setInvoices(res.data || [])
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac rozliczen')
    }
  }

  useEffect(() => {
    loadTenants()
  }, [])

  useEffect(() => {
    if (selectedTenantId) {
      loadLicenses(selectedTenantId)
      loadInvoices(selectedTenantId)
    }
  }, [selectedTenantId])

  const resetForm = () => {
    setEditingId(null)
    setTenantCode('')
    setTenantName('')
    setTenantPlan('BASIC')
    setTenantCycle('monthly')
    setTenantPrice('0')
    setTenantEmail('')
    setTenantDescription('')
    setTenantLegalName('')
    setTenantTaxId('')
    setTenantAddressLine1('')
    setTenantAddressLine2('')
    setTenantPostalCode('')
    setTenantCity('')
    setTenantCountry('PL')
    setTenantContactName('')
    setTenantContactPhone('')
    setTenantDueDays('14')
    setTenantActive(true)
    setAdminUsername('')
    setAdminPassword('')
  }

  const editTenant = (row: Tenant) => {
    setEditingId(row.id)
    setTenantCode(row.code)
    setTenantName(row.name)
    setTenantPlan(row.billing_plan || 'BASIC')
    setTenantCycle(row.billing_cycle || 'monthly')
    setTenantPrice(String(row.monthly_base_price ?? 0))
    setTenantEmail(row.billing_email || '')
    setTenantDescription(row.description || '')
    setTenantLegalName(row.legal_name || '')
    setTenantTaxId(row.tax_id || '')
    setTenantAddressLine1(row.billing_address_line1 || '')
    setTenantAddressLine2(row.billing_address_line2 || '')
    setTenantPostalCode(row.billing_postal_code || '')
    setTenantCity(row.billing_city || '')
    setTenantCountry((row.billing_country || 'PL').toUpperCase())
    setTenantContactName(row.billing_contact_name || '')
    setTenantContactPhone(row.billing_contact_phone || '')
    setTenantDueDays(String(row.billing_due_days ?? 14))
    setTenantActive(Boolean(row.is_active))
  }

  const saveTenant = async () => {
    setError(null)
    setMessage(null)
    try {
      const payload = {
        code: tenantCode.trim(),
        name: tenantName.trim(),
        is_active: tenantActive,
        billing_plan: tenantPlan.trim().toUpperCase(),
        billing_cycle: tenantCycle.trim().toLowerCase(),
        monthly_base_price: Number(tenantPrice || 0),
        billing_email: tenantEmail.trim() || null,
        description: tenantDescription.trim() || null,
        legal_name: tenantLegalName.trim() || null,
        tax_id: tenantTaxId.trim() || null,
        billing_address_line1: tenantAddressLine1.trim() || null,
        billing_address_line2: tenantAddressLine2.trim() || null,
        billing_postal_code: tenantPostalCode.trim() || null,
        billing_city: tenantCity.trim() || null,
        billing_country: tenantCountry.trim().toUpperCase() || 'PL',
        billing_contact_name: tenantContactName.trim() || null,
        billing_contact_phone: tenantContactPhone.trim() || null,
        billing_due_days: Math.max(1, Math.min(90, Number(tenantDueDays || 14))),
      }
      if (editingId) {
        await api.patch(`/tenants/${editingId}`, payload)
        setMessage('Tenant zaktualizowany')
      } else {
        await api.post('/tenants', {
          ...payload,
          admin_username: adminUsername.trim() || null,
          admin_password: adminPassword || null,
        })
        setMessage('Tenant utworzony')
      }
      await loadTenants()
      resetForm()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac tenanta')
    }
  }

  const saveLicenses = async () => {
    if (!selectedTenantId) return
    setError(null)
    setMessage(null)
    try {
      await api.put(`/tenants/${selectedTenantId}/licenses`, effectiveLicenses.map((row) => ({
        module_code: row.module_code,
        is_enabled: row.is_enabled,
        monthly_price: Number(row.monthly_price || 0),
        notes: row.notes || null,
      })))
      setMessage('Licencje zapisane')
      await loadLicenses(selectedTenantId)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac licencji')
    }
  }

  const generateInvoice = async () => {
    if (!selectedTenantId) return
    setError(null)
    setMessage(null)
    try {
      const year = Math.max(2020, Number(invoiceYear || new Date().getFullYear()))
      const month = Math.max(1, Math.min(12, Number(invoiceMonth || new Date().getMonth() + 1)))
      await api.post(`/tenants/${selectedTenantId}/billing/generate`, null, {
        params: { period_year: year, period_month: month, force_recalculate: true },
      })
      await loadInvoices(selectedTenantId)
      setMessage('Faktura rozliczeniowa wygenerowana')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie wygenerowac rozliczenia')
    }
  }

  const setInvoicePaid = async (invoiceId: number, paid: boolean) => {
    if (!selectedTenantId) return
    setError(null)
    setMessage(null)
    try {
      await api.post(`/tenants/${selectedTenantId}/billing/invoices/${invoiceId}/paid`, { paid })
      await loadInvoices(selectedTenantId)
      setMessage(paid ? 'Faktura oznaczona jako oplacona' : 'Faktura oznaczona jako nieoplacona')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zaktualizowac faktury')
    }
  }

  const runBillingReminders = async () => {
    setError(null)
    setMessage(null)
    try {
      const res = await api.post<{ sent: number; failed: number }>('/tenants/billing/reminders/run')
      const sent = Number(res.data?.sent || 0)
      const failed = Number(res.data?.failed || 0)
      setMessage(`Przypomnienia wyslane: ${sent}, bledy: ${failed}`)
      if (selectedTenantId) await loadInvoices(selectedTenantId)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie uruchomic przypomnien')
    }
  }

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Tenanty i licencje</Typography>
      {error ? <Alert severity="error">{error}</Alert> : null}
      {message ? <Alert severity="success">{message}</Alert> : null}

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Tenant</Typography>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
            <TextField label="Kod" value={tenantCode} onChange={(e) => setTenantCode(e.target.value)} fullWidth />
            <TextField label="Nazwa" value={tenantName} onChange={(e) => setTenantName(e.target.value)} fullWidth />
            <TextField label="Plan" value={tenantPlan} onChange={(e) => setTenantPlan(e.target.value)} />
            <TextField label="Cykl" value={tenantCycle} onChange={(e) => setTenantCycle(e.target.value)} />
            <TextField label="Abonament / mies." type="number" value={tenantPrice} onChange={(e) => setTenantPrice(e.target.value)} />
            <TextField label="Billing e-mail" value={tenantEmail} onChange={(e) => setTenantEmail(e.target.value)} />
            <TextField label="Termin platnosci (dni)" type="number" value={tenantDueDays} onChange={(e) => setTenantDueDays(e.target.value)} />
            <FormControlLabel
              control={<Checkbox checked={tenantActive} onChange={(e) => setTenantActive(e.target.checked)} />}
              label="Aktywny"
            />
          </Stack>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mt: 1.5 }}>
            <TextField label="Opis tenanta" value={tenantDescription} onChange={(e) => setTenantDescription(e.target.value)} fullWidth multiline minRows={2} />
          </Stack>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mt: 1.5 }}>
            <TextField label="Nazwa prawna" value={tenantLegalName} onChange={(e) => setTenantLegalName(e.target.value)} fullWidth />
            <TextField label="NIP / TAX ID" value={tenantTaxId} onChange={(e) => setTenantTaxId(e.target.value)} fullWidth />
            <TextField label="Osoba kontaktowa" value={tenantContactName} onChange={(e) => setTenantContactName(e.target.value)} fullWidth />
            <TextField label="Telefon kontaktowy" value={tenantContactPhone} onChange={(e) => setTenantContactPhone(e.target.value)} fullWidth />
          </Stack>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mt: 1.5 }}>
            <TextField label="Adres 1" value={tenantAddressLine1} onChange={(e) => setTenantAddressLine1(e.target.value)} fullWidth />
            <TextField label="Adres 2" value={tenantAddressLine2} onChange={(e) => setTenantAddressLine2(e.target.value)} fullWidth />
            <TextField label="Kod pocztowy" value={tenantPostalCode} onChange={(e) => setTenantPostalCode(e.target.value)} />
            <TextField label="Miasto" value={tenantCity} onChange={(e) => setTenantCity(e.target.value)} />
            <TextField label="Kraj" value={tenantCountry} onChange={(e) => setTenantCountry(e.target.value)} />
          </Stack>
          {!editingId ? (
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mt: 1.5 }}>
              <TextField label="Admin login tenanta" value={adminUsername} onChange={(e) => setAdminUsername(e.target.value)} fullWidth />
              <TextField label="Admin haslo tenanta" type="password" value={adminPassword} onChange={(e) => setAdminPassword(e.target.value)} fullWidth />
            </Stack>
          ) : null}
          <Stack direction="row" spacing={1} sx={{ mt: 1.5 }}>
            <Button
              variant="contained"
              onClick={saveTenant}
              disabled={tenantCode.trim().length < 2 || tenantName.trim().length < 2}
            >
              {editingId ? 'Zapisz tenant' : 'Dodaj tenant'}
            </Button>
            <Button variant="text" onClick={resetForm}>Wyczysc</Button>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Lista tenantow</Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Kod</TableCell>
                <TableCell>Nazwa</TableCell>
                <TableCell>Plan</TableCell>
                <TableCell>Abonament</TableCell>
                <TableCell>E-mail billing</TableCell>
                <TableCell>Aktywny</TableCell>
                <TableCell>Akcje</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tenants.map((row) => (
                <TableRow key={row.id} selected={row.id === selectedTenantId}>
                  <TableCell>{row.id}</TableCell>
                  <TableCell>{row.code}</TableCell>
                  <TableCell>{row.name}</TableCell>
                  <TableCell>{row.billing_plan}</TableCell>
                  <TableCell>{row.monthly_base_price}</TableCell>
                  <TableCell>{row.billing_email || '-'}</TableCell>
                  <TableCell>{row.is_active ? 'TAK' : 'NIE'}</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1}>
                      <Button size="small" variant="outlined" onClick={() => setSelectedTenantId(row.id)}>Licencje</Button>
                      <Button size="small" variant="outlined" onClick={() => editTenant(row)}>Edytuj</Button>
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {selectedTenantId ? (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>Licencje tenant #{selectedTenantId}</Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Modul</TableCell>
                  <TableCell>Wlaczony</TableCell>
                  <TableCell>Doplata / mies.</TableCell>
                  <TableCell>Notatka</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {effectiveLicenses.map((row) => (
                  <TableRow key={row.module_code}>
                    <TableCell>{row.module_code}</TableCell>
                    <TableCell>
                      <Checkbox
                        checked={row.is_enabled}
                        onChange={(e) =>
                          setLicenses((prev) => {
                            const next = [...prev]
                            const idx = next.findIndex((item) => item.module_code === row.module_code)
                            const updated = { ...row, is_enabled: e.target.checked }
                            if (idx >= 0) next[idx] = updated
                            else next.push(updated)
                            return next
                          })
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <TextField
                        size="small"
                        type="number"
                        value={row.monthly_price}
                        onChange={(e) =>
                          setLicenses((prev) => {
                            const next = [...prev]
                            const idx = next.findIndex((item) => item.module_code === row.module_code)
                            const updated = { ...row, monthly_price: Number(e.target.value || 0) }
                            if (idx >= 0) next[idx] = updated
                            else next.push(updated)
                            return next
                          })
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <TextField
                        size="small"
                        value={row.notes || ''}
                        onChange={(e) =>
                          setLicenses((prev) => {
                            const next = [...prev]
                            const idx = next.findIndex((item) => item.module_code === row.module_code)
                            const updated = { ...row, notes: e.target.value }
                            if (idx >= 0) next[idx] = updated
                            else next.push(updated)
                            return next
                          })
                        }
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Button variant="contained" sx={{ mt: 1.5 }} onClick={saveLicenses}>
              Zapisz licencje
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {selectedTenantId ? (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>Rozliczenia licencji tenant #{selectedTenantId}</Typography>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mb: 1.5 }}>
              <TextField label="Rok" type="number" value={invoiceYear} onChange={(e) => setInvoiceYear(e.target.value)} />
              <TextField label="Miesiac" type="number" value={invoiceMonth} onChange={(e) => setInvoiceMonth(e.target.value)} />
              <Button variant="contained" onClick={generateInvoice}>Generuj fakture</Button>
              <Button variant="outlined" onClick={runBillingReminders}>Uruchom przypomnienia</Button>
            </Stack>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Okres</TableCell>
                  <TableCell>Wystawiono</TableCell>
                  <TableCell>Termin</TableCell>
                  <TableCell>Kwota</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Pozycje</TableCell>
                  <TableCell>Akcje</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {invoices.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>{row.period_year}-{String(row.period_month).padStart(2, '0')}</TableCell>
                    <TableCell>{row.issue_date || '-'}</TableCell>
                    <TableCell>{row.due_date || '-'}</TableCell>
                    <TableCell>{Number(row.total_amount || 0).toFixed(2)} {row.currency || 'PLN'}</TableCell>
                    <TableCell>{row.status}</TableCell>
                    <TableCell>
                      {(row.line_items || []).map((line) => `${line.label}: ${Number(line.amount || 0).toFixed(2)}`).join(' | ') || '-'}
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1}>
                        <Button size="small" variant="outlined" onClick={() => setInvoicePaid(row.id, true)}>Oplacone</Button>
                        <Button size="small" variant="text" onClick={() => setInvoicePaid(row.id, false)}>Cofnij</Button>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
                {!invoices.length && (
                  <TableRow>
                    <TableCell colSpan={7}>Brak faktur rozliczeniowych.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}
    </Stack>
  )
}

export default TenantsPage
