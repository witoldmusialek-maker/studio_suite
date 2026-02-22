import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  LinearProgress,
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
  Tabs,
  Tab,
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Upload as UploadIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Pause as PauseIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'
import { api } from '../services/api'
import { BellSchedule, Group } from '../types'
import { useAuth } from '../contexts/AuthContext'

// Types
type BellFormData = {
  name: string
  bell_time: string
  event_type: string  // 'lesson' | 'break'
  playlist_id: string
  volume: string
  play_on_displays: boolean
  group_id: string
  active: boolean
}

type RuntimeStatus = {
  server_playback_enabled: boolean
  client_playback_enabled: boolean
  server_player_cmd_configured: boolean
  bells_enabled?: boolean
  pause_until?: string | null
  pause_reason?: string | null
}

type CalendarOverride = {
  id: number
  day: string
  bells_enabled: boolean
  reason?: string | null
}

type BellProfile = {
  id: number
  name: string
  month?: number | null
  is_default: boolean
  is_active: boolean
}

type BellProfileOverride = {
  id: number
  day: string
  profile_id: number
  reason?: string | null
}

type BellSound = {
  id: number
  name: string
  file_path: string
  mime_type?: string | null
  size_bytes?: number | null
  active: boolean
}

type ProfilePlaceholderMap = {
  id: number
  profile_id: number
  placeholder_key: string
  sound_id: number
}

type RuntimePreview = {
  preview_time: string
  runtime_blocked: boolean
  active_profile: string | null
  bells: Array<{ id: number; name: string; bell_time: string }>
}

type MusicSchedule = {
  id: number
  name: string
  start_time: string
  end_time: string
  days_of_week?: number[] | null
  display_ids?: number[] | null
  profile_ids?: number[] | null
  volume: number
  priority: number
  active: boolean
}

type MusicTrack = {
  id: number
  schedule_id: number
  file_path: string
  title?: string | null
  sort_order: number
  active: boolean
  sound_id?: number | null
  placeholder_key?: string | null
  resolved_name?: string | null
  resolved_file_path?: string | null
}

// Constants
const defaultFormData: BellFormData = {
  name: '',
  bell_time: '08:00',
  event_type: 'lesson',  // 'lesson' | 'break'
  playlist_id: '',
  volume: '50',
  play_on_displays: true,
  group_id: '',
  active: true,
}

const dayLabels: Record<number, string> = { 
  1: 'Poniedziałek', 
  2: 'Wtorek', 
  3: 'Środa', 
  4: 'Czwartek', 
  5: 'Piątek', 
  6: 'Sobota', 
  7: 'Niedziela' 
}

const monthLabels: Record<number, string> = {
  1: 'Styczeń',
  2: 'Luty',
  3: 'Marzec',
  4: 'Kwiecień',
  5: 'Maj',
  6: 'Czerwiec',
  7: 'Lipiec',
  8: 'Sierpień',
  9: 'Wrzesień',
  10: 'Październik',
  11: 'Listopad',
  12: 'Grudzień',
}

const placeholderKeys = ['BELL_MAIN', 'BELL_SOFT', 'BELL_BREAK_START', 'BELL_BREAK_END']
const placeholderLabels: Record<string, string> = {
  BELL_MAIN: 'Dzwonek główny',
  BELL_SOFT: 'Dzwonek łagodny',
  BELL_BREAK_START: 'Start przerwy',
  BELL_BREAK_END: 'Koniec przerwy',
}

// Helper functions
const parseCsvNumbers = (value: string) =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => Number(item))
    .filter((item) => !Number.isNaN(item))

const toTimeWithSeconds = (value: string) => (value.length === 5 ? `${value}:00` : value)
const formatTimeForInput = (value: string) => (value ? value.slice(0, 5) : '')

// Sound Row Component - editable name
interface SoundRowProps {
  sound: BellSound
  isAdmin: boolean
  onRename: (id: number, newName: string) => Promise<void>
  onDelete: (id: number) => Promise<void>
}

function SoundRow({ sound, isAdmin, onRename, onDelete }: SoundRowProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editName, setEditName] = useState(sound.name)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!editName.trim() || editName === sound.name) {
      setIsEditing(false)
      return
    }
    setSaving(true)
    await onRename(sound.id, editName.trim())
    setSaving(false)
    setIsEditing(false)
  }

  return (
    <TableRow hover>
      <TableCell>
        {isEditing ? (
          <TextField
            size="small"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            onBlur={handleSave}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSave()
              if (e.key === 'Escape') {
                setEditName(sound.name)
                setIsEditing(false)
              }
            }}
            disabled={saving}
            autoFocus
            sx={{ minWidth: 200 }}
          />
        ) : (
          <Typography fontWeight={600}>{sound.name}</Typography>
        )}
      </TableCell>
      <TableCell>
        <Typography variant="body2" color="text.secondary">
          {sound.file_path?.split('/').pop() || '-'}
        </Typography>
      </TableCell>
      <TableCell>
        <Chip 
          size="small" 
          label={sound.file_path?.toLowerCase().endsWith('.mp3') ? 'MP3' : 'WAV'} 
        />
      </TableCell>
      <TableCell>
        {isAdmin && (
          <Stack direction="row" spacing={1}>
            {!isEditing && (
              <Button 
                size="small" 
                startIcon={<EditIcon />}
                onClick={() => {
                  setEditName(sound.name)
                  setIsEditing(true)
                }}
              >
                Zmień nazwę
              </Button>
            )}
            <Button size="small" color="error" onClick={() => onDelete(sound.id)}>Usuń</Button>
          </Stack>
        )}
      </TableCell>
    </TableRow>
  )
}

// Tab Panel Component
interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  )
}

