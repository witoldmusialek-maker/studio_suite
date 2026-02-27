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
  const [snack, setSnack] = useState<{ message: string; severity: 'success' | 'error' } | null>(null)

  const roleOptions = useMemo(() => {
    if (currentUser?.role === 'admin') {
      return [
        { value: 'admin', label: 'Admin' },
        { value: 'manager', label: 'Manager' },
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

  useEffect(() => {
    fetchUsers()
  }, [])

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
    return currentUser?.role === 'manager' && (role === 'employee' || role === 'receptionist')
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

  return (
    <Stack spacing={2}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h4">Uzytkownicy i uprawnienia</Typography>
        <Button variant="contained" startIcon={<PersonAdd />} onClick={() => setCreateOpen(true)}>
          Dodaj uzytkownika
        </Button>
      </Stack>
      <Card>
        <CardContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Login</TableCell>
                <TableCell>Rola systemowa</TableCell>
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
                  <TableCell colSpan={3}>Brak uzytkownikow</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

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

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} fullWidth maxWidth="sm">
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
