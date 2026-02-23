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

type UserRole = 'admin' | 'operator'

type UserAdminDto = {
  id: number
  username: string
  role: UserRole
  created_at: string
  last_login?: string | null
}

const AdminUsersPage = () => {
  const { user } = useAuth()
  const [users, setUsers] = useState<UserAdminDto[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [openCreate, setOpenCreate] = useState(false)
  const [newUsername, setNewUsername] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newRole, setNewRole] = useState<UserRole>('operator')
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
      setUsers(res.data || [])
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udało się pobrać użytkowników.')
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
      setNewRole('operator')
      setInfo('Użytkownik został utworzony.')
      fetchUsers()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udało się utworzyć użytkownika.')
    }
  }

  const updateRole = async (target: UserAdminDto, role: UserRole) => {
    setError('')
    setInfo('')
    try {
      await api.patch(`/auth/users/${target.id}`, { role })
      setInfo(`Zmieniono rolę użytkownika ${target.username}.`)
      fetchUsers()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udało się zmienić roli.')
    }
  }

  const deleteUser = async (target: UserAdminDto) => {
    if (!window.confirm(`Usunąć użytkownika ${target.username}?`)) return
    setError('')
    setInfo('')
    try {
      await api.delete(`/auth/users/${target.id}`)
      setInfo(`Usunięto użytkownika ${target.username}.`)
      fetchUsers()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udało się usunąć użytkownika.')
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
        setInfo(`Hasło użytkownika ${resetUser.username} zostało zresetowane.`)
      }
      setResetPassword('')
      fetchUsers()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udało się zresetować hasła.')
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
      setInfo('Twoje hasło zostało zmienione.')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udało się zmienić hasła.')
    }
  }

  if (user?.role !== 'admin') {
    return <Typography>Brak uprawnień do tej sekcji.</Typography>
  }

  if (loading) {
    return <Typography>Ładowanie użytkowników...</Typography>
  }

  return (
    <Box>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mb: 2 }}>
        <Typography variant="h4">Administracja użytkownikami</Typography>
        <Button variant="contained" onClick={() => setOpenCreate(true)}>Dodaj użytkownika</Button>
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {info && <Alert severity="success" sx={{ mb: 2 }}>{info}</Alert>}
      {generatedPassword && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Wygenerowane hasło tymczasowe: <strong>{generatedPassword}</strong>
        </Alert>
      )}

      <Grid container spacing={2}>
        <Grid item xs={12} md={8}>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Użytkownik</TableCell>
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
                        <MenuItem value="admin">admin</MenuItem>
                        <MenuItem value="operator">operator</MenuItem>
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
                          Reset hasła
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          variant="outlined"
                          disabled={u.id === user?.id}
                          onClick={() => deleteUser(u)}
                        >
                          Usuń
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
              <Typography variant="h6" sx={{ mb: 2 }}>Zmiana mojego hasła</Typography>
              <Stack spacing={1.5}>
                <TextField
                  type="password"
                  size="small"
                  label="Aktualne hasło"
                  value={changeCurrentPassword}
                  onChange={(e) => setChangeCurrentPassword(e.target.value)}
                />
                <TextField
                  type="password"
                  size="small"
                  label="Nowe hasło"
                  value={changeNewPassword}
                  onChange={(e) => setChangeNewPassword(e.target.value)}
                />
                <Button variant="contained" onClick={changeMyPassword}>Zmień hasło</Button>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={openCreate} onClose={() => setOpenCreate(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Nowy użytkownik</DialogTitle>
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
              label="Hasło"
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
              <MenuItem value="admin">admin</MenuItem>
              <MenuItem value="operator">operator</MenuItem>
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreate(false)}>Anuluj</Button>
          <Button variant="contained" onClick={createUser}>Utwórz</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openReset} onClose={() => setOpenReset(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Reset hasła: {resetUser?.username}</DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 0.5 }}>
            <Typography variant="body2" color="text.secondary">
              Zostaw puste, aby wygenerować hasło tymczasowe.
            </Typography>
            <TextField
              size="small"
              type="password"
              label="Nowe hasło (opcjonalnie)"
              value={resetPassword}
              onChange={(e) => setResetPassword(e.target.value)}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenReset(false)}>Anuluj</Button>
          <Button variant="contained" onClick={submitResetPassword}>Resetuj</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default AdminUsersPage