const BellsPage = () => {
  const { user } = useAuth()
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  // State
  const [tabValue, setTabValue] = useState(0)
  const [bells, setBells] = useState<BellSchedule[]>([])
  const [sounds, setSounds] = useState<BellSound[]>([])
  const [profiles, setProfiles] = useState<BellProfile[]>([])
  const [activeProfile, setActiveProfile] = useState<BellProfile | null>(null)
  const [profileOverrides, setProfileOverrides] = useState<BellProfileOverride[]>([])
  const [profilePlaceholderMap, setProfilePlaceholderMap] = useState<Record<number, ProfilePlaceholderMap[]>>({})
  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatus | null>(null)
  const [calendarOverrides, setCalendarOverrides] = useState<CalendarOverride[]>([])
  const [musicSchedules, setMusicSchedules] = useState<MusicSchedule[]>([])
  const [musicTracks, setMusicTracks] = useState<Record<number, MusicTrack[]>>({})
  const [groups, setGroups] = useState<Group[]>([])

  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingBell, setEditingBell] = useState<BellSchedule | null>(null)
  const [formData, setFormData] = useState<BellFormData>(defaultFormData)
  const [error, setError] = useState('')

  // Form states for different sections
  const [overrideDay, setOverrideDay] = useState('')
  const [overrideEnabled, setOverrideEnabled] = useState<'true' | 'false'>('false')
  const [overrideReason, setOverrideReason] = useState('')

  const [newProfileName, setNewProfileName] = useState('')
  const [newProfileMonth, setNewProfileMonth] = useState('')
  const [newProfileDefault, setNewProfileDefault] = useState<'true' | 'false'>('false')
  const [editingProfileId, setEditingProfileId] = useState<number | null>(null)
  const [editingProfileName, setEditingProfileName] = useState('')
  const [editingProfileMonth, setEditingProfileMonth] = useState('')
  const [profileOverrideDay, setProfileOverrideDay] = useState('')
  const [profileOverrideProfileId, setProfileOverrideProfileId] = useState('')
  const [profileOverrideReason, setProfileOverrideReason] = useState('')
  const [previewAt, setPreviewAt] = useState('')
  const [previewLoading, setPreviewLoading] = useState(false)
  const [runtimePreview, setRuntimePreview] = useState<RuntimePreview | null>(null)
  
  // Music schedule form
  const [musicName, setMusicName] = useState('')
  const [musicStart, setMusicStart] = useState('08:45')
  const [musicEnd, setMusicEnd] = useState('08:55')
  const [musicDays, setMusicDays] = useState('1,2,3,4,5')
  const [musicVolume, setMusicVolume] = useState('35')
  const [musicPriority, setMusicPriority] = useState('0')
  const [musicTrackTitle, setMusicTrackTitle] = useState('')
  const [musicTrackSourceType, setMusicTrackSourceType] = useState<'sound' | 'placeholder'>('sound')
  const [musicTrackSoundId, setMusicTrackSoundId] = useState('')
  const [musicTrackPlaceholderKey, setMusicTrackPlaceholderKey] = useState('BELL_MAIN')
  const [musicTrackOrder, setMusicTrackOrder] = useState('0')
  
  // Upload sound form
  const [uploadSoundName, setUploadSoundName] = useState('')
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [selectedMusicSchedule, setSelectedMusicSchedule] = useState('')
  const [editingMusicSchedule, setEditingMusicSchedule] = useState<MusicSchedule | null>(null)
  const [selectedDaySchedule, setSelectedDaySchedule] = useState<number | null>(null)
  
  // Nowy typ dnia
  const [newDayTypeName, setNewDayTypeName] = useState('')
  const [showNewDayForm, setShowNewDayForm] = useState(false)

  useEffect(() => {
    fetchAll()
  }, [])

  const fetchAll = async () => {
    try {
      const [bellsRes, soundsRes, runtimeRes, dayOverrideRes, profileRes, activeProfileRes, profileOverrideRes, musicScheduleRes, groupsRes] =
        await Promise.all([
          api.get('/bells'),
          api.get('/bells/sounds'),
          api.get('/bells/runtime/status'),
          api.get('/bells/runtime/calendar-overrides'),
          api.get('/bells/runtime/profiles'),
          api.get('/bells/runtime/active-profile'),
          api.get('/bells/runtime/profile-overrides'),
          api.get('/bells/runtime/music-schedules'),
          api.get('/groups'),
        ])

      const bellsData: BellSchedule[] = bellsRes.data || []
      setBells(bellsData)
      setSounds(soundsRes.data || [])
      setRuntimeStatus(runtimeRes.data || null)
      setCalendarOverrides(dayOverrideRes.data || [])
      setProfiles(profileRes.data || [])
      setActiveProfile(activeProfileRes.data || null)
      setProfileOverrides(profileOverrideRes.data || [])
      const musicSchedulesData: MusicSchedule[] = musicScheduleRes.data || []
      setMusicSchedules(musicSchedulesData)
      setGroups(groupsRes.data || [])

      const musicTrackEntries = await Promise.all(
        musicSchedulesData.map(async (schedule) => {
          try {
            const response = await api.get(`/bells/runtime/music-schedules/${schedule.id}/tracks`)
            return [schedule.id, response.data || []] as const
          } catch {
            return [schedule.id, []] as const
          }
        })
      )
      setMusicTracks(Object.fromEntries(musicTrackEntries))

      const placeholderEntries = await Promise.all(
        (profileRes.data || []).map(async (profile: BellProfile) => {
          try {
            const response = await api.get(`/bells/runtime/profiles/${profile.id}/placeholders`)
            return [profile.id, response.data || []] as const
          } catch {
            return [profile.id, []] as const
          }
        })
      )
      setProfilePlaceholderMap(Object.fromEntries(placeholderEntries))
    } catch (fetchError) {
      console.error('Bell page fetch failed:', fetchError)
    } finally {
      setLoading(false)
    }
  }

  const stats = useMemo(() => {
    const active = bells.filter((bell) => bell.active).length
    return { total: bells.length, active, inactive: bells.length - active }
  }, [bells])

  // Bell CRUD handlers
  const handleOpenCreate = () => {
    setEditingBell(null)
    setFormData(defaultFormData)
    setError('')
    setOpenDialog(true)
  }

  const handleOpenEdit = (bell: BellSchedule) => {
    setEditingBell(bell)
    setFormData({
      name: bell.name,
      bell_time: formatTimeForInput(bell.bell_time),
      event_type: bell.event_type || 'lesson',
      playlist_id: bell.playlist_id ? String(bell.playlist_id) : '',
      volume: String(bell.volume),
      play_on_displays: bell.play_on_displays ?? true,
      group_id: bell.group_id ? String(bell.group_id) : '',
      active: bell.active,
    })
    setError('')
    setOpenDialog(true)
  }

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setEditingBell(null)
    setError('')
  }
  const handleSubmit = async () => {
    try {
      const payload: Record<string, unknown> = {
        name: formData.name.trim(),
        bell_time: toTimeWithSeconds(formData.bell_time),
        event_type: formData.event_type || 'lesson',
        volume: Number(formData.volume || 50),
        play_on_displays: formData.play_on_displays,
        group_id: formData.group_id ? Number(formData.group_id) : null,
        days_of_week: selectedDaySchedule ? [selectedDaySchedule] : [],
      }
      if (formData.playlist_id) payload.playlist_id = Number(formData.playlist_id)
      if (editingBell) payload.active = formData.active

      if (editingBell) {
        await api.put(`/bells/${editingBell.id}`, payload)
      } else {
        await api.post('/bells', payload)
      }

      handleCloseDialog()
      fetchAll()
    } catch (submitError: any) {
      setError(submitError.response?.data?.detail || 'Nie udało się zapisać harmonogramu dzwonka')
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Usunąć harmonogram dzwonka?')) return
    try {
      await api.delete(`/bells/${id}`)
      fetchAll()
    } catch (deleteError) {
      console.error('Bell delete failed:', deleteError)
    }
  }

  // Runtime control handlers
  const pauseBells = async (minutes: number, reason: string) => {
    await api.post('/bells/runtime/pause', { minutes, reason })
    fetchAll()
  }

  const resumeBells = async () => {
    await api.post('/bells/runtime/resume')
    fetchAll()
  }

  const setBellsEnabled = async (enabled: boolean) => {
    await api.post(`/bells/runtime/enabled/${enabled}`)
    fetchAll()
  }

  // Calendar override handlers
  const saveDayOverride = async () => {
    if (!overrideDay) return
    await api.post('/bells/runtime/calendar-overrides', {
      day: overrideDay,
      bells_enabled: overrideEnabled === 'true',
      reason: overrideReason || null,
    })
    setOverrideReason('')
    fetchAll()
  }

  const removeDayOverride = async (id: number) => {
    await api.delete(`/bells/runtime/calendar-overrides/${id}`)
    fetchAll()
  }

  // Profile handlers
  const createProfile = async () => {
    if (!newProfileName.trim()) return
    await api.post('/bells/runtime/profiles', {
      name: newProfileName.trim(),
      month: newProfileMonth ? Number(newProfileMonth) : null,
      is_default: newProfileDefault === 'true',
      is_active: true,
    })
    setNewProfileName('')
    setNewProfileMonth('')
    setNewProfileDefault('false')
    fetchAll()
  }

  const setDefaultProfile = async (profileId: number) => {
    await api.put(`/bells/runtime/profiles/${profileId}`, { is_default: true })
    fetchAll()
  }

  const setProfileActive = async (profileId: number, isActive: boolean) => {
    await api.put(`/bells/runtime/profiles/${profileId}`, { is_active: isActive })
    fetchAll()
  }

  const deleteProfile = async (profileId: number) => {
    if (!window.confirm('Usunąć profil?')) return
    await api.delete(`/bells/runtime/profiles/${profileId}`)
    fetchAll()
  }

  const startEditProfile = (profile: BellProfile) => {
    setEditingProfileId(profile.id)
    setEditingProfileName(profile.name)
    setEditingProfileMonth(profile.month ? String(profile.month) : '')
  }

  const cancelEditProfile = () => {
    setEditingProfileId(null)
    setEditingProfileName('')
    setEditingProfileMonth('')
  }

  const saveProfileEdit = async () => {
    if (!editingProfileId || !editingProfileName.trim()) return
    await api.put(`/bells/runtime/profiles/${editingProfileId}`, {
      name: editingProfileName.trim(),
      month: editingProfileMonth ? Number(editingProfileMonth) : null,
    })
    cancelEditProfile()
    fetchAll()
  }

  const setProfilePlaceholder = async (profileId: number, placeholderKey: string, soundId: number) => {
    await api.put(`/bells/runtime/profiles/${profileId}/placeholders/${placeholderKey}`, {
      placeholder_key: placeholderKey,
      sound_id: soundId,
    })
    fetchAll()
  }

  // Profile override handlers
  const saveProfileOverride = async () => {
    if (!profileOverrideDay || !profileOverrideProfileId) return
    await api.post('/bells/runtime/profile-overrides', {
      day: profileOverrideDay,
      profile_id: Number(profileOverrideProfileId),
      reason: profileOverrideReason || null,
    })
    setProfileOverrideReason('')
    fetchAll()
  }

  const removeProfileOverride = async (id: number) => {
    await api.delete(`/bells/runtime/profile-overrides/${id}`)
    fetchAll()
  }

  // Music schedule handlers
  const createMusicSchedule = async () => {
    if (!musicName.trim()) return
    const response = await api.post('/bells/runtime/music-schedules', {
      name: musicName.trim(),
      start_time: toTimeWithSeconds(musicStart),
      end_time: toTimeWithSeconds(musicEnd),
      days_of_week: parseCsvNumbers(musicDays),
      volume: Number(musicVolume || 35),
      priority: Number(musicPriority || 0),
      active: true,
    })
    const newScheduleId = response.data?.id
    setMusicName('')
    await fetchAll()
    // Po utworzeniu pokaż sekcję dodawania utworów
    if (newScheduleId) {
      setSelectedMusicSchedule(String(newScheduleId))
    }
  }

  const updateMusicSchedule = async () => {
    if (!editingMusicSchedule || !musicName.trim()) return
    await api.put(`/bells/runtime/music-schedules/${editingMusicSchedule.id}`, {
      name: musicName.trim(),
      start_time: toTimeWithSeconds(musicStart),
      end_time: toTimeWithSeconds(musicEnd),
      days_of_week: parseCsvNumbers(musicDays),
      volume: Number(musicVolume || 35),
      priority: Number(musicPriority || 0),
      active: musicPriority === '0',
    })
    setEditingMusicSchedule(null)
    setMusicName('')
    setMusicStart('08:45')
    setMusicEnd('08:55')
    setMusicDays('1,2,3,4,5')
    setMusicVolume('35')
    setMusicPriority('0')
    fetchAll()
  }

  const editMusicSchedule = (schedule: MusicSchedule) => {
    setEditingMusicSchedule(schedule)
    setMusicName(schedule.name)
    setMusicStart(formatTimeForInput(schedule.start_time))
    setMusicEnd(formatTimeForInput(schedule.end_time))
    setMusicDays(schedule.days_of_week?.join(',') || '1,2,3,4,5')
    setMusicVolume(String(schedule.volume))
    setMusicPriority(schedule.active ? '0' : '1')
  }

  const removeMusicSchedule = async (id: number) => {
    await api.delete(`/bells/runtime/music-schedules/${id}`)
    if (selectedMusicSchedule === String(id)) {
      setSelectedMusicSchedule('')
    }
    fetchAll()
  }

  const addMusicTrack = async () => {
    if (!selectedMusicSchedule) return

    const payload: Record<string, unknown> = {
      title: musicTrackTitle.trim() || null,
      sort_order: Number(musicTrackOrder || 0),
      active: true,
    }

    if (musicTrackSourceType === 'sound') {
      if (!musicTrackSoundId) return
      payload.sound_id = Number(musicTrackSoundId)
    } else {
      if (!musicTrackPlaceholderKey.trim()) return
      payload.placeholder_key = musicTrackPlaceholderKey.trim().toUpperCase()
    }

    await api.post(`/bells/runtime/music-schedules/${selectedMusicSchedule}/tracks`, payload)
    setMusicTrackTitle('')
    setMusicTrackSoundId('')
    setMusicTrackPlaceholderKey('BELL_MAIN')
    setMusicTrackOrder('0')
    fetchAll()
  }

  const removeMusicTrack = async (trackId: number) => {
    await api.delete(`/bells/runtime/music-tracks/${trackId}`)
    fetchAll()
  }

  // Preview handler
  const checkRuntimePreview = async () => {
    setPreviewLoading(true)
    try {
      const at = previewAt || new Date().toTimeString().slice(0, 5)
      const response = await api.get('/bells/runtime/preview', { params: { at } })
      setRuntimePreview(response.data || null)
    } finally {
      setPreviewLoading(false)
    }
  }

  // Group bells by day of week for "Typy dnia" view
  const bellsByDay = useMemo(() => {
    const grouped: Record<number, BellSchedule[]> = {}
    // Standardowe dni tygodnia (1-7)
    for (let i = 1; i <= 7; i++) {
      grouped[i] = bells
        .filter(b => b.active && (!b.days_of_week || b.days_of_week.length === 0 || b.days_of_week.includes(i)))
        .sort((a, b) => a.bell_time.localeCompare(b.bell_time))
    }
    // Niestandardowe typy dni (ID = 100 + override.id)
    calendarOverrides.forEach((override) => {
      const customDayId = 100 + override.id
      grouped[customDayId] = bells
        .filter(b => b.active && b.days_of_week?.includes(customDayId))
        .sort((a, b) => a.bell_time.localeCompare(b.bell_time))
    })
    return grouped
  }, [bells, calendarOverrides])

  if (loading) return <Typography>Ładowanie harmonogramów dzwonków...</Typography>

  return (
    <Box>
      <Paper sx={{ mb: 2, p: 3, borderRadius: 3, background: 'linear-gradient(145deg, #fff6ef 0%, #fff9f4 58%, #ffffff 100%)' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h4">Dzwonki i Muzyka na Przerwach</Typography>
            <Typography color="text.secondary">
              Dzwonek składa się z dwóch warstw: <b>melodia</b> + <b>zapowiedź słowna</b>
            </Typography>
          </Box>
          <Chip label="PROTOTYP UI 0.2" sx={{ bgcolor: '#ffe083', border: '1px solid #f3c445', fontWeight: 700 }} />
        </Box>
        
        {/* Quick stats */}
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="body2" color="text.secondary">Wszystkie dzwonki</Typography>
                <Typography variant="h5">{stats.total}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="body2" color="text.secondary">Aktywne</Typography>
                <Typography variant="h5" color="success.main">{stats.active}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="body2" color="text.secondary">Playlista przerw</Typography>
                <Typography variant="h5">{musicSchedules.length}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="body2" color="text.secondary">Profile miesięczne</Typography>
                <Typography variant="h5">{profiles.length}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label="1. Playlisty" />
          <Tab label="2. Typy dnia" />
          <Tab label="3. Kalendarz miesiąca" />
          <Tab label="4. Sterowanie teraz" />
        </Tabs>
      </Paper>

      {/* Tab 1: Playlisty */}
      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={2}>
          {/* Biblioteka dźwięków */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box>
                  <Typography variant="h6">Biblioteka dźwięków</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Dzwonki i zapowiedzi słowne do wykorzystania w playlistach.
                  </Typography>
                </Box>
                {user?.role === 'admin' && (
                  <Button 
                    variant="contained" 
                    startIcon={<UploadIcon />} 
                    onClick={() => setShowUploadForm(!showUploadForm)}
                  >
                    {showUploadForm ? 'Anuluj' : '+ Dodaj dźwięk'}
                  </Button>
                )}
              </Box>
              
              {/* Formularz uploadu */}
              {user?.role === 'admin' && showUploadForm && (
                <Card variant="outlined" sx={{ mb: 2, p: 2, bgcolor: '#e3f2fd' }}>
                  <Typography variant="subtitle1" sx={{ mb: 1 }}>Dodaj nowy dźwięk</Typography>
                  <Grid container spacing={1} alignItems="center">
                    <Grid item xs={12} md={4}>
                      <TextField 
                        fullWidth 
                        size="small"
                        label="Nazwa dźwięku" 
                        value={uploadSoundName} 
                        onChange={(e) => setUploadSoundName(e.target.value)}
                        placeholder="np. Dzwonek główny, Zapowiedź lekcja 1"
                      />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <Button 
                        fullWidth 
                        variant="outlined" 
                        component="label"
                        sx={{ height: 40 }}
                      >
                        Wybierz plik WAV/MP3
                        <input
                          type="file"
                          hidden
                          accept=".wav,.mp3"
                          ref={fileInputRef}
                          onChange={async (e) => {
                            const file = e.target.files?.[0]
                            if (!file) return
                            try {
                              setUploading(true)
                              const uploadData = new FormData()
                              uploadData.append('file', file)
                              const nameToUse = uploadSoundName.trim() || file.name.replace(/\.[^/.]+$/, '')
                              uploadData.append('name', nameToUse)
                              await api.post('/bells/upload-sound', uploadData, {
                                headers: { 'Content-Type': 'multipart/form-data' },
                              })
                              setUploadSoundName('')
                              setShowUploadForm(false)
                              fetchAll()
                            } catch (uploadError: any) {
                              setError(uploadError.response?.data?.detail || 'Nie udało się wgrać dźwięku')
                            } finally {
                              setUploading(false)
                            }
                          }}
                        />
                      </Button>
                    </Grid>
                    <Grid item xs={12} md={2}>
                      {uploading && <LinearProgress />}
                    </Grid>
                  </Grid>
                </Card>
              )}
              
              {/* Lista dźwięków */}
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Nazwa</TableCell>
                      <TableCell>Plik</TableCell>
                      <TableCell>Typ</TableCell>
                      <TableCell>Akcje</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {sounds.map((sound) => (
                      <SoundRow 
                        key={sound.id} 
                        sound={sound} 
                        isAdmin={user?.role === 'admin'}
                        onRename={async (id, newName) => {
                          try {
                            await api.put(`/bells/sounds/${id}`, { name: newName })
                            fetchAll()
                          } catch (err) {
                            console.error('Failed to rename sound:', err)
                          }
                        }}
                        onDelete={async (id) => {
                          if (!window.confirm('Usunąć dźwięk z biblioteki?')) return
                          await api.delete(`/bells/sounds/${id}`)
                          fetchAll()
                        }}
                      />
                    ))}
                    {sounds.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          <Typography color="text.secondary">Brak dźwięków. Kliknij "+ Dodaj dźwięk" aby wgrać plik.</Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
          
          {/* Playlisty */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box>
                  <Typography variant="h6">Lista playlist (CRUD)</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Wersja minimalna: odtwarzanie zawsze na serwerze (driver systemowy).
                  </Typography>
                </Box>
                {user?.role === 'admin' && (
                  <Button variant="contained" startIcon={<AddIcon />} onClick={createMusicSchedule}>
                    + Dodaj playlistę
                  </Button>
                )}
              </Box>

              {/* Music schedules table */}
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Nazwa playlisty</TableCell>
                      <TableCell>Liczba utworów</TableCell>
                      <TableCell>Akcje</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {musicSchedules.map((schedule) => (
                      <TableRow 
                        key={schedule.id} 
                        hover 
                        sx={{ cursor: 'pointer' }}
                        onClick={() => setSelectedMusicSchedule(selectedMusicSchedule === String(schedule.id) ? '' : String(schedule.id))}
                      >
                        <TableCell><Typography fontWeight={600}>{schedule.name}</Typography></TableCell>
                        <TableCell>
                          <Chip size="small" label={`${(musicTracks[schedule.id] || []).length} utworów`} />
                        </TableCell>
                        <TableCell>
                          {user?.role === 'admin' && (
                            <>
                              <Button size="small" onClick={(e) => { e.stopPropagation(); setSelectedMusicSchedule(String(schedule.id)) }}>
                                Edytuj utwory
                              </Button>
                              <Button size="small" onClick={(e) => { e.stopPropagation(); editMusicSchedule(schedule) }}>
                                Zmień nazwę
                              </Button>
                              <Button size="small" color="error" onClick={(e) => { e.stopPropagation(); removeMusicSchedule(schedule.id) }}>
                                Usuń
                              </Button>
                            </>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                    {musicSchedules.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={3} align="center">
                          <Typography color="text.secondary">Brak playlist. Utwórz pierwszą playlistę powyżej.</Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>

            {/* Formularz dodawania/edycji playlisty - tylko nazwa - ukryj gdy edytujemy utwory */}
            {user?.role === 'admin' && !selectedMusicSchedule && (
              <Paper sx={{ p: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    {editingMusicSchedule ? 'Edycja playlisty' : 'Nowa playlista'}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {editingMusicSchedule && (
                      <Button 
                        variant="outlined" 
                        onClick={() => {
                          setEditingMusicSchedule(null)
                          setMusicName('')
                        }}
                      >
                        Anuluj
                      </Button>
                    )}
                    <Button 
                      variant="contained" 
                      onClick={editingMusicSchedule ? updateMusicSchedule : createMusicSchedule}
                      disabled={!musicName.trim()}
                    >
                      {editingMusicSchedule ? 'Zapisz zmiany' : 'Utwórz playlistę'}
                    </Button>
                  </Box>
                </Box>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Nazwa playlisty"
                      value={musicName}
                      onChange={(e) => setMusicName(e.target.value)}
                      placeholder="np. Muzyka relaksacyjna, Hity 2024"
                      required
                    />
                  </Grid>
                </Grid>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  Utwory dodasz po utworzeniu playlisty. Przypisanie kiedy/gdzie playlista będzie grana zrobisz w harmonogramie przerw.
                </Typography>
              </Paper>
            )}

            {/* Tracks section */}
            {user?.role === 'admin' && selectedMusicSchedule && (
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="h6">
                    Utwory playlisty: {musicSchedules.find(s => s.id === Number(selectedMusicSchedule))?.name}
                  </Typography>
                  <Button 
                    variant="contained" 
                    color="success"
                    onClick={() => setSelectedMusicSchedule('')}
                  >
                    Zakończ
                  </Button>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Tylko podstawowe akcje: dodaj plik WAV/MP3, usuń plik, kolejność listy.
                </Typography>

                {/* Formularz dodawania utworu z dropdown */}
                <Grid container spacing={1} sx={{ mb: 2 }} alignItems="center">
                  <Grid item xs={12} md={2}>
                    <TextField
                      fullWidth
                      size="small"
                      select
                      label="Źródło"
                      value={musicTrackSourceType}
                      onChange={(e) => setMusicTrackSourceType(e.target.value as 'sound' | 'placeholder')}
                    >
                      <MenuItem value="sound">Dźwięk</MenuItem>
                      <MenuItem value="placeholder">Placeholder</MenuItem>
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      size="small"
                      select
                      label={musicTrackSourceType === 'sound' ? 'Wybierz dźwięk' : 'Wybierz placeholder'}
                      value={musicTrackSourceType === 'sound' ? musicTrackSoundId : musicTrackPlaceholderKey}
                      onChange={(e) => {
                        if (musicTrackSourceType === 'sound') {
                          setMusicTrackSoundId(e.target.value)
                        } else {
                          setMusicTrackPlaceholderKey(e.target.value)
                        }
                      }}
                    >
                      <MenuItem value="">-- Wybierz --</MenuItem>
                      {musicTrackSourceType === 'sound' && sounds.map((sound) => (
                        <MenuItem key={sound.id} value={String(sound.id)}>
                          {sound.name} ({sound.file_path?.split('/').pop()})
                        </MenuItem>
                      ))}
                      {musicTrackSourceType === 'placeholder' && placeholderKeys.map((key) => (
                        <MenuItem key={key} value={key}>
                          {placeholderLabels[key]} ({key})
                        </MenuItem>
                      ))}
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Tytuł (opcjonalnie)"
                      value={musicTrackTitle}
                      onChange={(e) => setMusicTrackTitle(e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={6} md={2}>
                    <TextField
                      fullWidth
                      size="small"
                      type="number"
                      label="Kolejność"
                      value={musicTrackOrder}
                      onChange={(e) => setMusicTrackOrder(e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={6} md={2}>
                    <Button
                      fullWidth
                      variant="contained"
                      sx={{ height: 40 }}
                      onClick={addMusicTrack}
                      disabled={musicTrackSourceType === 'sound' ? !musicTrackSoundId : !musicTrackPlaceholderKey}
                    >
                      Dodaj
                    </Button>
                  </Grid>
                </Grid>

                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>#</TableCell>
                        <TableCell>Źródło</TableCell>
                        <TableCell>Resolved</TableCell>
                        <TableCell>Format</TableCell>
                        <TableCell>Akcje</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {(musicTracks[Number(selectedMusicSchedule)] || []).map((track, idx) => (
                        <TableRow key={track.id}>
                          <TableCell>{idx + 1}</TableCell>
                          <TableCell>{track.title || (track.placeholder_key ? (placeholderLabels[track.placeholder_key] || track.placeholder_key) : track.file_path)}</TableCell>
                          <TableCell>{track.resolved_name || track.resolved_file_path || '-'}</TableCell>
                          <TableCell>
                            <Chip size="small" label={(track.resolved_file_path || track.file_path)?.toLowerCase().endsWith('.mp3') ? 'MP3' : 'WAV'} />
                          </TableCell>
                          <TableCell>
                            <Button size="small" color="error" onClick={() => removeMusicTrack(track.id)}>Usuń</Button>
                          </TableCell>
                        </TableRow>
                      ))}
                      {(musicTracks[Number(selectedMusicSchedule)] || []).length === 0 && (
                        <TableRow>
                          <TableCell colSpan={5} align="center">
                            <Typography variant="body2" color="text.secondary">
                              Brak utworów w playliście
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            )}
          </Grid>
        </Grid>
      </TabPanel>

      {/* Tab 2: Typy dnia */}
      <TabPanel value={tabValue} index={1}>
        {/* Lista dni (harmonogramów) */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Lista typów dni (harmonogramów)</Typography>
            {user?.role === 'admin' && (
              <Button 
                variant="contained" 
                startIcon={<AddIcon />} 
                onClick={() => setShowNewDayForm(!showNewDayForm)}
              >
                {showNewDayForm ? 'Anuluj' : '+ Dodaj typ dnia'}
              </Button>
            )}
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Standardowe dni tygodnia + niestandardowe typy (np. Dzień egzaminu, Dzień sportowy).
          </Typography>
          
          {/* Formularz nowego typu dnia */}
          {user?.role === 'admin' && showNewDayForm && (
            <Card variant="outlined" sx={{ mb: 2, p: 2, bgcolor: '#fff8e1' }}>
              <Typography variant="subtitle1" sx={{ mb: 1 }}>Nowy typ dnia</Typography>
              <Grid container spacing={1} alignItems="center">
                <Grid item xs={12} md={4}>
                  <TextField 
                    fullWidth 
                    size="small"
                    label="Nazwa typu dnia" 
                    value={newDayTypeName} 
                    onChange={(e) => setNewDayTypeName(e.target.value)}
                    placeholder="np. Dzień egzaminu, Dzień sportowy"
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <TextField 
                    fullWidth 
                    size="small"
                    type="date" 
                    label="Data (opcj.)" 
                    InputLabelProps={{ shrink: true }}
                    value={overrideDay}
                    onChange={(e) => setOverrideDay(e.target.value)}
                    helperText="Puste = szablon"
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <TextField 
                    fullWidth 
                    size="small"
                    select
                    label="Dzwonki" 
                    value={overrideEnabled}
                    onChange={(e) => setOverrideEnabled(e.target.value as 'true' | 'false')}
                  >
                    <MenuItem value="true">Włączone</MenuItem>
                    <MenuItem value="false">Wyłączone</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={12} md={2}>
                  <Button 
                    fullWidth 
                    variant="contained" 
                    sx={{ height: 40 }}
                    onClick={async () => {
                      if (!newDayTypeName.trim()) return
                      // Utwórz typ dnia - z datą lub jako szablon (data = null)
                      await api.post('/bells/runtime/calendar-overrides', {
                        day: overrideDay || null,
                        bells_enabled: overrideEnabled === 'true',
                        reason: newDayTypeName.trim(),
                      })
                      setNewDayTypeName('')
                      setOverrideDay('')
                      setShowNewDayForm(false)
                      fetchAll()
                    }}
                    disabled={!newDayTypeName.trim()}
                  >
                    Utwórz
                  </Button>
                </Grid>
              </Grid>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Typ dnia bez daty = szablon do wykorzystania w kalendarzu. Z datą = konkretny wyjątek.
              </Typography>
            </Card>
          )}
          
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Nazwa dnia/typu</TableCell>
                  <TableCell>Liczba zdarzeń</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Akcje</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {/* Standardowe dni tygodnia */}
                {[1, 2, 3, 4, 5, 6, 7].map((day) => (
                  <TableRow 
                    key={day} 
                    hover 
                    sx={{ cursor: 'pointer' }}
                    onClick={() => setSelectedDaySchedule(selectedDaySchedule === day ? null : day)}
                  >
                    <TableCell><Typography fontWeight={600}>{dayLabels[day]}</Typography></TableCell>
                    <TableCell>
                      <Chip size="small" label={`${bellsByDay[day]?.length || 0} zdarzeń`} />
                    </TableCell>
                    <TableCell>
                      <Chip size="small" color="success" label="Aktywny" />
                    </TableCell>
                    <TableCell>
                      {user?.role === 'admin' && (
                        <Button size="small" onClick={(e) => { e.stopPropagation(); setSelectedDaySchedule(day) }}>
                          Edytuj zdarzenia
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {/* Niestandardowe typy dnia - wszystkie wyjątki */}
                {calendarOverrides.map((override) => {
                  const customDayId = 100 + override.id
                  return (
                  <TableRow 
                    key={`override-${override.id}`} 
                    hover 
                    sx={{ cursor: 'pointer', bgcolor: '#fff8e1' }}
                    onClick={() => setSelectedDaySchedule(selectedDaySchedule === customDayId ? null : customDayId)}
                  >
                    <TableCell>
                      <Typography fontWeight={600}>
                        {override.reason || 'Dzień wyjątkowy'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {override.day}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip size="small" label={`${bellsByDay[customDayId]?.length || 0} zdarzeń`} />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        size="small" 
                        color={override.bells_enabled ? 'success' : 'warning'} 
                        label={override.bells_enabled ? 'Dzwonki ON' : 'Dzwonki OFF'} 
                      />
                    </TableCell>
                    <TableCell>
                      {user?.role === 'admin' && (
                        <>
                          <Button 
                            size="small" 
                            onClick={(e) => { e.stopPropagation(); setSelectedDaySchedule(customDayId) }}
                          >
                            Edytuj zdarzenia
                          </Button>
                          <Button 
                            size="small" 
                            onClick={(e) => {
                              e.stopPropagation()
                              setOverrideDay(override.day)
                              setOverrideEnabled(override.bells_enabled ? 'true' : 'false')
                              setNewDayTypeName(override.reason || '')
                              setShowNewDayForm(true)
                            }}
                          >
                            Edytuj
                          </Button>
                          <Button size="small" color="error" onClick={(e) => { e.stopPropagation(); removeDayOverride(override.id) }}>
                            Usuń
                          </Button>
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </TableContainer>

          
        </Paper>

        {/* Zdarzenia wybranego harmonogramu - tylko gdy wybrano dzień */}
        {selectedDaySchedule && (
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6">
                Zdarzenia: {selectedDaySchedule <= 7 
                  ? dayLabels[selectedDaySchedule] 
                  : calendarOverrides.find(o => 100 + o.id === selectedDaySchedule)?.reason || 'Dzień wyjątkowy'}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {user?.role === 'admin' && (
                  <Button variant="outlined" startIcon={<AddIcon />} onClick={handleOpenCreate}>
                    Dodaj zdarzenie
                  </Button>
                )}
                <Button 
                  variant="contained" 
                  color="success"
                  onClick={() => setSelectedDaySchedule(null)}
                >
                  Zakończ
                </Button>
              </Box>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Lista zdarzeń dla wybranego dnia. Godzina, nazwa, dzwonek, głośność.
            </Typography>
            
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Godzina</TableCell>
                    <TableCell>Nazwa</TableCell>
                    <TableCell>Dzwonek</TableCell>
                    <TableCell>Głośność</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Akcje</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {bellsByDay[selectedDaySchedule]?.map((bell) => {
                    const playlist = musicSchedules.find(s => s.id === bell.playlist_id)
                    return (
                      <TableRow key={bell.id} hover>
                        <TableCell><Typography fontWeight={600}>{bell.bell_time?.slice(0, 5)}</Typography></TableCell>
                        <TableCell>{bell.name}</TableCell>
                        <TableCell>
                          <Typography variant="body2" noWrap maxWidth={150}>
                            {playlist ? playlist.name : (bell.sound_file_path?.split('/').pop() || 'Brak')}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <LinearProgress 
                              variant="determinate" 
                              value={Math.max(0, Math.min(100, bell.volume || 0))} 
                              sx={{ width: 60, height: 6, borderRadius: 2 }} 
                            />
                            <Typography variant="body2">{bell.volume}%</Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip size="small" label={bell.active ? 'Aktywny' : 'Nieaktywny'} color={bell.active ? 'success' : 'default'} />
                        </TableCell>
                        <TableCell>
                          {user?.role === 'admin' && (
                            <>
                              <IconButton size="small" onClick={() => handleOpenEdit(bell)}><EditIcon /></IconButton>
                              <IconButton size="small" color="error" onClick={() => handleDelete(bell.id)}><DeleteIcon /></IconButton>
                            </>
                          )}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                  {(!bellsByDay[selectedDaySchedule] || bellsByDay[selectedDaySchedule].length === 0) && (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        <Typography color="text.secondary">Brak zdarzeń dla tego dnia. Kliknij "Dodaj zdarzenie".</Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        )}
      </TabPanel>

      {/* Tab 3: Kalendarz miesiąca */}
      <TabPanel value={tabValue} index={2}>
        <Paper sx={{ p: 2, mb: 2 }}>
          <Alert severity="info">
            Nie ma osobnego przypisania harmonogramu do dnia tygodnia. Dzień tygodnia wynika bezpośrednio
            z pól `days_of_week` w zdarzeniach dzwonków oraz z wyjątków datowych.
          </Alert>
        </Paper>

        {/* Profile miesięczne dzwonków */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6">Profile miesięczne dzwonków</Typography>
              <Typography variant="body2" color="text.secondary">
                Profil miesięczny określa, jaki dzwonek jest przypisany do każdego zdarzenia w danym miesiącu.
              </Typography>
            </Box>
          </Box>
          
          {user?.role === 'admin' && (
            <Card variant="outlined" sx={{ mb: 2, p: 2 }}>
              <Grid container spacing={1}>
                <Grid item xs={12} md={4}>
                  <TextField fullWidth label="Nazwa profilu" value={newProfileName} onChange={(e) => setNewProfileName(e.target.value)} />
                </Grid>
                <Grid item xs={12} md={2}>
                  <TextField fullWidth select label="Miesiąc (opcj.)" value={newProfileMonth} onChange={(e) => setNewProfileMonth(e.target.value)}>
                    <MenuItem value="">Brak</MenuItem>
                    {Object.entries(monthLabels).map(([num, name]) => (
                      <MenuItem key={num} value={num}>{name}</MenuItem>
                    ))}
                  </TextField>
                </Grid>
                <Grid item xs={12} md={3}>
                  <TextField fullWidth select label="Domyślny" value={newProfileDefault} onChange={(e) => setNewProfileDefault(e.target.value as 'true' | 'false')}>
                    <MenuItem value="false">Nie</MenuItem>
                    <MenuItem value="true">Tak</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Button fullWidth variant="contained" sx={{ height: 56 }} onClick={createProfile}>Dodaj profil</Button>
                </Grid>
              </Grid>
            </Card>
          )}

          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Miesiąc</TableCell>
                  <TableCell>Profil dzwonków</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Akcje</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {profiles.map((profile) => (
                  <TableRow key={profile.id} hover>
                    <TableCell>
                      {editingProfileId === profile.id ? (
                        <TextField
                          fullWidth
                          size="small"
                          select
                          value={editingProfileMonth}
                          onChange={(e) => setEditingProfileMonth(e.target.value)}
                        >
                          <MenuItem value="">Brak</MenuItem>
                          {Object.entries(monthLabels).map(([num, name]) => (
                            <MenuItem key={num} value={num}>{name}</MenuItem>
                          ))}
                        </TextField>
                      ) : (
                        profile.month ? monthLabels[profile.month] : '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {editingProfileId === profile.id ? (
                        <TextField
                          fullWidth
                          size="small"
                          value={editingProfileName}
                          onChange={(e) => setEditingProfileName(e.target.value)}
                        />
                      ) : (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography fontWeight={600}>{profile.name}</Typography>
                          {profile.is_default && <Chip size="small" color="secondary" label="Domyślny" />}
                        </Box>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip size="small" color={profile.is_active ? 'success' : 'default'} label={profile.is_active ? 'Aktywny' : 'Nieaktywny'} />
                    </TableCell>
                    <TableCell>
                      {user?.role === 'admin' && (
                        <>
                          {editingProfileId === profile.id ? (
                            <>
                              <Button size="small" onClick={saveProfileEdit}>Zapisz</Button>
                              <Button size="small" onClick={cancelEditProfile}>Anuluj</Button>
                            </>
                          ) : (
                            <>
                              <Button size="small" onClick={() => startEditProfile(profile)}>Edytuj</Button>
                              <Button size="small" onClick={() => setDefaultProfile(profile.id)}>Ustaw domyślny</Button>
                              <Button size="small" onClick={() => setProfileActive(profile.id, !profile.is_active)}>
                                {profile.is_active ? 'Dezaktywuj' : 'Aktywuj'}
                              </Button>
                              <Button size="small" color="error" onClick={() => deleteProfile(profile.id)}>Usuń</Button>
                            </>
                          )}
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {profiles.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      <Typography color="text.secondary">Brak profili. Dodaj pierwszy profil miesięczny.</Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          <Card variant="outlined" sx={{ mt: 2, p: 2, bgcolor: '#f7faff' }}>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>Mapowanie placeholderów</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Dla każdego profilu przypisz dźwięk, który ma wejść w miejsce placeholdera playlisty.
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Profil</TableCell>
                  {placeholderKeys.map((key) => (
                    <TableCell key={key}>{placeholderLabels[key]}</TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {profiles.map((profile) => {
                  const mappings = profilePlaceholderMap[profile.id] || []
                  const byKey = Object.fromEntries(mappings.map((m) => [m.placeholder_key, m.sound_id]))
                  return (
                    <TableRow key={profile.id} hover>
                      <TableCell>
                        <Typography fontWeight={600}>{profile.name}</Typography>
                      </TableCell>
                      {placeholderKeys.map((key) => (
                        <TableCell key={`${profile.id}-${key}`}>
                          <TextField
                            fullWidth
                            size="small"
                            select
                            value={byKey[key] ? String(byKey[key]) : ''}
                            onChange={async (e) => {
                              if (!e.target.value) return
                              await setProfilePlaceholder(profile.id, key, Number(e.target.value))
                            }}
                            disabled={user?.role !== 'admin'}
                          >
                            <MenuItem value="">-- brak --</MenuItem>
                            {sounds.map((sound) => (
                              <MenuItem key={sound.id} value={String(sound.id)}>
                                {sound.name}
                              </MenuItem>
                            ))}
                          </TextField>
                        </TableCell>
                      ))}
                    </TableRow>
                  )
                })}
                {profiles.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={1 + placeholderKeys.length} align="center">
                      <Typography color="text.secondary">Brak profili do mapowania placeholderów.</Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Card>
        </Paper>

        {/* Wyjątki datowe */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Wyjątki datowe (CRUD)</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Wyjątek nadpisuje mapowanie tygodniowe dla konkretnej daty.
          </Typography>
          
          {user?.role === 'admin' && (
            <Card variant="outlined" sx={{ mb: 2, p: 2 }}>
              <Grid container spacing={1}>
                <Grid item xs={12} md={3}>
                  <TextField fullWidth type="date" label="Data" InputLabelProps={{ shrink: true }} value={overrideDay} onChange={(e) => setOverrideDay(e.target.value)} />
                </Grid>
                <Grid item xs={12} md={3}>
                  <TextField fullWidth select label="Dzwonki" value={overrideEnabled} onChange={(e) => setOverrideEnabled(e.target.value as 'true' | 'false')}>
                    <MenuItem value="false">Wyłączone</MenuItem>
                    <MenuItem value="true">Włączone</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField fullWidth label="Powód" value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)} />
                </Grid>
                <Grid item xs={12} md={2}>
                  <Button fullWidth variant="contained" sx={{ height: 56 }} onClick={saveDayOverride}>Zapisz</Button>
                </Grid>
              </Grid>
            </Card>
          )}

          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Data</TableCell>
                  <TableCell>Harmonogram</TableCell>
                  <TableCell>Dzwonki OFF</TableCell>
                  <TableCell>Akcje</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {calendarOverrides.map((entry) => (
                  <TableRow key={entry.id} hover>
                    <TableCell><Typography fontWeight={600}>{entry.day}</Typography></TableCell>
                    <TableCell>{entry.bells_enabled ? 'Normalny' : 'OFF'}</TableCell>
                    <TableCell>
                      <Chip size="small" color={entry.bells_enabled ? 'success' : 'error'} label={entry.bells_enabled ? 'Nie' : 'Tak'} />
                    </TableCell>
                    <TableCell>
                      {user?.role === 'admin' && (
                        <>
                          <Button size="small">Edytuj</Button>
                          <Button size="small" color="error" onClick={() => removeDayOverride(entry.id)}>Usuń</Button>
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {calendarOverrides.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      <Typography color="text.secondary">Brak wyjątków datowych.</Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        {/* Nadpisania profilu */}
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Nadpisania profilu na daty (Święto / Apel / Egzamin)</Typography>
          
          {user?.role === 'admin' && (
            <Card variant="outlined" sx={{ mb: 2, p: 2 }}>
              <Grid container spacing={1}>
                <Grid item xs={12} md={3}>
                  <TextField fullWidth type="date" label="Data" InputLabelProps={{ shrink: true }} value={profileOverrideDay} onChange={(e) => setProfileOverrideDay(e.target.value)} />
                </Grid>
                <Grid item xs={12} md={3}>
                  <TextField fullWidth select label="Profil" value={profileOverrideProfileId} onChange={(e) => setProfileOverrideProfileId(e.target.value)}>
                    {profiles.map((p) => (
                      <MenuItem key={p.id} value={String(p.id)}>{p.name}</MenuItem>
                    ))}
                  </TextField>
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField fullWidth label="Powód" value={profileOverrideReason} onChange={(e) => setProfileOverrideReason(e.target.value)} />
                </Grid>
                <Grid item xs={12} md={2}>
                  <Button fullWidth variant="contained" sx={{ height: 56 }} onClick={saveProfileOverride}>Zapisz</Button>
                </Grid>
              </Grid>
            </Card>
          )}

          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Data</TableCell>
                  <TableCell>Profil</TableCell>
                  <TableCell>Powód</TableCell>
                  <TableCell>Akcje</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {profileOverrides.map((entry) => {
                  const profile = profiles.find((p) => p.id === entry.profile_id)
                  return (
                    <TableRow key={entry.id} hover>
                      <TableCell><Typography fontWeight={600}>{entry.day}</Typography></TableCell>
                      <TableCell>
                        <Chip size="small" label={profile ? profile.name : `Profil #${entry.profile_id}`} />
                      </TableCell>
                      <TableCell>{entry.reason || '-'}</TableCell>
                      <TableCell>
                        {user?.role === 'admin' && (
                          <Button size="small" color="error" onClick={() => removeProfileOverride(entry.id)}>Usuń</Button>
                        )}
                      </TableCell>
                    </TableRow>
                  )
                })}
                {profileOverrides.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      <Typography color="text.secondary">Brak nadpisań profilu.</Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </TabPanel>

      {/* Tab 4: Sterowanie teraz */}
      <TabPanel value={tabValue} index={3}>
        {/* Szybkie akcje runtime */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>Szybkie akcje runtime</Typography>
          
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} flexWrap="wrap">
            {user?.role === 'admin' && (
              <>
                <Button variant="outlined" startIcon={<PauseIcon />} onClick={() => pauseBells(10, 'Pauza 10 min')}>Pauza 10 min</Button>
                <Button variant="outlined" startIcon={<PauseIcon />} onClick={() => pauseBells(20, 'Pauza 20 min')}>Pauza 20 min</Button>
                <Button variant="outlined" startIcon={<PauseIcon />} onClick={() => pauseBells(45, 'Apel')}>Pauza 45 min</Button>
                <Button variant="outlined" color="success" startIcon={<PlayIcon />} onClick={resumeBells}>Wznów</Button>
                <Button variant="outlined" color="warning" startIcon={<StopIcon />} onClick={() => setBellsEnabled(false)}>Globalnie OFF</Button>
                <Button variant="outlined" color="primary" startIcon={<PlayIcon />} onClick={() => setBellsEnabled(true)}>Globalnie ON</Button>
              </>
            )}
          </Stack>
          
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Działa na scheduler, nie zmienia definicji harmonogramów.
          </Typography>
        </Paper>

        {/* Status bieżący */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>Status bieżący</Typography>
          
          <TableContainer>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell><Typography fontWeight={600}>Scheduler dzwonków</Typography></TableCell>
                  <TableCell>
                    <Chip 
                      size="small" 
                      color={runtimeStatus?.bells_enabled !== false ? 'success' : 'error'} 
                      label={runtimeStatus?.bells_enabled !== false ? 'AKTYWNY' : 'NIEAKTYWNY'} 
                    />
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><Typography fontWeight={600}>Aktywny harmonogram dnia</Typography></TableCell>
                  <TableCell>
                    {(() => {
                      const today = new Date().getDay()
                      const dayNum = today === 0 ? 7 : today
                      return dayLabels[dayNum]
                    })()}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><Typography fontWeight={600}>Aktywny profil miesięczny dzwonków</Typography></TableCell>
                  <TableCell>{activeProfile?.name || 'Domyślny'}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><Typography fontWeight={600}>Serwer audio</Typography></TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1}>
                      <Chip size="small" color={runtimeStatus?.server_playback_enabled ? 'success' : 'default'} label={runtimeStatus?.server_playback_enabled ? 'Serwer audio włączony' : 'Serwer audio wyłączony'} />
                      <Chip size="small" color={runtimeStatus?.client_playback_enabled ? 'success' : 'default'} label={runtimeStatus?.client_playback_enabled ? 'Klienci włączeni' : 'Klienci wyłączeni'} />
                    </Stack>
                  </TableCell>
                </TableRow>
                {runtimeStatus?.pause_until && (
                  <TableRow>
                    <TableCell><Typography fontWeight={600}>Pauza do</Typography></TableCell>
                    <TableCell>
                      <Chip size="small" color="warning" label={`Pauza do ${new Date(runtimeStatus.pause_until).toLocaleString()} (${runtimeStatus.pause_reason || 'bez powodu'})`} />
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        {/* Podgląd logiki */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>Podgląd logiki dzwonków</Typography>
          
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
            <TextField
              size="small"
              type="time"
              label="Podgląd HH:MM"
              InputLabelProps={{ shrink: true }}
              value={previewAt}
              onChange={(e) => setPreviewAt(e.target.value)}
              sx={{ minWidth: 150 }}
            />
            <Button variant="outlined" onClick={checkRuntimePreview} disabled={previewLoading}>
              {previewLoading ? 'Sprawdzanie...' : 'Sprawdź logikę'}
            </Button>
          </Stack>

          {runtimePreview && (
            <Alert severity={runtimePreview.runtime_blocked ? 'warning' : 'info'}>
              {`Podgląd ${runtimePreview.preview_time}: ${
                runtimePreview.runtime_blocked
                  ? 'dzwonki zablokowane'
                  : runtimePreview.bells.length > 0
                    ? `zadzwoni: ${runtimePreview.bells.map((b) => `${b.name} (${b.bell_time})`).join(', ')}`
                    : 'brak dzwonków do odtworzenia'
              }${runtimePreview.active_profile ? `, profil: ${runtimePreview.active_profile}` : ''}`}
            </Alert>
          )}
        </Paper>

        {/* Wynikowa lista zdarzeń na dziś */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Wynikowa lista zdarzeń na dziś</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Lista składana z: harmonogram dnia + profil miesięczny dzwonków + wyjątki datowe.
          </Typography>
          
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Godzina</TableCell>
                  <TableCell>Zdarzenie</TableCell>
                  <TableCell>Dzwonek</TableCell>
                  <TableCell>Zapowiedź</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {bells
                  .filter(b => b.active)
                  .sort((a, b) => a.bell_time.localeCompare(b.bell_time))
                  .map((bell) => {
                    const now = new Date()
                    const bellTime = new Date()
                    const [hours, minutes] = bell.bell_time.split(':')
                    bellTime.setHours(parseInt(hours), parseInt(minutes), 0)
                    const isPast = bellTime < now
                    const isNext = bells
                      .filter(b => b.active)
                      .sort((a, b) => a.bell_time.localeCompare(b.bell_time))
                      .find(b => {
                        const [h, m] = b.bell_time.split(':')
                        const bt = new Date()
                        bt.setHours(parseInt(h), parseInt(m), 0)
                        return bt > now
                      })?.id === bell.id
                    
                    return (
                      <TableRow key={bell.id} hover>
                        <TableCell><Typography fontWeight={600}>{bell.bell_time?.slice(0, 5)}</Typography></TableCell>
                        <TableCell>{bell.name}</TableCell>
                        <TableCell>{bell.sound_file_path?.split('/').pop() || '-'}</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>
                          <Chip 
                            size="small" 
                            color={isNext ? 'primary' : isPast ? 'default' : 'success'} 
                            label={isNext ? 'Następne' : isPast ? 'Wykonane' : 'Oczekuje'} 
                          />
                        </TableCell>
                      </TableRow>
                    )
                  })}
                {bells.filter(b => b.active).length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      <Typography color="text.secondary">Brak aktywnych dzwonków na dziś.</Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        {/* Podgląd składania dzwonka */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Podgląd składania dzwonka (debug)</Typography>
          
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Element</TableCell>
                  <TableCell>Źródło</TableCell>
                  <TableCell>Plik</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><Typography fontWeight={600}>Dzwonek</Typography></TableCell>
                  <TableCell>Profil miesięczny dzwonków</TableCell>
                  <TableCell>{activeProfile?.name || 'Domyślny'}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><Typography fontWeight={600}>Zapowiedź</Typography></TableCell>
                  <TableCell>Zdarzenie harmonogramu</TableCell>
                  <TableCell>-</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><Typography fontWeight={600}>Kolejność</Typography></TableCell>
                  <TableCell>Runtime</TableCell>
                  <TableCell>Dzwonek {'->'} Zapowiedź {'->'} Playlista (jeśli przerwa)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        {/* Emergency */}
        {user?.role === 'admin' && (
          <Paper sx={{ p: 2, bgcolor: '#fff5f5' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <WarningIcon color="error" />
              <Typography variant="h6" color="error">Emergency (awaryjne)</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Użyj, gdy odtwarzanie się zawiesi albo scheduler przestanie reagować.
            </Typography>
            
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
              <Button variant="contained" color="error" startIcon={<StopIcon />}>EMERGENCY STOP AUDIO</Button>
              <Button variant="outlined" color="warning" startIcon={<PauseIcon />}>EMERGENCY PAUSE 60 MIN</Button>
              <Button variant="outlined" color="error" startIcon={<RefreshIcon />}>RESTART SCHEDULER</Button>
              <Button variant="outlined" color="error">WYCZYŚĆ KOLEJKĘ</Button>
            </Stack>
          </Paper>
        )}
      </TabPanel>

      {/* Dialog for creating/editing bell - uproszczony formularz */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{editingBell ? 'Edycja zdarzenia' : 'Nowe zdarzenie'}</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Grid container spacing={2} sx={{ mt: 0 }}>
            <Grid item xs={12} md={6}>
              <TextField 
                fullWidth 
                label="Nazwa zdarzenia" 
                value={formData.name} 
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="np. Dzwonek na 1 lekcję"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField 
                fullWidth 
                type="time" 
                label="Godzina" 
                InputLabelProps={{ shrink: true }} 
                value={formData.bell_time} 
                onChange={(e) => setFormData({ ...formData, bell_time: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField 
                fullWidth 
                select 
                label="Typ zdarzenia" 
                value={formData.event_type} 
                onChange={(e) => setFormData({ ...formData, event_type: e.target.value })}
                helperText="PRZERWA = start playlisty, LEKCJA = stop playlisty"
              >
                <MenuItem value="lesson">Na lekcję (stop playlisty)</MenuItem>
                <MenuItem value="break">Na przerwę (start playlisty)</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField 
                fullWidth 
                select 
                label="Playlista (dźwięk)" 
                value={formData.playlist_id} 
                onChange={(e) => setFormData({ ...formData, playlist_id: e.target.value })}
                helperText={musicSchedules.length ? `${musicSchedules.length} playlist dostępnych` : 'Brak playlist - utwórz w zakładce Playlisty'}
              >
                <MenuItem value="">-- Brak (cisza) --</MenuItem>
                {musicSchedules.map((schedule) => (
                  <MenuItem key={schedule.id} value={String(schedule.id)}>
                    {schedule.name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField 
                fullWidth 
                type="number" 
                label="Głośność (0-100)" 
                value={formData.volume} 
                onChange={(e) => setFormData({ ...formData, volume: e.target.value })} 
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField 
                fullWidth 
                select 
                label="Grupa docelowa" 
                value={formData.group_id} 
                onChange={(e) => setFormData({ ...formData, group_id: e.target.value })}
                helperText={groups.length ? `Dostępne grupy: ${groups.map(g => g.name).join(', ')}` : 'Brak grup'}
              >
                <MenuItem value="">-- Wszystkie --</MenuItem>
                {groups.map((group) => (
                  <MenuItem key={group.id} value={String(group.id)}>
                    {group.name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField 
                fullWidth 
                select 
                label="Odtwarzaj na displayach" 
                value={formData.play_on_displays ? 'true' : 'false'} 
                onChange={(e) => setFormData({ ...formData, play_on_displays: e.target.value === 'true' })}
              >
                <MenuItem value="true">Tak</MenuItem>
                <MenuItem value="false">Nie (tylko serwer)</MenuItem>
              </TextField>
            </Grid>
            {editingBell && (
              <Grid item xs={12}>
                <TextField 
                  fullWidth 
                  select 
                  label="Aktywny" 
                  value={formData.active ? 'true' : 'false'} 
                  onChange={(e) => setFormData({ ...formData, active: e.target.value === 'true' })}
                >
                  <MenuItem value="true">Tak</MenuItem>
                  <MenuItem value="false">Nie</MenuItem>
                </TextField>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Anuluj</Button>
          <Button variant="contained" onClick={handleSubmit}>Zapisz</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default BellsPage





