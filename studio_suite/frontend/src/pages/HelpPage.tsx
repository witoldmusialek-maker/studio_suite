import { useEffect, useMemo, useState } from 'react'
import { Alert, Box, Card, CardContent, Chip, Link, Stack, Typography, Button, Divider, FormControl, InputLabel, MenuItem, Select, Table, TableBody, TableCell, TableHead, TableRow, TextField } from '@mui/material'
import { useAuth } from '../contexts/AuthContext'
import { APP_VERSION } from '../version'
import receptionistHelp from '../help/help_receptionist.md?raw'
import managerSalonHelp from '../help/help_manager_salon.md?raw'
import managerMainHelp from '../help/help_manager_main.md?raw'
import { api } from '../services/api'

type HelpSection = { id: string; title: string; body: string }

const toAnchorId = (value: string) =>
  value
    .toLowerCase()
    .replace(/[ąćęłńóśżź]/g, (match) => ({ ą: 'a', ć: 'c', ę: 'e', ł: 'l', ń: 'n', ó: 'o', ś: 's', ż: 'z', ź: 'z' }[match] || match))
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')

const stripHeadingPrefix = (value: string) =>
  value
    .replace(/^\s*\d+\.\s*/, '')
    .replace(/^\s*#+\s*/, '')
    .trim()

const parseHelpSections = (raw: string): HelpSection[] => {
  const lines = raw.split('\n')
  const sections: HelpSection[] = []
  let currentTitle = ''
  let currentBody: string[] = []

  for (const line of lines) {
    if (line.startsWith('## ')) {
      if (currentTitle) {
        const cleanTitle = stripHeadingPrefix(currentTitle)
        sections.push({
          id: toAnchorId(cleanTitle),
          title: cleanTitle,
          body: currentBody
            .map((row) => row.replace(/^\s*###\s*/, '').replace(/^\s*####\s*/, '').trimEnd())
            .join('\n')
            .trim(),
        })
      }
      currentTitle = line.slice(3).trim()
      currentBody = []
      continue
    }
    if (line.startsWith('# ')) continue
    currentBody.push(line)
  }
  if (currentTitle) {
    const cleanTitle = stripHeadingPrefix(currentTitle)
    sections.push({
      id: toAnchorId(cleanTitle),
      title: cleanTitle,
      body: currentBody
        .map((row) => row.replace(/^\s*###\s*/, '').replace(/^\s*####\s*/, '').trimEnd())
        .join('\n')
        .trim(),
    })
  }
  return sections
}

const bodyStyle = {
  margin: 0,
  whiteSpace: 'pre-wrap' as const,
  wordBreak: 'break-word' as const,
  fontFamily: '"Segoe UI", "Trebuchet MS", "Roboto", "Helvetica", "Arial", sans-serif',
  fontSize: '0.95rem',
  lineHeight: 1.6,
}

const HelpPage = () => {
  const { user } = useAuth()
  const [activeSectionId, setActiveSectionId] = useState<string>('')
  const [apkReady, setApkReady] = useState<boolean>(false)
  const [apkChecked, setApkChecked] = useState<boolean>(false)
  const [salons, setSalons] = useState<Array<{ id: number; name: string }>>([])
  const [selectedSalonId, setSelectedSalonId] = useState<number>(0)
  const [pairCode, setPairCode] = useState<string>('')
  const [pairExpiresAt, setPairExpiresAt] = useState<string>('')
  const [pairingBusy, setPairingBusy] = useState<boolean>(false)
  const [smsDevices, setSmsDevices] = useState<Array<{ id: number; device_name: string; device_uuid: string; endpoint_url: string; app_version?: string; is_active: boolean; last_seen_at?: string; created_at: string }>>([])
  const [devicesBusy, setDevicesBusy] = useState<boolean>(false)
  const [smsFlash, setSmsFlash] = useState<string>('')
  const [smsTestPhone, setSmsTestPhone] = useState<string>('')
  const [smsTestMessage, setSmsTestMessage] = useState<string>('Test SMS z panelu parowania')
  const [smsTestBusy, setSmsTestBusy] = useState<boolean>(false)

  const role = user?.role || 'employee'
  const isMainManager = role === 'manager_main' || role === 'manager' || role === 'admin'
  const isSalonManager = role === 'manager_salon'
  const isReception = role === 'receptionist'

  let content = receptionistHelp
  let title = 'Help obsługi'
  if (isSalonManager) {
    title = 'Help managera salonu'
    content = managerSalonHelp
  } else if (isMainManager) {
    title = 'Help głównego managera'
    content = managerMainHelp
  } else if (isReception) {
    title = 'Help recepcjonisty'
    content = receptionistHelp
  }
  const sections = parseHelpSections(content)
  const sectionIds = useMemo(() => sections.map((row) => row.id), [sections])
  const publicBookingPath = '/public/client-booking'
  const publicBookingAbsolute = `${window.location.origin}${publicBookingPath}`
  const smsBridgeApkBasePath = '/downloads/sms-bridge-android12.apk'
  const smsBridgeApkPath = `${smsBridgeApkBasePath}?v=${encodeURIComponent(APP_VERSION)}&apk=20260314-1755`

  useEffect(() => {
    let canceled = false
    const checkApk = async () => {
      try {
        const response = await fetch(smsBridgeApkPath, { method: 'HEAD', cache: 'no-store' })
        const contentType = (response.headers.get('content-type') || '').toLowerCase()
        const looksLikeApk = response.ok && !contentType.includes('text/html')
        if (!canceled) setApkReady(looksLikeApk)
      } catch {
        if (!canceled) setApkReady(false)
      } finally {
        if (!canceled) setApkChecked(true)
      }
    }
    void checkApk()
    return () => {
      canceled = true
    }
  }, [])

  const loadSmsDevices = async (salonId: number) => {
    if (!salonId) return
    setDevicesBusy(true)
    try {
      const res = await api.get<Array<{ id: number; device_name: string; device_uuid: string; endpoint_url: string; app_version?: string; is_active: boolean; last_seen_at?: string; created_at: string }>>('/auth/sms-gateway/devices', { params: { salon_id: salonId } })
      setSmsDevices(res.data || [])
    } catch (err: any) {
      setSmsFlash(err?.response?.data?.detail || 'Nie udalo sie pobrac listy urzadzen SMS')
    } finally {
      setDevicesBusy(false)
    }
  }

  useEffect(() => {
    if (!isMainManager) return
    let active = true
    const load = async () => {
      try {
        const res = await api.get<Array<{ id: number; name: string }>>('/resources/salons')
        if (!active) return
        const rows = (res.data || []).map((row) => ({ id: row.id, name: row.name }))
        setSalons(rows)
        const firstId = rows[0]?.id || 0
        setSelectedSalonId(firstId)
        if (firstId) {
          await loadSmsDevices(firstId)
        }
      } catch (err: any) {
        if (!active) return
        setSmsFlash(err?.response?.data?.detail || 'Nie udalo sie pobrac salonow')
      }
    }
    void load()
    return () => {
      active = false
    }
  }, [isMainManager])

  useEffect(() => {
    if (!selectedSalonId || !isMainManager) return
    void loadSmsDevices(selectedSalonId)
  }, [selectedSalonId, isMainManager])

  const scrollToSection = (sectionId: string) => {
    const node = document.getElementById(sectionId)
    if (!node) return
    setActiveSectionId(sectionId)
    node.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <Box>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent='space-between' sx={{ mb: 2 }} spacing={1}>
        <Typography variant='h4'>Pomoc</Typography>
        <Stack direction='row' spacing={1}>
          <Chip label={title} color='primary' variant='outlined' />
          <Chip label={`Wersja: ${APP_VERSION}`} size='small' />
        </Stack>
      </Stack>

      <Card>
        <CardContent>
          <Typography variant='body2' color='text.secondary' sx={{ mb: 2 }}>
            Dokumentacja operacyjna. Po każdej zmianie workflow aplikacji należy zaktualizować treść pomocy.
          </Typography>
          {isMainManager && (
            <Box sx={{ mb: 3, p: 1.5, border: '1px solid #dbe3ee', borderRadius: 2, bgcolor: '#f8fbff' }}>
              <Typography variant='subtitle2' sx={{ mb: 0.5, fontWeight: 700 }}>
                Test samorezerwacji klienta
              </Typography>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                <Link href={publicBookingPath} underline='hover'>
                  Otworz rezerwacje klienta (lokalnie)
                </Link>
                <Link href={publicBookingAbsolute} target='_blank' rel='noreferrer' underline='hover'>
                  Otworz rezerwacje klienta (nowa karta)
                </Link>
              </Stack>
            </Box>
          )}
          {isMainManager && (
            <Box sx={{ mb: 3, p: 1.5, border: '1px solid #dbe3ee', borderRadius: 2, bgcolor: '#f8fbff' }}>
              <Typography variant='subtitle2' sx={{ mb: 0.5, fontWeight: 700 }}>
                Mostek SMS (Android 12)
              </Typography>
              <Typography variant='body2' color='text.secondary' sx={{ mb: 1.5 }}>
                Aplikacja odbiera zlecenia SMS przez Wi-Fi i wysyla wiadomosci przez telefon firmowy.
                Plik APK jest dystrybuowany lokalnie z tej aplikacji.
              </Typography>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mb: 1.5 }}>
                <Button
                  component='a'
                  href={smsBridgeApkPath}
                  download
                  variant='contained'
                  disabled={!apkReady}
                >
                  Pobierz APK (Android 12)
                </Button>
                <Link href={smsBridgeApkPath} target='_blank' rel='noreferrer' underline='hover'>
                  Otworz link bezposredni
                </Link>
              </Stack>
              {!apkChecked && <Alert severity='info'>Sprawdzanie dostepnosci APK...</Alert>}
              {apkChecked && !apkReady && (
                <Alert severity='warning'>
                  APK nie zostal jeszcze podmieniony pod sciezka <code>{smsBridgeApkBasePath}</code>.
                </Alert>
              )}
              {apkChecked && apkReady && <Alert severity='success'>APK jest gotowe do pobrania.</Alert>}
            </Box>
          )}
          {isMainManager && (
            <Box sx={{ mb: 3, p: 1.5, border: '1px solid #dbe3ee', borderRadius: 2, bgcolor: '#f8fbff' }}>
              <Typography variant='subtitle2' sx={{ mb: 1, fontWeight: 700 }}>
                Parowanie telefonu SMS
              </Typography>
              <Typography variant='body2' color='text.secondary' sx={{ mb: 1.5 }}>
                1) Wybierz salon i wygeneruj kod. 2) W aplikacji Android wpisz kod i zarejestruj urządzenie.
              </Typography>
              {smsFlash && <Alert severity='info' sx={{ mb: 1.5 }}>{smsFlash}</Alert>}
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mb: 1.5 }}>
                <FormControl size='small' sx={{ minWidth: 240 }}>
                  <InputLabel id='sms-salon-label'>Salon</InputLabel>
                  <Select
                    labelId='sms-salon-label'
                    label='Salon'
                    value={selectedSalonId}
                    onChange={(event) => setSelectedSalonId(Number(event.target.value) || 0)}
                  >
                    {salons.map((salon) => (
                      <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Button
                  variant='contained'
                  disabled={!selectedSalonId || pairingBusy}
                  onClick={async () => {
                    if (!selectedSalonId) return
                    setSmsFlash('')
                    setPairingBusy(true)
                    try {
                      const res = await api.post<{ code: string; expires_at: string }>('/auth/sms-gateway/pairing-codes', { salon_id: selectedSalonId, ttl_minutes: 10 })
                      setPairCode(res.data?.code || '')
                      setPairExpiresAt(res.data?.expires_at || '')
                      setSmsFlash('Kod parowania wygenerowany.')
                    } catch (err: any) {
                      setSmsFlash(err?.response?.data?.detail || 'Nie udalo sie wygenerowac kodu')
                    } finally {
                      setPairingBusy(false)
                    }
                  }}
                >
                  Generuj kod parowania
                </Button>
                <Button variant='outlined' disabled={!selectedSalonId || devicesBusy} onClick={() => void loadSmsDevices(selectedSalonId)}>
                  Odswiez urzadzenia
                </Button>
              </Stack>
              {!!pairCode && (
                <Alert severity='success' sx={{ mb: 1.5 }}>
                  Kod: <strong>{pairCode}</strong> (wazny do {pairExpiresAt ? new Date(pairExpiresAt).toLocaleString() : '-'})
                </Alert>
              )}
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mb: 1.5 }}>
                <TextField
                  size='small'
                  label='Numer testowy'
                  placeholder='+48...'
                  value={smsTestPhone}
                  onChange={(event) => setSmsTestPhone(event.target.value)}
                  sx={{ minWidth: 220 }}
                />
                <TextField
                  size='small'
                  label='Tresc SMS testowego'
                  value={smsTestMessage}
                  onChange={(event) => setSmsTestMessage(event.target.value)}
                  sx={{ minWidth: 320, flex: 1 }}
                />
                <Button
                  variant='outlined'
                  disabled={!selectedSalonId || !smsTestPhone.trim() || !smsTestMessage.trim() || smsTestBusy}
                  onClick={async () => {
                    if (!selectedSalonId || !smsTestPhone.trim() || !smsTestMessage.trim()) return
                    setSmsFlash('')
                    setSmsTestBusy(true)
                    try {
                      await api.post('/auth/sms-test', {
                        phone: smsTestPhone.trim(),
                        message: smsTestMessage.trim(),
                        salon_id: selectedSalonId,
                      })
                      setSmsFlash('SMS testowy wyslany.')
                    } catch (err: any) {
                      setSmsFlash(err?.response?.data?.detail || 'Nie udalo sie wyslac SMS testowego')
                    } finally {
                      setSmsTestBusy(false)
                    }
                  }}
                >
                  Wyslij test SMS
                </Button>
              </Stack>
              <Table size='small'>
                <TableHead>
                  <TableRow>
                    <TableCell>Urzadzenie</TableCell>
                    <TableCell>Endpoint</TableCell>
                    <TableCell>Ostatnie polaczenie</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align='right'>Akcje</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {smsDevices.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <Typography variant='body2' sx={{ fontWeight: 700 }}>{row.device_name}</Typography>
                        <Typography variant='caption' color='text.secondary'>{row.device_uuid}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant='caption' sx={{ wordBreak: 'break-all' }}>{row.endpoint_url}</Typography>
                      </TableCell>
                      <TableCell>{row.last_seen_at ? new Date(row.last_seen_at).toLocaleString() : '-'}</TableCell>
                      <TableCell>{row.is_active ? 'Aktywne' : 'Wylaczone'}</TableCell>
                      <TableCell align='right'>
                        <Button
                          size='small'
                          color='error'
                          disabled={!row.is_active}
                          onClick={async () => {
                            setSmsFlash('')
                            try {
                              await api.delete(`/auth/sms-gateway/devices/${row.id}`)
                              setSmsFlash('Urzadzenie zostalo wylaczone.')
                              if (selectedSalonId) {
                                await loadSmsDevices(selectedSalonId)
                              }
                            } catch (err: any) {
                              setSmsFlash(err?.response?.data?.detail || 'Nie udalo sie wylaczyc urzadzenia')
                            }
                          }}
                        >
                          Wylacz
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {!smsDevices.length && (
                    <TableRow>
                      <TableCell colSpan={5}>Brak urzadzen SMS dla wybranego salonu.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </Box>
          )}
          {!!sections.length && (
            <Stack spacing={2} sx={{ mb: 3 }}>
              <Typography variant='subtitle1' sx={{ fontWeight: 700 }}>Spis treści</Typography>
              <Card variant='outlined' sx={{ bgcolor: '#fbfdff' }}>
                <CardContent sx={{ py: 1.5 }}>
                  <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} sx={{ flexWrap: 'wrap' }}>
                    {sections.map((section, idx) => (
                      <Button
                        key={section.id}
                        size='small'
                        variant={activeSectionId === section.id ? 'contained' : 'outlined'}
                        onClick={() => scrollToSection(section.id)}
                        sx={{ justifyContent: 'flex-start', textAlign: 'left' }}
                      >
                        {idx + 1}. {section.title}
                      </Button>
                    ))}
                  </Stack>
                </CardContent>
              </Card>
            </Stack>
          )}
          <Stack spacing={2.5}>
            {sections.map((section, idx) => (
              <Card
                key={section.id}
                id={section.id}
                variant='outlined'
                sx={{ scrollMarginTop: 96, borderColor: activeSectionId === section.id ? '#90caf9' : '#e5e7eb' }}
              >
                <CardContent>
                  <Typography variant='h6' sx={{ mb: 1 }}>{idx + 1}. {section.title}</Typography>
                  <pre style={bodyStyle}>{section.body}</pre>
                  {idx < sectionIds.length - 1 && <Divider sx={{ mt: 2 }} />}
                </CardContent>
              </Card>
            ))}
            {!sections.length && (
              <Card variant='outlined'>
                <CardContent>
                  <pre style={bodyStyle}>{content}</pre>
                </CardContent>
              </Card>
            )}
          </Stack>
        </CardContent>
      </Card>
    </Box>
  )
}

export default HelpPage
