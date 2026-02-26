import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Container,
  Paper,
  TextField,
  Typography,
} from '@mui/material'
import { useAuth } from '../contexts/AuthContext'

const LoginPage = () => {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('Admin2026.')
  const [website, setWebsite] = useState('')
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    try {
      if (website.trim()) {
        throw new Error('Blad logowania')
      }
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
            Logowanie do backend API.
          </Typography>

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
            <TextField
              label="Website"
              fullWidth
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              sx={{ display: 'none' }}
              tabIndex={-1}
              autoComplete="off"
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
