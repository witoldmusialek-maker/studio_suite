import { useEffect, useState, useRef } from 'react'
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Upload as UploadIcon,
} from '@mui/icons-material'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

type SoundFile = {
  id: number
  name: string
  file_path: string
  file_size?: number
  duration?: string
  type: 'bell' | 'announcement'
}

const SoundsPage = () => {
  const { user } = useAuth()
  const [sounds, setSounds] = useState<SoundFile[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [search, setSearch] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  // Audio player state
  const [playingId, setPlayingId] = useState<number | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    fetchSounds()
  }, [])

  const fetchSounds = async () => {
    try {
      // Pobierz dzwonki jako źródło plików dźwiękowych
      const response = await api.get('/bells')
      const bellsData = response.data || []
      
      // Pobierz też pliki z katalogu sounds
      const soundsData: SoundFile[] = bellsData
        .filter((b: any) => b.sound_file_path)
        .map((b: any) => ({
          id: b.id,
          name: b.name,
          file_path: b.sound_file_path,
          type: 'bell' as const,
        }))
      
      setSounds(soundsData)
    } catch (err) {
      console.error('Błąd pobierania dźwięków:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setError('')
    setSuccess('')

    try {
      // 1. Upload pliku
      const formData = new FormData()
      formData.append('file', file)
      
      const uploadRes = await api.post('/bells/upload-sound', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      
      const filePath = uploadRes.data.file_path
      
      // 2. Utwórz rekord dzwonka w bazie
      const fileName = file.name.replace(/\.[^/.]+$/, '') // nazwa bez rozszerzenia
      await api.post('/bells', {
        name: fileName,
        bell_time: '00:00:00', // domyślna godzina (do ustawienia później)
        sound_file_path: filePath,
        volume: 50,
        active: true,
        play_on_displays: false,
      })
      
      setSuccess(`Plik "${file.name}" został wgrany pomyślnie i dodany do biblioteki`)
      fetchSounds()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Błąd uploadu')
    } finally {
      setUploading(false)
    }
  }

  const handlePlay = async (sound: SoundFile) => {
    // Zatrzymaj obecnie odtwarzany
    if (playingId === sound.id) {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
      setPlayingId(null)
      return
    }

    // Zatrzymaj poprzedni
    if (audioRef.current) {
      audioRef.current.pause()
    }

    // Utwórz nowy audio
    try {
      const audioUrl = `http://localhost:8000/api/v1/bells/${sound.id}/sound-file`
      audioRef.current = new Audio(audioUrl)
      audioRef.current.onended = () => setPlayingId(null)
      audioRef.current.onerror = () => {
        setError('Nie można odtworzyć pliku')
        setPlayingId(null)
      }
      await audioRef.current.play()
      setPlayingId(sound.id)
    } catch (err) {
      setError('Błąd odtwarzania')
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Usunąć ten plik dźwiękowy?')) return
    
    try {
      await api.delete(`/bells/${id}`)
      fetchSounds()
    } catch (err) {
      setError('Błąd usuwania')
    }
  }

  const filteredSounds = sounds.filter(s => 
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.file_path?.toLowerCase().includes(search.toLowerCase())
  )

  const getFormat = (path: string) => {
    if (path.endsWith('.mp3')) return 'MP3'
    if (path.endsWith('.wav')) return 'WAV'
    if (path.endsWith('.ogg')) return 'OGG'
    return 'AUDIO'
  }

  if (loading) {
    return <Typography>Ładowanie biblioteki dźwięków...</Typography>
  }

  return (
    <Box>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4">Biblioteka dźwięków</Typography>
          {user?.role === 'admin' && (
            <>
              <input
                accept=".mp3,.wav,.ogg,audio/*"
                style={{ display: 'none' }}
                id="upload-sound-file"
                type="file"
                onChange={handleUpload}
              />
              <label htmlFor="upload-sound-file">
                <Button
                  variant="contained"
                  component="span"
                  startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : <UploadIcon />}
                  disabled={uploading}
                >
                  {uploading ? 'Wgrywanie...' : 'Upload dźwięku'}
                </Button>
              </label>
            </>
          )}
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

        <TextField
          fullWidth
          size="small"
          placeholder="Szukaj dźwięku..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ mb: 2 }}
        />

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Obsługiwane formaty: MP3, WAV, OGG. Maksymalny rozmiar: 5 MB.
        </Typography>
      </Paper>

      <Paper sx={{ p: 2 }}>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Nazwa</TableCell>
                <TableCell>Plik</TableCell>
                <TableCell>Format</TableCell>
                <TableCell>Długość</TableCell>
                <TableCell>Typ</TableCell>
                <TableCell>Akcje</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredSounds.map((sound) => (
                <TableRow key={sound.id} hover>
                  <TableCell>{sound.id}</TableCell>
                  <TableCell>
                    <Typography fontWeight={600}>{sound.name}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                      {sound.file_path?.split('/').pop()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip size="small" label={getFormat(sound.file_path)} />
                  </TableCell>
                  <TableCell>{sound.duration || '-'}</TableCell>
                  <TableCell>
                    <Chip 
                      size="small" 
                      color={sound.type === 'bell' ? 'primary' : 'secondary'}
                      label={sound.type === 'bell' ? 'Dzwonek' : 'Zapowiedź'} 
                    />
                  </TableCell>
                  <TableCell>
                    <IconButton 
                      size="small" 
                      color={playingId === sound.id ? 'primary' : 'default'}
                      onClick={() => handlePlay(sound)}
                    >
                      {playingId === sound.id ? <StopIcon /> : <PlayIcon />}
                    </IconButton>
                    {user?.role === 'admin' && (
                      <IconButton size="small" color="error" onClick={() => handleDelete(sound.id)}>
                        <DeleteIcon />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {filteredSounds.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="text.secondary">
                      Brak plików dźwiękowych. Użyj przycisku "Upload dźwięku" aby dodać pierwszy plik.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  )
}

export default SoundsPage
