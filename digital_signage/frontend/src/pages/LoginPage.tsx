import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Container,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useAuth } from '../contexts/AuthContext'

const LoginPage = () => {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('demo123')
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    try {
      await login(username, password)
      navigate('/')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Blad logowania')
    }
  }

  return (
    <Container maxWidth="sm">
      <Box sx={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
        <Paper sx={{ width: '100%', p: 4 }}>
          <Typography variant="h4" sx={{ mb: 1 }}>Salon Booking Frontend</Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>
            Demo UX do konsultacji przed implementacja backendu.
          </Typography>

          <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap' }}>
            <Button size="small" variant="outlined" onClick={() => setUsername('admin')}>admin</Button>
            <Button size="small" variant="outlined" onClick={() => setUsername('manager')}>manager</Button>
            <Button size="small" variant="outlined" onClick={() => setUsername('recepcja')}>recepcja</Button>
          </Stack>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              label="Login"
              fullWidth
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              sx={{ mb: 2 }}
            />
            <TextField
              label="Haslo"
              type="password"
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Button type="submit" variant="contained" fullWidth>
              Wejdz do panelu
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}

export default LoginPage
