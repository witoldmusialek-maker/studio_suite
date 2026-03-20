import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Container,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material'

import { api } from '../services/api'

type PublicSalon = { id: number; name: string }
type PublicBundle = { id: number; code: string; name: string; duration_minutes: number; price: number }
type PublicStaff = { id: number; display_name: string; public_bio?: string | null; public_photo_url?: string | null }
type PublicSlot = { staff_id: number; staff_name: string; start_at: string; end_at: string; duration_minutes: number }
type PublicOtpResponse = { otp_challenge_id: number; expires_in_seconds: number; masked_phone: string }

type PublicBootstrap = { salons: PublicSalon[]; services: unknown[]; bundles: PublicBundle[]; staff: PublicStaff[] }
type PublicCalendar = { salon_id: number; duration_minutes: number; slots: PublicSlot[] }

const CALENDAR_START_HOUR = 8
const CALENDAR_END_HOUR = 22
const CALENDAR_SLOT_MINUTES = 30
const CALENDAR_DAYS_AHEAD = 14

const pad2 = (value: number) => String(value).padStart(2, '0')
const toDateKey = (iso: string) => {
  const date = new Date(iso)
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`
}
const toTimeKey = (iso: string) => {
  const date = new Date(iso)
  return `${pad2(date.getHours())}:${pad2(date.getMinutes())}`
}
const todayKey = () => {
  const now = new Date()
  return `${now.getFullYear()}-${pad2(now.getMonth() + 1)}-${pad2(now.getDate())}`
}
const dateKeyWithOffset = (offset: number) => {
  const base = new Date()
  base.setHours(0, 0, 0, 0)
  base.setDate(base.getDate() + offset)
  return `${base.getFullYear()}-${pad2(base.getMonth() + 1)}-${pad2(base.getDate())}`
}
const preferredSalon = (rows: PublicSalon[]) => {
  const ordered = [...rows]
  ordered.sort((a, b) => {
    const aName = (a.name || '').toLowerCase()
    const bName = (b.name || '').toLowerCase()
    const rank = (name: string) => {
      if (name.includes('puław') || name.includes('pulaw')) return 0
      if (name.includes('krasi')) return 1
      if (name.includes('odyń') || name.includes('odyn')) return 2
      return 99
    }
    const diff = rank(aName) - rank(bName)
    if (diff !== 0) return diff
    return a.name.localeCompare(b.name, 'pl')
  })
  return ordered[0]?.id
}
const displayDatePl = (dateKey: string) => {
  const [y, m, d] = dateKey.split('-').map(Number)
  const date = new Date(y, (m || 1) - 1, d || 1)
  return date.toLocaleDateString('pl-PL', { weekday: 'long', day: '2-digit', month: '2-digit' })
}
const staffInitials = (name: string) =>
  (name || '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || '')
    .join('') || '?'

const TIME_ROWS = (() => {
  const rows: string[] = []
  let hour = CALENDAR_START_HOUR
  let minute = 0
  while (hour < CALENDAR_END_HOUR) {
    rows.push(`${pad2(hour)}:${pad2(minute)}`)
    minute += CALENDAR_SLOT_MINUTES
    if (minute >= 60) {
      minute -= 60
      hour += 1
    }
  }
  return rows
})()

const PublicBookingPage = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const [salons, setSalons] = useState<PublicSalon[]>([])
  const [bundles, setBundles] = useState<PublicBundle[]>([])
  const [staff, setStaff] = useState<PublicStaff[]>([])
  const [allSlots, setAllSlots] = useState<PublicSlot[]>([])
  const [bundleCompatibleSlots, setBundleCompatibleSlots] = useState<Set<string>>(new Set())

  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')
  const [selectedBundleId, setSelectedBundleId] = useState<number | ''>('')
  const [selectedStaffId, setSelectedStaffId] = useState<number | ''>('')
  const [selectedSlotKey, setSelectedSlotKey] = useState<string>('')
  const [dayOffset, setDayOffset] = useState(0)

  const [clientPhone, setClientPhone] = useState('')
  const [clientName, setClientName] = useState('')
  const [otpChallengeId, setOtpChallengeId] = useState<number | null>(null)
  const [otpCode, setOtpCode] = useState('')
  const [otpHint, setOtpHint] = useState('')
  const [otpLoading, setOtpLoading] = useState(false)
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const bundleSectionRef = useRef<HTMLDivElement | null>(null)

  const loadBootstrap = async (salonId?: number, staffId?: number) => {
    const res = await api.get<PublicBootstrap>('/public/bootstrap', {
      params: {
        ...(salonId ? { salon_id: salonId } : {}),
        ...(staffId ? { staff_id: staffId } : {}),
      },
    })
    const payload = res.data
    setSalons(payload.salons || [])
    setBundles(payload.bundles || [])
    setStaff(payload.staff || [])
    if (!salonId && payload.salons?.length && selectedSalonId === '') {
      setSelectedSalonId(preferredSalon(payload.salons) ?? payload.salons[0].id)
    }
  }

  const loadBaseCalendar = async (salonId: number) => {
    setLoadingSlots(true)
    try {
      const res = await api.get<PublicCalendar>('/public/calendar', {
        params: { salon_id: salonId, days: CALENDAR_DAYS_AHEAD, duration_minutes: CALENDAR_SLOT_MINUTES },
      })
      setAllSlots(res.data.slots || [])
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac wolnych terminow.')
      setAllSlots([])
    } finally {
      setLoadingSlots(false)
    }
  }

  useEffect(() => {
    void loadBootstrap().catch(() => setError('Nie udalo sie zaladowac formularza.'))
  }, [])

  useEffect(() => {
    if (selectedSalonId === '') return
    setError('')
    setSuccess('')
    setSelectedBundleId('')
    setSelectedStaffId('')
    setSelectedSlotKey('')
    setBundles([])
    setBundleCompatibleSlots(new Set())
    setOtpChallengeId(null)
    setOtpCode('')
    setOtpHint('')
    setDayOffset(0)
    void loadBootstrap(selectedSalonId).catch(() => setError('Nie udalo sie odswiezyc danych salonu.'))
    void loadBaseCalendar(selectedSalonId)
  }, [selectedSalonId])

  useEffect(() => {
    if (selectedSalonId === '' || selectedStaffId === '' || selectedBundleId === '') {
      setBundleCompatibleSlots(new Set())
      return
    }
    let cancelled = false
    const run = async () => {
      try {
        const res = await api.get<PublicCalendar>('/public/calendar', {
          params: {
            salon_id: selectedSalonId,
            staff_id: selectedStaffId,
            bundle_id: selectedBundleId,
            days: CALENDAR_DAYS_AHEAD,
          },
        })
        if (cancelled) return
        const next = new Set((res.data.slots || []).map((slot) => slot.start_at))
        setBundleCompatibleSlots(next)
        const currentSlotStart = selectedSlotKey.includes('|') ? selectedSlotKey.split('|')[1] : ''
        if (currentSlotStart && !next.has(currentSlotStart)) {
          setError('Wybrany termin nie pasuje do czasu trwania wybranej oferty. Wybierz inny slot.')
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(err?.response?.data?.detail || 'Nie udalo sie pobrac dostepnosci dla wybranej oferty.')
          setBundleCompatibleSlots(new Set())
        }
      }
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [selectedSalonId, selectedStaffId, selectedBundleId, selectedSlotKey])

  const currentDayKey = useMemo(() => dateKeyWithOffset(dayOffset), [dayOffset])
  const visibleSlots = useMemo(() => allSlots.filter((slot) => toDateKey(slot.start_at) === currentDayKey), [allSlots, currentDayKey])

  const slotByStaffAndTime = useMemo(() => {
    const map = new Map<string, PublicSlot>()
    for (const slot of visibleSlots) {
      map.set(`${slot.staff_id}|${toTimeKey(slot.start_at)}`, slot)
    }
    return map
  }, [visibleSlots])

  const slotsByStaff = useMemo(() => {
    const map = new Map<number, PublicSlot[]>()
    for (const slot of visibleSlots) {
      const list = map.get(slot.staff_id) || []
      list.push(slot)
      map.set(slot.staff_id, list)
    }
    for (const list of map.values()) {
      list.sort((a, b) => new Date(a.start_at).getTime() - new Date(b.start_at).getTime())
    }
    return map
  }, [visibleSlots])

  const selectedSlotStart = useMemo(
    () => (selectedSlotKey.includes('|') ? selectedSlotKey.split('|')[1] : ''),
    [selectedSlotKey],
  )
  const selectedSlotRow = useMemo(
    () => {
      if (!selectedSlotKey.includes('|')) return null
      const [staffIdRaw, startAt] = selectedSlotKey.split('|')
      const staffId = Number(staffIdRaw || 0)
      return allSlots.find((slot) => slot.staff_id === staffId && slot.start_at === startAt) || null
    },
    [allSlots, selectedSlotKey],
  )
  const selectedStaffProfile = useMemo(
    () => (selectedStaffId === '' ? null : staff.find((row) => row.id === selectedStaffId) || null),
    [selectedStaffId, staff],
  )

  const onSelectSlot = async (slot: PublicSlot) => {
    setSelectedSlotKey(`${slot.staff_id}|${slot.start_at}`)
    setSelectedStaffId(slot.staff_id)
    setSelectedBundleId('')
    setBundleCompatibleSlots(new Set())
    setOtpChallengeId(null)
    setOtpCode('')
    setOtpHint('')
    setError('')
    setBundles([])
    await loadBootstrap(selectedSalonId === '' ? undefined : selectedSalonId, slot.staff_id)
    if (bundleSectionRef.current) {
      setTimeout(() => {
        bundleSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }, 80)
    }
  }

  const requestOtp = async () => {
    if (selectedSalonId === '' || selectedStaffId === '' || selectedBundleId === '' || !selectedSlotStart || !clientPhone.trim()) {
      setError('Wybierz salon, termin, forfet i podaj telefon.')
      return
    }
    if (!bundleCompatibleSlots.has(selectedSlotStart)) {
      setError('Wybrany termin nie jest dostepny dla wybranej oferty.')
      return
    }
    setOtpLoading(true)
    setError('')
    setSuccess('')
    try {
      const res = await api.post<PublicOtpResponse>('/public/otp/request', {
        salon_id: selectedSalonId,
        bundle_id: selectedBundleId,
        staff_id: selectedStaffId,
        slot: selectedSlotStart,
        client_phone: clientPhone,
        client_name: clientName || undefined,
      })
      setOtpChallengeId(res.data.otp_challenge_id)
      setOtpHint(`Kod wysłano na ${res.data.masked_phone}. Ważny ${Math.max(Math.floor(res.data.expires_in_seconds / 60), 1)} min.`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udało się wysłać kodu OTP.')
    } finally {
      setOtpLoading(false)
    }
  }

  const submit = async () => {
    if (selectedSalonId === '' || selectedStaffId === '' || selectedBundleId === '' || !selectedSlotStart) {
      setError('Wybierz salon, termin i forfet.')
      return
    }
    if (!bundleCompatibleSlots.has(selectedSlotStart)) {
      setError('Wybrany termin nie jest dostepny dla wybranej oferty.')
      return
    }
    setError('')
    setSuccess('')
    try {
      const res = await api.post('/public/appointments', {
        salon_id: selectedSalonId,
        bundle_id: selectedBundleId,
        staff_id: selectedStaffId,
        slot: selectedSlotStart,
        client_phone: clientPhone,
        client_name: clientName || undefined,
        otp_challenge_id: otpChallengeId,
        otp_code: otpCode || undefined,
      })
      setSuccess(`Rezerwacja #${res.data.appointment_id} zapisana. Czeka na potwierdzenie recepcji.`)
      setSelectedBundleId('')
      setSelectedSlotKey('')
      setClientPhone('')
      setClientName('')
      setOtpChallengeId(null)
      setOtpCode('')
      setOtpHint('')
      await loadBootstrap(selectedSalonId, selectedStaffId)
      await loadBaseCalendar(selectedSalonId)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac rezerwacji.')
    }
  }

  const canBook = selectedSalonId !== '' && selectedStaffId !== '' && selectedBundleId !== '' && !!selectedSlotStart
  const showBundleAvailabilityWarning = selectedSlotStart && selectedBundleId !== '' && !bundleCompatibleSlots.has(selectedSlotStart)
  const isToday = currentDayKey === todayKey()

  return (
    <Box
      sx={{
        minHeight: '100vh',
        py: 4,
        backgroundColor: '#16181f',
        backgroundImage:
          'linear-gradient(90deg, rgba(12, 16, 28, 0.62) 0%, rgba(12, 16, 28, 0.42) 44%, rgba(12, 16, 28, 0.16) 100%), url("/booking-bg.jpg")',
        backgroundSize: 'cover',
        backgroundPosition: { xs: 'center top', md: 'center center' },
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: { xs: 'scroll', md: 'fixed' },
      }}
    >
      <Container maxWidth={false} sx={{ maxWidth: 1360 }}>
        <Stack spacing={2}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700, color: '#fff' }}>Rezerwacja online</Typography>
            <Typography sx={{ color: 'rgba(255,255,255,0.85)' }}>Wybierz salon, specjalistę, wolny termin i forfet.</Typography>
          </Box>

          {error && <Alert severity="error">{error}</Alert>}
          {success && <Alert severity="success">{success}</Alert>}
          {otpHint && <Alert severity="info">{otpHint}</Alert>}

          <Card
            sx={{
              maxWidth: { xs: '100%', md: 1120 },
              mr: { xs: 0, md: 'auto' },
              backgroundColor: 'rgba(255,255,255,0.9)',
              backdropFilter: 'blur(2px)',
              border: '1px solid rgba(255,255,255,0.35)',
            }}
          >
            <CardContent>
              <Stack spacing={2}>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ xs: 'stretch', md: 'center' }}>
                  <FormControl sx={{ minWidth: 320 }}>
                    <InputLabel>Salon</InputLabel>
                    <Select value={selectedSalonId} label="Salon" onChange={(e) => setSelectedSalonId(e.target.value === '' ? '' : Number(e.target.value))}>
                      {salons.map((salon) => <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>)}
                    </Select>
                  </FormControl>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Button variant="outlined" onClick={() => setDayOffset((prev) => Math.max(0, prev - 1))} disabled={dayOffset <= 0}>
                      Poprzedni dzien
                    </Button>
                    <Typography sx={{ minWidth: 230, textAlign: 'center', fontWeight: 600 }}>
                      {displayDatePl(currentDayKey)}
                    </Typography>
                    <Button variant="outlined" onClick={() => setDayOffset((prev) => Math.min(CALENDAR_DAYS_AHEAD - 1, prev + 1))} disabled={dayOffset >= CALENDAR_DAYS_AHEAD - 1}>
                      Nastepny dzien
                    </Button>
                    {!isToday && (
                      <Button variant="text" onClick={() => setDayOffset(0)}>Dzis</Button>
                    )}
                  </Stack>
                </Stack>

                <Typography variant="subtitle2" color="text.secondary">
                  Kalendarz dnia (wolne sloty co {CALENDAR_SLOT_MINUTES} min): wybierz godzinę u specjalisty.
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Dla bieżącego dnia godziny już minione są automatycznie niedostępne.
                </Typography>

                <Box sx={{ border: '1px solid #d1d5db', borderRadius: 2, overflow: 'auto' }}>
                  {loadingSlots && <Typography sx={{ p: 2 }} color="text.secondary">Ladowanie kalendarza...</Typography>}
                  {!loadingSlots && !isMobile && (
                    <Box sx={{ minWidth: 900 }}>
                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: `120px repeat(${Math.max(staff.length, 1)}, minmax(170px, 1fr))`,
                          borderBottom: '1px solid #e5e7eb',
                          bgcolor: '#f8fafc',
                        }}
                      >
                        <Box sx={{ p: 1, fontWeight: 600 }}>Godzina</Box>
                        {(staff.length ? staff : [{ id: 0, display_name: 'Brak specjalistow' }]).map((row) => (
                          <Box key={row.id} sx={{ p: 1, borderLeft: '1px solid #e5e7eb' }}>
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Avatar
                                src={row.public_photo_url || undefined}
                                alt={row.display_name}
                                sx={{ width: 28, height: 28, fontSize: 12 }}
                              >
                                {staffInitials(row.display_name)}
                              </Avatar>
                              <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{row.display_name}</Typography>
                            </Stack>
                          </Box>
                        ))}
                      </Box>
                      {TIME_ROWS.map((timeKey) => (
                        <Box
                          key={timeKey}
                          sx={{
                            display: 'grid',
                            gridTemplateColumns: `120px repeat(${Math.max(staff.length, 1)}, minmax(170px, 1fr))`,
                            borderBottom: '1px solid #f1f5f9',
                            minHeight: 46,
                          }}
                        >
                          <Box sx={{ p: 1, fontWeight: 500, color: 'text.secondary' }}>{timeKey}</Box>
                          {(staff.length ? staff : [{ id: 0, display_name: '-' }]).map((row) => {
                            const slot = slotByStaffAndTime.get(`${row.id}|${timeKey}`)
                            const isSelected = !!slot && selectedSlotKey === `${slot.staff_id}|${slot.start_at}`
                            const isCompatible = !slot || selectedBundleId === '' || bundleCompatibleSlots.has(slot.start_at)
                            return (
                              <Box key={`${row.id}-${timeKey}`} sx={{ p: 0.5, borderLeft: '1px solid #f1f5f9' }}>
                                {slot ? (
                                  <Button
                                    variant={isSelected ? 'contained' : 'outlined'}
                                    color={isCompatible ? 'primary' : 'warning'}
                                    fullWidth
                                    size="small"
                                    disabled={!isCompatible}
                                    onClick={() => onSelectSlot(slot)}
                                  >
                                    Wolny
                                  </Button>
                                ) : (
                                  <Box sx={{ height: 30, bgcolor: '#f8fafc', borderRadius: 1 }} />
                                )}
                              </Box>
                            )
                          })}
                        </Box>
                      ))}
                    </Box>
                  )}
                  {!loadingSlots && isMobile && (
                    <Stack spacing={1.25} sx={{ p: 1.25 }}>
                      {(staff.length ? staff : [{ id: 0, display_name: 'Brak specjalistow' }]).map((row) => {
                        const rowSlots = slotsByStaff.get(row.id) || []
                        return (
                          <Card key={row.id} variant="outlined">
                            <CardContent sx={{ p: 1.25 }}>
                              <Stack spacing={1}>
                                <Stack direction="row" spacing={1} alignItems="center">
                                  <Avatar
                                    src={row.public_photo_url || undefined}
                                    alt={row.display_name}
                                    sx={{ width: 30, height: 30, fontSize: 12 }}
                                  >
                                    {staffInitials(row.display_name)}
                                  </Avatar>
                                  <Box>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{row.display_name}</Typography>
                                    {!!row.public_bio && (
                                      <Typography variant="caption" color="text.secondary">
                                        {row.public_bio.length > 90 ? `${row.public_bio.slice(0, 90)}...` : row.public_bio}
                                      </Typography>
                                    )}
                                  </Box>
                                </Stack>
                                {rowSlots.length === 0 ? (
                                  <Typography variant="caption" color="text.secondary">Brak wolnych terminow w tym dniu.</Typography>
                                ) : (
                                  <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                                    {rowSlots.map((slot) => {
                                      const isSelected = selectedSlotKey === `${slot.staff_id}|${slot.start_at}`
                                      const isCompatible = selectedBundleId === '' || bundleCompatibleSlots.has(slot.start_at)
                                      return (
                                        <Button
                                          key={`${slot.staff_id}-${slot.start_at}`}
                                          size="small"
                                          variant={isSelected ? 'contained' : 'outlined'}
                                          color={isCompatible ? 'primary' : 'warning'}
                                          disabled={!isCompatible}
                                          onClick={() => onSelectSlot(slot)}
                                        >
                                          {toTimeKey(slot.start_at)}
                                        </Button>
                                      )
                                    })}
                                  </Stack>
                                )}
                              </Stack>
                            </CardContent>
                          </Card>
                        )
                      })}
                    </Stack>
                  )}
                </Box>

                {selectedSlotRow && (
                  <Alert severity="success">
                    Wybrany termin: {new Date(selectedSlotRow.start_at).toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })} - {selectedSlotRow.staff_name}
                  </Alert>
                )}
                {selectedStaffProfile && (
                  <Card variant="outlined">
                    <CardContent sx={{ p: 1.5 }}>
                      <Stack direction="row" spacing={1.25} alignItems="flex-start">
                        <Avatar
                          src={selectedStaffProfile.public_photo_url || undefined}
                          alt={selectedStaffProfile.display_name}
                          sx={{ width: 52, height: 52 }}
                        >
                          {staffInitials(selectedStaffProfile.display_name)}
                        </Avatar>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{selectedStaffProfile.display_name}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {selectedStaffProfile.public_bio || 'Specjalista salonu.'}
                          </Typography>
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>
                )}

                <Box ref={bundleSectionRef}>
                  <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.25}>
                    <FormControl fullWidth disabled={selectedStaffId === ''}>
                      <InputLabel>Forfet (tylko przypisane do specjalisty)</InputLabel>
                      <Select
                        value={selectedBundleId}
                        label="Forfet (tylko przypisane do specjalisty)"
                        onChange={(e) => {
                          setSelectedBundleId(e.target.value === '' ? '' : Number(e.target.value))
                          setOtpChallengeId(null)
                          setOtpCode('')
                          setOtpHint('')
                        }}
                      >
                        <MenuItem value="">Wybierz forfet</MenuItem>
                        {bundles.map((bundle) => (
                          <MenuItem key={bundle.id} value={bundle.id}>
                            {bundle.code} - {bundle.name} ({bundle.duration_minutes} min) • {Number(bundle.price || 0).toFixed(2)} PLN
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Stack>
                  {selectedStaffId === '' && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.75 }}>
                      Najpierw wybierz termin u specjalisty, wtedy pokażą się przypisane forfety.
                    </Typography>
                  )}
                </Box>

                {selectedBundleId !== '' && (
                  <Typography variant="body2" color="text.secondary">
                    Cena wybranego forfetu: {(bundles.find((row) => row.id === selectedBundleId)?.price ?? 0).toFixed(2)} PLN
                  </Typography>
                )}

                {showBundleAvailabilityWarning && (
                  <Alert severity="warning">Wybrany slot nie miesci czasu trwania wybranej oferty. Kliknij inny wolny termin.</Alert>
                )}

                <TextField label="Telefon" value={clientPhone} onChange={(e) => setClientPhone(e.target.value)} fullWidth required />
                <TextField label="Imie i nazwisko (opcjonalnie)" value={clientName} onChange={(e) => setClientName(e.target.value)} fullWidth />

                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
                  <Button variant="outlined" onClick={requestOtp} disabled={otpLoading || !canBook || !clientPhone.trim()}>
                    {otpLoading ? 'Wysyłanie OTP...' : 'Wyślij kod OTP'}
                  </Button>
                  <TextField
                    label="Kod OTP"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    sx={{ minWidth: 220 }}
                  />
                </Stack>

                <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="flex-end" spacing={2} alignItems={{ xs: 'stretch', sm: 'center' }}>
                  <Button variant="contained" onClick={submit} disabled={!canBook || !clientPhone.trim() || !otpChallengeId || !otpCode.trim()}>
                    Zarezerwuj
                  </Button>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      </Container>
    </Box>
  )
}

export default PublicBookingPage
