import { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardMedia,
  CardContent,
  CardActions,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  Delete as DeleteIcon,
  CloudUpload as UploadIcon,
} from '@mui/icons-material'
import { api } from '../services/api'
import { Content } from '../types'
import { useAuth } from '../contexts/AuthContext'

const ContentPage = () => {
  const { user } = useAuth()
  const [contents, setContents] = useState<Content[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [openDialog, setOpenDialog] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchContents()
  }, [])

  const fetchContents = async () => {
    try {
      const response = await api.get('/content')
      setContents(response.data.items || response.data)
    } catch (error) {
      console.error('Błąd pobierania treści:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setOpenDialog(true)
      setError('')
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setUploading(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      await api.post('/content/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setOpenDialog(false)
      setSelectedFile(null)
      fetchContents()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Błąd uploadu')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Czy na pewno chcesz usunąć tę treść?')) {
      return
    }

    try {
      await api.delete(`/content/${id}`)
      fetchContents()
    } catch (error) {
      console.error('Błąd usuwania:', error)
    }
  }

  const getContentTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      image: 'Obraz',
      pdf: 'PDF',
      excel: 'Excel',
      video: 'Video',
    }
    return labels[type] || type
  }

  if (loading) {
    return <Typography>Ładowanie...</Typography>
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Treści</Typography>
        {user?.role === 'admin' && (
          <>
            <input
              accept="image/*,application/pdf,.xlsx,.xls,video/*"
              style={{ display: 'none' }}
              id="upload-file"
              type="file"
              onChange={handleFileSelect}
            />
            <label htmlFor="upload-file">
              <Button
                variant="contained"
                component="span"
                startIcon={<UploadIcon />}
              >
                Upload
              </Button>
            </label>
          </>
        )}
      </Box>

      <Grid container spacing={3}>
        {contents.map((content) => (
          <Grid item xs={12} sm={6} md={4} key={content.id}>
            <Card>
              {content.thumbnail_path && (
                <CardMedia
                  component="img"
                  height="200"
                  image={`${window.location.origin}${content.thumbnail_path}`}
                  alt={content.filename}
                />
              )}
              <CardContent>
                <Typography variant="h6" noWrap>
                  {content.original_filename}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Typ: {getContentTypeLabel(content.type)}
                </Typography>
                {content.file_size_mb && (
                  <Typography variant="body2" color="text.secondary">
                    Rozmiar: {content.file_size_mb} MB
                  </Typography>
                )}
              </CardContent>
              {user?.role === 'admin' && (
                <CardActions>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDelete(content.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </CardActions>
              )}
            </Card>
          </Grid>
        ))}
      </Grid>

      {contents.length === 0 && (
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Typography variant="h6" color="text.secondary">
            Brak treści
          </Typography>
        </Box>
      )}

      <Dialog open={openDialog} onClose={() => !uploading && setOpenDialog(false)}>
        <DialogTitle>Upload Treści</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          {selectedFile && (
            <Typography variant="body1">
              Plik: {selectedFile.name}
            </Typography>
          )}
          {uploading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <CircularProgress />
            </Box>
          )}
        </DialogContent>
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
          <Button onClick={() => setOpenDialog(false)} disabled={uploading}>
            Anuluj
          </Button>
          <Button
            onClick={handleUpload}
            variant="contained"
            disabled={!selectedFile || uploading}
          >
            Upload
          </Button>
        </Box>
      </Dialog>
    </Box>
  )
}

export default ContentPage


