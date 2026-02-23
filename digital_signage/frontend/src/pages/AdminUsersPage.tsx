import { useEffect, useState } from 'react'
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
  Grid,
  MenuItem,
  Paper,
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
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

type UserRole = 'admin' | 'operator_displays' | 'operator_bells' | 'operator'

type UserAdminDto = {
  id: number
  username: string
  role: UserRole
  created_at: string
  last_login?: string | null
}

const roleLabel = (role: UserRole) => {
  const labels: Record<UserRole, string> = {
    admin: 'Administrator',
    operator_displays: 'Operator wyswietlaczy',
    operator_bells: 'Operator dzwonkow',
    operator: 'Operator wyswietlaczy (legacy)',
  }
  return labels[role] || role
}

const normalizeRole = (role: string): UserRole => {
  const normalized = String(role || '').toLowerCase()
  if (normalized === 'admin') return 'admin'
  if (normalized === 'operator_displays') return 'operator_displays'
  if (normalized === 'operator_bells') return 'operator_bells'
  return 'operator'
}

const AdminUsersPage = () => {
  const { user } = useAuth()
  const [users, setUsers] = useState<UserAdminDto[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [openCreate, setOpenCreate] = useState(false)
  const [newUsername, setNewUsername] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newRole, setNewRole] = useState<UserRole>('operator_displays')
  const [openReset, setOpenReset] = useState(false)
  const [resetUser, setResetUser] = useState<UserAdminDto | null>(null)
  const [resetPassword, setResetPassword] = useState('')
  const [generatedPassword, setGeneratedPassword] = useState('')
  const [changeCurrentPassword, setChangeCurrentPassword] = useState('')
  const [changeNewPassword, setChangeNewPassword] = useState('')
  const [info, setInfo] = useState('')

  const fetchUsers = async () => {
    try {
      const res = await api.get<UserAdminDto[]>('/auth/users')
      setUsers(
        (res.data || []).map((u) => ({
          ...u,
          role: normalizeRole(String(u.role)),
        }))
      )
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac uzytkownikow.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  const createUser = async () => {
    setError('')
    setInfo('')
    try {
      await api.post('/auth/register', {
        username: newUsername.trim(),
        password: newPassword,
        role: newRole,
      })
      setOpenCreate(false)
      setNewUsername('')
      setNewPassword('')
      setNewRole('operator_displays')
      setInfo('Uzytkownik zostal utworzony.')
      await fetchUsers()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie utworzyc uzytkownika.')
    }
  }

  const updateRole = async (target: UserAdminDto, role: UserRole) => {
    setError('')
    setInfo('')
    try {
      await api.patch(`/auth/users/${target.id}`, { role })
      setInfo(`Zmieniono role uzytkownika ${target.username}.`)
      await fetchUsers()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zmienic roli.')
    }
  }

  const deleteUser = async (target: UserAdminDto) => {
    if (!window.confirm(`Usunac uzytkownika ${target.username}?`)) return
    setError('')
    setInfo('')
    try {
      await api.delete(`/auth/users/${target.id}`)
      setInfo(`Usunieto uzytkownika ${target.username}.`)
      await fetchUsers()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie usunac uzytkownika.')
    }
  }

  const submitResetPassword = async () => {
    if (!resetUser) return
    setError('')
    setInfo('')
    setGeneratedPassword('')
    try {
      const res = await api.post<{ temporary_password?: string; message: string }>(
        `/auth/users/${resetUser.id}/reset-password`,
        { new_password: resetPassword.trim() || null }
      )

      if (res.data?.temporary_password) {
        setGeneratedPassword(res.data.temporary_password)
      } else {
        setInfo(`Haslo uzytkownika ${resetUser.username} zostalo zresetowane.`)
      }

      setResetPassword('')
      setOpenReset(false)
      setResetUser(null)
      await fetchUsers()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zresetowac hasla.')
    }
  }

  const changeMyPassword = async () => {
    setError('')
    setInfo('')
    try {
      await api.post('/auth/change-password', {
        current_password: changeCurrentPassword,
        new_password: changeNewPassword,
      })
      setChangeCurrentPassword('')
      setChangeNewPassword('')
      setInfo('Twoje haslo zostalo zmienione.')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zmienic hasla.')
    }
  }

  if (user?.role !== 'admin') {
    return <Typography>Brak uprawnien do tej sekcji.</Typography>
  }

  if (loading) {
    return <Typography>Ladowanie uzytkownikow...</Typography>
  }

  return (
    <Box>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mb: 2 }}>
        <Typography variant="h4">Administracja uzytkownikami</Typography>
        <Button variant="contained" onClick={() => setOpenCreate(true)}>Dodaj uzytkownika</Button>
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {info && <Alert severity="success" sx={{ mb: 2 }}>{info}</Alert>}
      {generatedPassword && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Wygenerowane haslo tymczasowe: <strong>{generatedPassword}</strong>
        </Alert>
      )}

      <Grid container spacing={2}>
        <Grid item xs={12} md={8}>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Uzytkownik</TableCell>
                  <TableCell>Rola</TableCell>
                  <TableCell>Ostatnie logowanie</TableCell>
                  <TableCell align="right">Akcje</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell>{u.username}</TableCell>
                    <TableCell sx={{ minWidth: 170 }}>
                      <TextField
                        size="small"
                        select
                        fullWidth
                        value={u.role}
                        onChange={(e) => updateRole(u, e.target.value as UserRole)}
                      >
                        <MenuItem value="admin">{roleLabel('admin')}</MenuItem>
                        <MenuItem value="operator_displays">{roleLabel('operator_displays')}</MenuItem>
                        <MenuItem value="operator_bells">{roleLabel('operator_bells')}</MenuItem>
                        <MenuItem value="operator">{roleLabel('operator')}</MenuItem>
                      </TextField>
                    </TableCell>
                    <TableCell>{u.last_login ? new Date(u.last_login).toLocaleString() : '-'}</TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={1} justifyContent="flex-end">
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => {
                            setResetUser(u)
                            setOpenReset(true)
                            setResetPassword('')
                            setGeneratedPassword('')
                          }}
                        >
                          Reset hasla
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          variant="outlined"
                          disabled={u.id === user?.id}
                          onClick={() => deleteUser(u)}
                        >
                          Usun
                        </Button>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Zmiana mojego hasla</Typography>
              <Stack spacing={1.5}>
                <TextField
                  type="password"
                  size="small"
                  label="Aktualne haslo"
                  value={changeCurrentPassword}
                  onChange={(e) => setChangeCurrentPassword(e.target.value)}
                />
                <TextField
                  type="password"
                  size="small"
                  label="Nowe haslo"
                  value={changeNewPassword}
                  onChange={(e) => setChangeNewPassword(e.target.value)}
                />
                <Button variant="contained" onClick={changeMyPassword}>Zmien haslo</Button>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={openCreate} onClose={() => setOpenCreate(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Nowy uzytkownik</DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 0.5 }}>
            <TextField
              size="small"
              label="Login"
              value={newUsername}
              onChange={(e) => setNewUsername(e.target.value)}
            />
            <TextField
              size="small"
              type="password"
              label="Haslo"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <TextField
              size="small"
              select
              label="Rola"
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as UserRole)}
            >
              <MenuItem value="admin">{roleLabel('admin')}</MenuItem>
              <MenuItem value="operator_displays">{roleLabel('operator_displays')}</MenuItem>
              <MenuItem value="operator_bells">{roleLabel('operator_bells')}</MenuItem>
              <MenuItem value="operator">{roleLabel('operator')}</MenuItem>
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreate(false)}>Anuluj</Button>
          <Button variant="contained" onClick={createUser}>Utworz</Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={openReset}
        onClose={() => {
          setOpenReset(false)
          setResetUser(null)
        }}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Reset hasla: {resetUser?.username}</DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 0.5 }}>
            <Typography variant="body2" color="text.secondary">
              Zostaw puste, aby wygenerowac haslo tymczasowe.
            </Typography>
            <TextField
              size="small"
              type="password"
              label="Nowe haslo (opcjonalnie)"
              value={resetPassword}
              onChange={(e) => setResetPassword(e.target.value)}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setOpenReset(false)
              setResetUser(null)
            }}
          >
            Anuluj
          </Button>
          <Button variant="contained" onClick={submitResetPassword}>Resetuj</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default AdminUsersPage
