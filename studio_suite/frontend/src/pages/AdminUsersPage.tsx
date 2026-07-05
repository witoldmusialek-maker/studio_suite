import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Snackbar,
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
import { Delete, LockReset, PersonAdd } from '@mui/icons-material'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { User } from '../types'

type TenantRow = {
  id: number
  code: string
  name: string
  is_active: boolean
  created_at: string
}

const AdminUsersPage = () => {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [createUsername, setCreateUsername] = useState('')
  const [createPassword, setCreatePassword] = useState('')
  const [createRole, setCreateRole] = useState<User['role']>('employee')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [totpEnabled, setTotpEnabled] = useState(false)
  const [totpSecret, setTotpSecret] = useState('')
  const [totpQrUrl, setTotpQrUrl] = useState('')
  const [totpSetupCode, setTotpSetupCode] = useState('')
  const [totpDisableCode, setTotpDisableCode] = useState('')
  const [smsTestPhone, setSmsTestPhone] = useState('')
  const [smsTestMessage, setSmsTestMessage] = useState('Test SMS Studio Suite')
  const [smsTestSending, setSmsTestSending] = useState(false)
  const [tenants, setTenants] = useState<TenantRow[]>([])
  const [tenantCode, setTenantCode] = useState('')
  const [tenantName, setTenantName] = useState('')
  const [tenantActive, setTenantActive] = useState(true)
  const [editingTenantId, setEditingTenantId] = useState<number | null>(null)
  const [snack, setSnack] = useState<{ message: string; severity: 'success' | 'error' } | null>(null)

  const roleOptions = useMemo(() => {
    if (currentUser?.role === 'admin') {
      return [
        { value: 'admin', label: 'Admin' },
        { value: 'manager_main', label: 'Manager główny' },
        { value: 'manager_salon', label: 'Manager salonu' },
        { value: 'manager', label: 'Manager (legacy)' },
        { value: 'employee', label: 'Employee' },
        { value: 'receptionist', label: 'Receptionist' },
      ] as const
    }
    if (currentUser?.role === 'manager_main' || currentUser?.role === 'manager') {
      return [
        { value: 'manager_salon', label: 'Manager salonu' },
        { value: 'employee', label: 'Employee' },
        { value: 'receptionist', label: 'Receptionist' },
      ] as const
    }
    return [
      { value: 'employee', label: 'Employee' },
      { value: 'receptionist', label: 'Receptionist' },
    ] as const
  }, [currentUser?.role])

  const fetchUsers = async () => {
    if (currentUser?.is_superadmin) {
      setUsers([])
      return
    }
    setLoading(true)
    try {
      const res = await api.get('/auth/users')
      setUsers(res.data)
    } catch {
      setSnack({ message: 'Nie udalo sie pobrac listy uzytkownikow', severity: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const tenantHasLegacyCaisse = useMemo(
    () => Boolean(currentUser?.licensed_modules?.some((code) => code.trim().toUpperCase() === 'LEGACY_CAISSE')),
    [currentUser?.licensed_modules],
  )

  useEffect(() => {
    fetchUsers()
  }, [currentUser?.is_superadmin])

  const fetchTenants = async () => {
    if (!currentUser?.is_superadmin) return
    try {
      const res = await api.get<TenantRow[]>('/tenants')
      setTenants(res.data || [])
    } catch {
      setSnack({ message: 'Nie udalo sie pobrac tenantow', severity: 'error' })
    }
  }

  useEffect(() => {
    fetchTenants()
  }, [currentUser?.is_superadmin])

  useEffect(() => {
    if (!(currentUser?.role === 'admin' || currentUser?.role === 'manager' || currentUser?.role === 'manager_main' || currentUser?.role === 'manager_salon')) return
    const loadTotpStatus = async () => {
      try {
        const res = await api.get<{ enabled: boolean }>('/auth/totp/status')
        setTotpEnabled(Boolean(res.data?.enabled))
      } catch {
        setTotpEnabled(false)
      }
    }
    loadTotpStatus().catch(() => undefined)
  }, [currentUser?.role])

  const handleCreate = async () => {
    try {
      await api.post('/auth/register', {
        username: createUsername.trim(),
        password: createPassword,
        role: createRole,
      })
      setSnack({ message: 'Uzytkownik utworzony', severity: 'success' })
      setCreateOpen(false)
      setCreateUsername('')
      setCreatePassword('')
      setCreateRole(currentUser?.role === 'admin' ? 'employee' : 'employee')
      await fetchUsers()
    } catch {
      setSnack({ message: 'Nie udalo sie utworzyc uzytkownika', severity: 'error' })
    }
  }

  const handleRoleChange = async (id: number, role: User['role']) => {
    try {
      await api.patch(`/auth/users/${id}`, { role })
      setSnack({ message: 'Rola zaktualizowana', severity: 'success' })
      await fetchUsers()
    } catch {
      setSnack({ message: 'Nie udalo sie zaktualizowac roli', severity: 'error' })
    }
  }

  const handleLegacyCaisseAccessChange = async (target: User, enabled: boolean) => {
    try {
      await api.patch(`/auth/users/${target.id}`, { legacy_caisse_enabled: enabled })
      setSnack({ message: enabled ? 'Dostep do Legacy CAISSE wlaczony' : 'Dostep do Legacy CAISSE wylaczony', severity: 'success' })
      await fetchUsers()
    } catch (err: any) {
      setSnack({ message: err?.response?.data?.detail || 'Nie udalo sie zmienic dostepu do Legacy CAISSE', severity: 'error' })
    }
  }

  const handleResetPassword = async (id: number) => {
    const newPassword = window.prompt('Nowe haslo (min 10, mala/duza/cyfra):')
    if (!newPassword) return
    try {
      await api.post(`/auth/users/${id}/reset-password`, { new_password: newPassword })
      setSnack({ message: 'Haslo zresetowane', severity: 'success' })
    } catch {
      setSnack({ message: 'Nie udalo sie zresetowac hasla', severity: 'error' })
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Na pewno usunac uzytkownika?')) return
    try {
      await api.delete(`/auth/users/${id}`)
      setSnack({ message: 'Uzytkownik usuniety', severity: 'success' })
      await fetchUsers()
    } catch {
      setSnack({ message: 'Nie udalo sie usunac uzytkownika', severity: 'error' })
    }
  }

  const canManageRole = (role: User['role']) => {
    if (currentUser?.role === 'admin') return true
    if (currentUser?.role === 'manager_main' || currentUser?.role === 'manager') {
      return role === 'manager_salon' || role === 'employee' || role === 'receptionist'
    }
    return currentUser?.role === 'manager_salon' && (role === 'employee' || role === 'receptionist')
  }

  const canEditUserRole = (target: User) => {
    if (!canManageRole(target.role)) return false
    if (currentUser?.role === 'admin' && target.id === currentUser.id) return false
    return true
  }

  const canDeleteUser = (target: User) => target.id !== currentUser?.id && canManageRole(target.role)

  const handleOwnPasswordChange = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      setSnack({ message: 'Uzupelnij wszystkie pola hasla', severity: 'error' })
      return
    }
    if (newPassword !== confirmPassword) {
      setSnack({ message: 'Nowe hasla nie sa takie same', severity: 'error' })
      return
    }
    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setSnack({ message: 'Haslo zostalo zmienione', severity: 'success' })
    } catch (err: any) {
      setSnack({ message: err?.response?.data?.detail || 'Nie udalo sie zmienic hasla', severity: 'error' })
    }
  }

  const handleTotpSetup = async () => {
    try {
      const res = await api.post<{ secret: string; otpauth_uri: string; qr_url: string }>('/auth/totp/setup')
      setTotpSecret(res.data.secret)
      setTotpQrUrl(res.data.qr_url)
      setTotpSetupCode('')
      setTotpEnabled(false)
      setSnack({ message: 'Zeskanuj kod QR i potwierdz kodem TOTP.', severity: 'success' })
    } catch (err: any) {
      setSnack({ message: err?.response?.data?.detail || 'Nie udalo sie przygotowac TOTP', severity: 'error' })
    }
  }

  const handleTotpEnable = async () => {
    try {
      await api.post('/auth/totp/enable', { code: totpSetupCode })
      setTotpEnabled(true)
      setTotpSecret('')
      setTotpQrUrl('')
      setTotpSetupCode('')
      setSnack({ message: 'TOTP wlaczone.', severity: 'success' })
    } catch (err: any) {
      setSnack({ message: err?.response?.data?.detail || 'Nie udalo sie wlaczyc TOTP', severity: 'error' })
    }
  }

  const handleTotpDisable = async () => {
    try {
      await api.post('/auth/totp/disable', { code: totpDisableCode })
      setTotpEnabled(false)
      setTotpDisableCode('')
      setSnack({ message: 'TOTP wylaczone.', severity: 'success' })
    } catch (err: any) {
      setSnack({ message: err?.response?.data?.detail || 'Nie udalo sie wylaczyc TOTP', severity: 'error' })
    }
  }

  const handleSmsTest = async () => {
    if (!smsTestPhone.trim() || !smsTestMessage.trim()) {
      setSnack({ message: 'Uzupelnij numer i tresc SMS', severity: 'error' })
      return
    }
    setSmsTestSending(true)
    try {
      await api.post('/auth/sms-test', {
        phone: smsTestPhone.trim(),
        message: smsTestMessage.trim(),
      })
      setSnack({ message: 'SMS testowy wyslany', severity: 'success' })
    } catch (err: any) {
      setSnack({ message: err?.response?.data?.detail || 'Nie udalo sie wyslac SMS testowego', severity: 'error' })
    } finally {
      setSmsTestSending(false)
    }
  }

  const resetTenantForm = () => {
    setTenantCode('')
    setTenantName('')
    setTenantActive(true)
    setEditingTenantId(null)
  }

  const handleTenantSave = async () => {
    try {
      if (editingTenantId) {
        await api.patch(`/tenants/${editingTenantId}`, {
          code: tenantCode.trim(),
          name: tenantName.trim(),
          is_active: tenantActive,
        })
        setSnack({ message: 'Tenant zaktualizowany', severity: 'success' })
      } else {
        await api.post('/tenants', {
          code: tenantCode.trim(),
          name: tenantName.trim(),
          is_active: tenantActive,
        })
        setSnack({ message: 'Tenant utworzony', severity: 'success' })
      }
      resetTenantForm()
      await fetchTenants()
    } catch (err: any) {
      setSnack({ message: err?.response?.data?.detail || 'Nie udalo sie zapisac tenanta', severity: 'error' })
    }
  }

  const handleTenantEdit = (tenant: TenantRow) => {
    setEditingTenantId(tenant.id)
    setTenantCode(tenant.code)
    setTenantName(tenant.name)
    setTenantActive(Boolean(tenant.is_active))
  }

  const handleTenantDelete = async (tenantId: number) => {
    if (!window.confirm('Usunac tenant?')) return
    try {
      await api.delete(`/tenants/${tenantId}`)
      setSnack({ message: 'Tenant usuniety', severity: 'success' })
      await fetchTenants()
    } catch (err: any) {
      setSnack({ message: err?.response?.data?.detail || 'Nie udalo sie usunac tenanta', severity: 'error' })
    }
  }

  return (
    <Stack spacing={2}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h4">{currentUser?.is_superadmin ? 'Tenanty i bezpieczenstwo' : 'Uzytkownicy i uprawnienia'}</Typography>
        {!currentUser?.is_superadmin ? (
          <Button variant="contained" startIcon={<PersonAdd />} onClick={() => setCreateOpen(true)}>
            Dodaj uzytkownika
          </Button>
        ) : null}
      </Stack>
      {!currentUser?.is_superadmin ? (
        <Card>
          <CardContent>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Login</TableCell>
                  <TableCell>Rola systemowa</TableCell>
                  <TableCell>Powiazanie</TableCell>
                  <TableCell>Legacy CAISSE</TableCell>
                  <TableCell>Akcje</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>{user.username}</TableCell>
                    <TableCell>
                      {canEditUserRole(user) ? (
                        <FormControl size="small" sx={{ minWidth: 220 }}>
                          <InputLabel>Rola</InputLabel>
                          <Select
                            label="Rola"
                            value={user.role}
                            onChange={(e) => handleRoleChange(user.id, e.target.value as User['role'])}
                          >
                            {roleOptions.map((r) => (
                              <MenuItem key={r.value} value={r.value}>
                                {r.label}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      ) : (
                        <Chip size="small" label={user.role} />
                      )}
                    </TableCell>
                    <TableCell>
                      {user.linked_staff_id ? (
                        <Stack spacing={0.5}>
                          <Typography variant="body2">
                            {user.linked_staff_name || `Pracownik #${user.linked_staff_id}`}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {user.linked_salon_name || (user.linked_salon_id ? `Salon #${user.linked_salon_id}` : 'Salon nieznany')}
                          </Typography>
                        </Stack>
                      ) : (
                        <Typography variant="body2" color="text.secondary">Nieprzypisane</Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Stack spacing={0.5}>
                        <Switch
                          size="small"
                          checked={Boolean(user.legacy_caisse_enabled) || ['admin', 'manager', 'manager_main'].includes(user.role)}
                          disabled={
                            !tenantHasLegacyCaisse ||
                            currentUser?.role !== 'admin' ||
                            ['admin', 'manager', 'manager_main'].includes(user.role)
                          }
                          onChange={(e) => handleLegacyCaisseAccessChange(user, e.target.checked)}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {!tenantHasLegacyCaisse
                            ? 'Brak licencji tenantowej'
                            : ['admin', 'manager', 'manager_main'].includes(user.role)
                            ? 'Dostep administracyjny'
                            : user.legacy_caisse_enabled
                            ? 'Wlaczony dla pracownika'
                            : 'Wylaczony'}
                        </Typography>
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1}>
                        <IconButton
                          size="small"
                          onClick={() => handleResetPassword(user.id)}
                          disabled={!canDeleteUser(user)}
                        >
                          <LockReset fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(user.id)}
                          disabled={!canDeleteUser(user)}
                        >
                          <Delete fontSize="small" />
                        </IconButton>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
                {!users.length && !loading && (
                  <TableRow>
                    <TableCell colSpan={5}>Brak uzytkownikow</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Zmiana wlasnego hasla</Typography>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField
              label="Obecne haslo"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              fullWidth
            />
            <TextField
              label="Nowe haslo"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              fullWidth
            />
            <TextField
              label="Powtorz nowe haslo"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              fullWidth
            />
            <Button
              variant="contained"
              onClick={handleOwnPasswordChange}
              disabled={!currentPassword || newPassword.length < 10 || newPassword !== confirmPassword}
            >
              Zmien haslo
            </Button>
          </Stack>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            Wymagania: min. 10 znakow, mala i duza litera, cyfra, bez spacji.
          </Typography>
        </CardContent>
      </Card>

      {(currentUser?.role === 'admin' || currentUser?.role === 'manager' || currentUser?.role === 'manager_main' || currentUser?.role === 'manager_salon') && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>TOTP (2FA) dla konta {currentUser?.role}</Typography>
            <Stack spacing={1.5}>
              <Typography variant="body2" color="text.secondary">
                Status: {totpEnabled ? 'Wlaczone' : 'Wylaczone'}
              </Typography>
              {!totpEnabled && (
                <Stack spacing={1.5}>
                  <Stack direction="row" spacing={1}>
                    <Button variant="outlined" onClick={handleTotpSetup}>Generuj konfiguracje TOTP</Button>
                  </Stack>
                  {totpSecret && (
                    <Stack spacing={1}>
                      <Typography variant="body2">Sekret: <b>{totpSecret}</b></Typography>
                      {totpQrUrl && (
                        <img src={totpQrUrl} alt="TOTP QR" style={{ width: 180, height: 180, border: '1px solid #d1d5db' }} />
                      )}
                      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
                        <TextField
                          label="Kod z aplikacji (6 cyfr)"
                          value={totpSetupCode}
                          onChange={(e) => setTotpSetupCode(e.target.value)}
                        />
                        <Button variant="contained" onClick={handleTotpEnable} disabled={totpSetupCode.trim().length < 6}>
                          Wlacz TOTP
                        </Button>
                      </Stack>
                    </Stack>
                  )}
                </Stack>
              )}
              {totpEnabled && (
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
                  <TextField
                    label="Kod TOTP do wylaczenia"
                    value={totpDisableCode}
                    onChange={(e) => setTotpDisableCode(e.target.value)}
                  />
                  <Button variant="outlined" color="error" onClick={handleTotpDisable} disabled={totpDisableCode.trim().length < 6}>
                    Wylacz TOTP
                  </Button>
                </Stack>
              )}
            </Stack>
          </CardContent>
        </Card>
      )}

      {(currentUser?.role === 'admin' || currentUser?.role === 'manager' || currentUser?.role === 'manager_main' || currentUser?.role === 'manager_salon') && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>Test SMS</Typography>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
              <TextField
                label="Numer telefonu"
                value={smsTestPhone}
                onChange={(e) => setSmsTestPhone(e.target.value)}
                placeholder="+48500100200"
                sx={{ minWidth: 240 }}
              />
              <TextField
                label="Tresc SMS"
                value={smsTestMessage}
                onChange={(e) => setSmsTestMessage(e.target.value)}
                fullWidth
              />
              <Button variant="outlined" onClick={handleSmsTest} disabled={smsTestSending}>
                Wyslij test
              </Button>
            </Stack>
          </CardContent>
        </Card>
      )}

      {currentUser?.is_superadmin && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>Tenanty (superadmin)</Typography>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mb: 2 }}>
              <TextField
                label="Kod"
                value={tenantCode}
                onChange={(e) => setTenantCode(e.target.value)}
                fullWidth
              />
              <TextField
                label="Nazwa"
                value={tenantName}
                onChange={(e) => setTenantName(e.target.value)}
                fullWidth
              />
              <FormControl size="small" sx={{ minWidth: 140 }}>
                <InputLabel>Aktywny</InputLabel>
                <Select
                  label="Aktywny"
                  value={tenantActive ? 'tak' : 'nie'}
                  onChange={(e) => setTenantActive(e.target.value === 'tak')}
                >
                  <MenuItem value="tak">Tak</MenuItem>
                  <MenuItem value="nie">Nie</MenuItem>
                </Select>
              </FormControl>
              <Button
                variant="contained"
                onClick={handleTenantSave}
                disabled={tenantCode.trim().length < 2 || tenantName.trim().length < 2}
              >
                {editingTenantId ? 'Zapisz' : 'Dodaj'}
              </Button>
              {editingTenantId ? <Button onClick={resetTenantForm}>Anuluj</Button> : null}
            </Stack>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Kod</TableCell>
                  <TableCell>Nazwa</TableCell>
                  <TableCell>Aktywny</TableCell>
                  <TableCell>Akcje</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tenants.map((tenant) => (
                  <TableRow key={tenant.id}>
                    <TableCell>{tenant.id}</TableCell>
                    <TableCell>{tenant.code}</TableCell>
                    <TableCell>{tenant.name}</TableCell>
                    <TableCell>{tenant.is_active ? 'TAK' : 'NIE'}</TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1}>
                        <Button size="small" variant="outlined" onClick={() => handleTenantEdit(tenant)}>Edytuj</Button>
                        {tenant.id !== 1 ? (
                          <IconButton size="small" color="error" onClick={() => handleTenantDelete(tenant.id)}>
                            <Delete fontSize="small" />
                          </IconButton>
                        ) : null}
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
                {!tenants.length && (
                  <TableRow>
                    <TableCell colSpan={5}>Brak tenantow</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <Dialog open={!currentUser?.is_superadmin && createOpen} onClose={() => setCreateOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Dodaj uzytkownika</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Login"
              value={createUsername}
              onChange={(e) => setCreateUsername(e.target.value)}
              fullWidth
            />
            <TextField
              label="Haslo"
              type="password"
              value={createPassword}
              onChange={(e) => setCreatePassword(e.target.value)}
              fullWidth
            />
            <FormControl fullWidth>
              <InputLabel>Rola</InputLabel>
              <Select
                label="Rola"
                value={createRole}
                onChange={(e) => setCreateRole(e.target.value as User['role'])}
              >
                {roleOptions.map((r) => (
                  <MenuItem key={r.value} value={r.value}>
                    {r.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Anuluj</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={createUsername.trim().length < 3 || createPassword.length < 10}
          >
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snack} autoHideDuration={3500} onClose={() => setSnack(null)}>
        <Alert onClose={() => setSnack(null)} severity={snack?.severity ?? 'success'} variant="filled">
          {snack?.message}
        </Alert>
      </Snackbar>
    </Stack>
  )
}

export default AdminUsersPage
