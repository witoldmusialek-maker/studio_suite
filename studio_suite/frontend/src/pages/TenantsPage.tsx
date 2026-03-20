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
}

type License = {
  id?: number
  tenant_id?: number
  module_code: string
  is_enabled: boolean
  monthly_price: number
  notes?: string | null
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
  const [tenantActive, setTenantActive] = useState(true)
  const [adminUsername, setAdminUsername] = useState('')
  const [adminPassword, setAdminPassword] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
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

  useEffect(() => {
    loadTenants()
  }, [])

  useEffect(() => {
    if (selectedTenantId) loadLicenses(selectedTenantId)
  }, [selectedTenantId])

  const resetForm = () => {
    setEditingId(null)
    setTenantCode('')
    setTenantName('')
    setTenantPlan('BASIC')
    setTenantCycle('monthly')
    setTenantPrice('0')
    setTenantEmail('')
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
            <FormControlLabel
              control={<Checkbox checked={tenantActive} onChange={(e) => setTenantActive(e.target.checked)} />}
              label="Aktywny"
            />
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
    </Stack>
  )
}

export default TenantsPage
