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
import { getBranding } from '../config/branding'

const LoginPage = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [website, setWebsite] = useState('')
  const [totpCode, setTotpCode] = useState('')
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()
  const branding = getBranding(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    try {
      if (website.trim()) {
        throw new Error('Błąd logowania')
      }
      await login(username, password, totpCode || undefined)
      navigate('/')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Błąd logowania'
      if (message === 'TOTP_REQUIRED') {
        setError('Podaj kod TOTP z aplikacji uwierzytelniajacej.')
        return
      }
      if (message === 'TOTP_INVALID') {
        setError('Niepoprawny kod TOTP.')
        return
      }
      setError(message)
    }
  }

  return (
    <Container maxWidth="sm">
      <Box sx={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
        <Paper sx={{ width: '100%', p: 4 }}>
          <Typography variant="h4" sx={{ mb: 1 }}>{branding.loginTitle}</Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>
            {branding.loginSubtitle}
          </Typography>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              label="Login"
              fullWidth
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              sx={{ mb: 2 }}
              autoComplete="username"
            />
            <TextField
              label="Haslo"
              type="password"
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              sx={{ mb: 2 }}
              autoComplete="current-password"
            />
            <TextField
              label="Kod TOTP"
              fullWidth
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value)}
              sx={{ mb: 2 }}
              inputProps={{ inputMode: 'numeric', maxLength: 8 }}
              helperText="Wpisz kod, jeśli konto ma włączone 2FA."
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
            <Button type="submit" variant="contained" fullWidth sx={{ bgcolor: '#1f1b14' }}>
              Wejdź do panelu
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}

export default LoginPage
