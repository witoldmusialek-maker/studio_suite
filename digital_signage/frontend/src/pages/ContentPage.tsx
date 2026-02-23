import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardMedia,
  Chip,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  MenuItem,
  IconButton,
  InputAdornment,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayArrowIcon,
  Description as DescriptionIcon,
  Image as ImageIcon,
  Movie as MovieIcon,
  PictureAsPdf as PdfIcon,
  Search as SearchIcon,
  TableChart as TableChartIcon,
} from '@mui/icons-material'
import { api } from '../services/api'
import { Content } from '../types'
import { useAuth } from '../contexts/AuthContext'

const PREVIEW_HEIGHT = 190

type ContentTypeFilter = 'all' | 'image' | 'video' | 'pdf' | 'excel'

const ContentPage = () => {
  const { user } = useAuth()
  const [contents, setContents] = useState<Content[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [openDialog, setOpenDialog] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<ContentTypeFilter>('all')
  const [previewContent, setPreviewContent] = useState<Content | null>(null)
  const [failedThumbnails, setFailedThumbnails] = useState<Record<number, boolean>>({})

  useEffect(() => {
    fetchContents()
  }, [])

  const fetchContents = async () => {
    try {
      const response = await api.get('/content')
      setContents(response.data.items || response.data)
    } catch (fetchError) {
      console.error('Błąd pobierania treści:', fetchError)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setSelectedFile(file)
    setOpenDialog(true)
    setError('')
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
    } catch (uploadError: any) {
      setError(uploadError.response?.data?.detail || 'Błąd uploadu')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Czy na pewno chcesz usunąć tę treść?')) return

    try {
      await api.delete(`/content/${id}`)
      fetchContents()
    } catch (deleteError) {
      console.error('Błąd usuwania:', deleteError)
    }
  }

  const getContentTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      image: 'Obraz',
      pdf: 'PDF',
      excel: 'Excel',
      video: 'Wideo',
    }
    return labels[type] || type
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <ImageIcon sx={{ fontSize: 48 }} />
      case 'video':
        return <MovieIcon sx={{ fontSize: 48 }} />
      case 'pdf':
        return <PdfIcon sx={{ fontSize: 48 }} />
      case 'excel':
        return <TableChartIcon sx={{ fontSize: 48 }} />
      default:
        return <DescriptionIcon sx={{ fontSize: 48 }} />
    }
  }

  const formatSize = (mb?: number) => {
    if (mb === undefined || mb === null) return '-'
    return `${Number(mb).toFixed(2)} MB`
  }

  const getThumbnailUrl = (content: Content) => `/api/v1/content/${content.id}/thumbnail`
  const getDownloadUrl = (content: Content) => `/api/v1/content/${content.id}/download`

  const stats = useMemo(() => {
    return {
      total: contents.length,
      images: contents.filter((c) => c.type === 'image').length,
      videos: contents.filter((c) => c.type === 'video').length,
      documents: contents.filter((c) => c.type === 'pdf' || c.type === 'excel').length,
    }
  }, [contents])

  const filteredContents = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()

    return contents.filter((content) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        content.original_filename.toLowerCase().includes(normalizedSearch) ||
        content.filename.toLowerCase().includes(normalizedSearch)

      const matchesType = typeFilter === 'all' || content.type === typeFilter

      return matchesSearch && matchesType
    })
  }, [contents, search, typeFilter])

  if (loading) {
    return <Typography>Ładowanie...</Typography>
  }

  return (
    <Box>
      <Paper
        sx={{
          p: 2.5,
          mb: 2.5,
          borderRadius: 3,
          background: 'linear-gradient(145deg, #f6f8fb 0%, #ffffff 60%)',
        }}
      >
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2}>
          <Box>
            <Typography variant="h4">Biblioteka treści</Typography>
            <Typography color="text.secondary">Zarządzaj materiałami do emisji na wyświetlaczach</Typography>
          </Box>
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
                <Button variant="contained" component="span" startIcon={<UploadIcon />} size="large">
                  Dodaj plik
                </Button>
              </label>
            </>
          )}
        </Stack>

        <Grid container spacing={1.5} sx={{ mt: 1.5, mb: 1.5 }}>
          <Grid item xs={6} md={3}>
            <Card variant="outlined"><CardContent><Typography variant="body2" color="text.secondary">Wszystkie</Typography><Typography variant="h5">{stats.total}</Typography></CardContent></Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card variant="outlined"><CardContent><Typography variant="body2" color="text.secondary">Obrazy</Typography><Typography variant="h5">{stats.images}</Typography></CardContent></Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card variant="outlined"><CardContent><Typography variant="body2" color="text.secondary">Wideo</Typography><Typography variant="h5">{stats.videos}</Typography></CardContent></Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card variant="outlined"><CardContent><Typography variant="body2" color="text.secondary">Dokumenty</Typography><Typography variant="h5">{stats.documents}</Typography></CardContent></Card>
          </Grid>
        </Grid>

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
          <TextField
            fullWidth
            size="small"
            placeholder="Szukaj po nazwie pliku..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
          <TextField
            select
            size="small"
            label="Typ"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as ContentTypeFilter)}
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="all">Wszystkie</MenuItem>
            <MenuItem value="image">Obraz</MenuItem>
            <MenuItem value="video">Wideo</MenuItem>
            <MenuItem value="pdf">PDF</MenuItem>
            <MenuItem value="excel">Excel</MenuItem>
          </TextField>
        </Stack>
      </Paper>

      <Grid container spacing={2}>
        {filteredContents.map((content) => (
          <Grid item xs={12} sm={6} lg={4} xl={3} key={content.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                borderRadius: 3,
                border: '1px solid',
                borderColor: 'divider',
                transition: 'transform 160ms ease, box-shadow 160ms ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: 4,
                },
              }}
            >
              <Box
                sx={{
                  height: PREVIEW_HEIGHT,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  bgcolor: '#f4f6fa',
                  overflow: 'hidden',
                }}
              >
                {content.thumbnail_path && !failedThumbnails[content.id] ? (
                  <CardMedia
                    component="img"
                    image={getThumbnailUrl(content)}
                    alt={content.filename}
                    sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    onError={() =>
                      setFailedThumbnails((prev) => ({
                        ...prev,
                        [content.id]: true,
                      }))
                    }
                  />
                ) : content.type === 'image' ? (
                  <CardMedia
                    component="img"
                    image={getDownloadUrl(content)}
                    alt={content.filename}
                    sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                ) : (
                  <Stack alignItems="center" spacing={1} sx={{ color: 'text.secondary' }}>
                    {getTypeIcon(content.type)}
                    <Typography variant="caption">Brak miniatury</Typography>
                  </Stack>
                )}
              </Box>

              <CardContent sx={{ flexGrow: 1, pb: 1.5 }}>
                <Tooltip title={content.original_filename}>
                  <Typography
                    variant="h6"
                    sx={{
                      lineHeight: 1.25,
                      mb: 1,
                      display: '-webkit-box',
                      overflow: 'hidden',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                    }}
                  >
                    {content.original_filename}
                  </Typography>
                </Tooltip>

                <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                  <Chip size="small" label={getContentTypeLabel(content.type)} />
                </Stack>

                <Typography variant="body2" color="text.secondary">
                  Rozmiar: {formatSize(content.file_size_mb)}
                </Typography>
              </CardContent>

              <Box
                sx={{
                  px: 2,
                  pb: 1.5,
                  pt: 0.5,
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
              >
                <Tooltip title="Podgląd / test">
                  <IconButton size="small" color="primary" onClick={() => setPreviewContent(content)}>
                    <PlayArrowIcon />
                  </IconButton>
                </Tooltip>
                {user?.role === 'admin' && (
                  <Tooltip title="Usuń plik">
                    <IconButton size="small" color="error" onClick={() => handleDelete(content.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>

      {filteredContents.length === 0 && (
        <Paper sx={{ textAlign: 'center', mt: 3, p: 4, borderRadius: 3 }}>
          <Typography variant="h6" color="text.secondary">
            Brak treści dla wybranych filtrów
          </Typography>
        </Paper>
      )}

      <Dialog open={openDialog} onClose={() => !uploading && setOpenDialog(false)}>
        <DialogTitle>Dodaj nową treść</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          {selectedFile && <Typography variant="body1">Plik: {selectedFile.name}</Typography>}
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
          <Button onClick={handleUpload} variant="contained" disabled={!selectedFile || uploading}>
            Wyślij
          </Button>
        </Box>
      </Dialog>

      <Dialog
        open={Boolean(previewContent)}
        onClose={() => setPreviewContent(null)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Podgląd testowy: {previewContent?.original_filename}
        </DialogTitle>
        <DialogContent>
          {previewContent?.type === 'image' && (
            <Box
              component="img"
              src={getDownloadUrl(previewContent)}
              alt={previewContent.original_filename}
              sx={{ width: '100%', maxHeight: '70vh', objectFit: 'contain', bgcolor: '#111' }}
            />
          )}
          {previewContent?.type === 'video' && (
            <Box
              component="video"
              src={getDownloadUrl(previewContent)}
              controls
              autoPlay
              sx={{ width: '100%', maxHeight: '70vh', bgcolor: '#000' }}
            />
          )}
          {previewContent?.type === 'pdf' && (
            <Box
              component="iframe"
              src={getDownloadUrl(previewContent)}
              title={previewContent.original_filename}
              sx={{ width: '100%', height: '70vh', border: 0 }}
            />
          )}
          {previewContent?.type === 'excel' && (
            <Stack spacing={2}>
              <Alert severity="info">
                Podgląd Excel w przeglądarce może być ograniczony. Użyj pobierania pliku.
              </Alert>
              <Button
                variant="contained"
                component="a"
                href={getDownloadUrl(previewContent)}
                target="_blank"
                rel="noreferrer"
              >
                Pobierz plik Excel
              </Button>
            </Stack>
          )}
        </DialogContent>
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button onClick={() => setPreviewContent(null)}>Zamknij</Button>
        </Box>
      </Dialog>
    </Box>
  )
}

export default ContentPage
