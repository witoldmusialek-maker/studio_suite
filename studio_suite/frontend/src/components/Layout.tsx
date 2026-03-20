import { ReactNode, useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  AppBar,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from '@mui/material'
import {
  CalendarMonth,
  Groups,
  Business,
  Inventory2,
  LocalOffer,
  Logout,
  Palette,
  People,
  PersonSearch,
  Speed,
  Summarize,
  HelpOutline,
  ViewKanban,
} from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'
import { APP_VERSION } from '../version'
import { AppSection, canAccess } from '../config/permissions'
import { getBranding } from '../config/branding'

const drawerWidth = 280
const PENDING_POLL_MS = 30_000
const PENDING_SEEN_KEY_PREFIX = 'studio_suite.pending_seen_ids'

interface LayoutProps {
  children: ReactNode
}

type NavItem = {
  label: string
  path: string
  section: AppSection
  icon: ReactNode
}

const navItems: NavItem[] = [
  { label: 'Tenanty', path: '/tenants', section: 'tenants', icon: <Business /> },
  { label: 'Dashboard', path: '/dashboard', section: 'dashboard', icon: <Speed /> },
  { label: 'Kalendarz wizyt', path: '/calendar', section: 'calendar', icon: <CalendarMonth /> },
  { label: 'Cennik uslug', path: '/services', section: 'services', icon: <LocalOffer /> },
  { label: 'Pakiety (forfety)', path: '/bundles', section: 'bundles', icon: <ViewKanban /> },
  { label: 'Kartoteka klientow', path: '/clients', section: 'clients', icon: <PersonSearch /> },
  { label: 'Farby i kolory', path: '/colors', section: 'colors', icon: <Palette /> },
  { label: 'Magazyn', path: '/inventory/stock-levels', section: 'inventory', icon: <Inventory2 /> },
  { label: 'Raporty', path: '/reports', section: 'reports', icon: <Summarize /> },
  { label: 'Pomoc', path: '/help', section: 'help', icon: <HelpOutline /> },
  { label: 'Salony i zasoby', path: '/resources', section: 'resources', icon: <Groups /> },
  { label: 'Uzytkownicy i role', path: '/users', section: 'users', icon: <People /> },
]

const SALON_ORDER_CODES = ['05', '12', '02', '07'] as const

const getSalonOrderRank = (salon: { code?: string | null; name: string }) => {
  const code = (salon.code || '').trim()
  const idx = SALON_ORDER_CODES.indexOf(code as (typeof SALON_ORDER_CODES)[number])
  if (idx >= 0) return idx
  const normalized = salon.name.toLowerCase()
  if (normalized.includes('pulaw')) return 0
  if (normalized.includes('kras')) return 1
  if (normalized.includes('odyn')) return 2
  return 99
}

const sortSalonsPreferred = <T extends { code?: string | null; name: string }>(rows: T[]) =>
  [...rows].sort((left, right) => {
    const rankDiff = getSalonOrderRank(left) - getSalonOrderRank(right)
    if (rankDiff !== 0) return rankDiff
    return left.name.localeCompare(right.name, 'pl')
  })

const Layout = ({ children }: LayoutProps) => {
  const { user, logout } = useAuth()
  const { salons: allSalons, appointments, reload } = useBooking()
  const navigate = useNavigate()
  const location = useLocation()
  const [pendingPopupOpen, setPendingPopupOpen] = useState(false)
  const [pendingPopupCount, setPendingPopupCount] = useState(0)

  const visible = navItems.filter((item) => canAccess(user, item.section))
  const helpItem = visible.find((item) => item.section === 'help')
  const topItems = visible.filter((item) => item.section !== 'help')
  const salons = sortSalonsPreferred(
    allSalons.filter((salon) => user?.assigned_salon_ids?.includes(salon.id)),
  )
  const showSalonChips = user?.role !== 'receptionist' && !user?.is_superadmin && salons.length > 1
  const primarySalon = salons[0]
  const userDisplayName = user?.full_name && user?.full_name !== user?.username ? user.full_name : user?.username
  const branding = getBranding(user)
  const canSeePendingPopup = !!user && !user.is_superadmin
  const pendingSeenKey = `${PENDING_SEEN_KEY_PREFIX}.${user?.id ?? 'anon'}`
  const pendingIds = useMemo(
    () => (appointments || []).filter((row) => (row.status || '').toLowerCase() === 'pending').map((row) => row.id),
    [appointments],
  )

  useEffect(() => {
    if (!user) return
    const timer = window.setInterval(() => {
      void reload().catch(() => undefined)
    }, PENDING_POLL_MS)
    return () => window.clearInterval(timer)
  }, [user, reload])

  useEffect(() => {
    if (!canSeePendingPopup || pendingIds.length === 0) return
    const raw = window.localStorage.getItem(pendingSeenKey) || ''
    const seen = new Set(
      raw
        .split(',')
        .map((item) => Number(item))
        .filter((item) => Number.isFinite(item) && item > 0),
    )
    const fresh = pendingIds.filter((id) => !seen.has(id))
    if (fresh.length === 0) return
    fresh.forEach((id) => seen.add(id))
    window.localStorage.setItem(pendingSeenKey, Array.from(seen).slice(-200).join(','))
    setPendingPopupCount(fresh.length)
    setPendingPopupOpen(true)
  }, [canSeePendingPopup, pendingIds, pendingSeenKey])

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          bgcolor: branding.appBarBg,
          color: branding.appBarText,
        }}
      >
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            {branding.appTitle}
          </Typography>
          <Chip label={user?.role} size="small" sx={{ mr: 1, textTransform: 'uppercase' }} />
          <Chip
            label={APP_VERSION}
            size="small"
            sx={{
              mr: 2,
              bgcolor: branding.appBarAccent,
              color: '#1a1a1a',
              fontWeight: 700,
              border: '1px solid rgba(0,0,0,0.2)',
            }}
          />
          <ListItemButton onClick={() => { logout(); navigate('/login') }} sx={{ width: 'auto' }}>
            <ListItemIcon sx={{ minWidth: 32, color: 'white' }}>
              <Logout />
            </ListItemIcon>
          </ListItemButton>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            bgcolor: branding.sidebarBg,
            borderRight: `1px solid ${branding.sidebarBorder}`,
            display: 'flex',
            flexDirection: 'column',
          },
        }}
      >
        <Toolbar />
        <Box sx={{ p: 2, borderBottom: `1px solid ${branding.sidebarBorder}` }}>
          <Typography variant="overline">{primarySalon ? 'Salon' : 'Konto'}</Typography>
          <Typography variant="body1" sx={{ fontWeight: 700 }}>
            {primarySalon?.name || userDisplayName}
          </Typography>
          <Typography variant="caption" color="text.secondary">{userDisplayName}</Typography>
          {showSalonChips && (
            <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {salons.map((salon) => (
                <Chip key={salon.id} size="small" label={salon.name} />
              ))}
            </Box>
          )}
        </Box>
        <List sx={{ flex: 1 }}>
          {topItems.map((item) => (
            <ListItem key={item.path} disablePadding>
              <ListItemButton
                selected={
                  location.pathname === item.path ||
                  location.pathname.startsWith(`${item.path}/`) ||
                  (item.path.startsWith('/inventory') && location.pathname.startsWith('/inventory/'))
                }
                onClick={() => navigate(item.path)}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
        {helpItem && (
          <List sx={{ borderTop: `1px solid ${branding.sidebarBorder}`, pb: 1 }}>
            <ListItem disablePadding>
              <ListItemButton
                selected={
                  location.pathname === helpItem.path ||
                  location.pathname.startsWith(`${helpItem.path}/`)
                }
                onClick={() => navigate(helpItem.path)}
              >
                <ListItemIcon>{helpItem.icon}</ListItemIcon>
                <ListItemText primary={helpItem.label} />
              </ListItemButton>
            </ListItem>
          </List>
        )}
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3, bgcolor: branding.pageBg }}>
        <Toolbar />
        {children}
      </Box>
      <Dialog open={pendingPopupOpen} onClose={() => setPendingPopupOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Nowa rezerwacja oczekujaca</DialogTitle>
        <DialogContent>
          <Typography>
            {pendingPopupCount === 1
              ? 'Pojawila sie 1 rezerwacja oczekujaca na potwierdzenie.'
              : `Pojawily sie ${pendingPopupCount} rezerwacje oczekujace na potwierdzenie.`}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPendingPopupOpen(false)}>Zamknij</Button>
          <Button
            variant="contained"
            onClick={() => {
              setPendingPopupOpen(false)
              navigate('/calendar')
            }}
          >
            Otworz kalendarz
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default Layout
