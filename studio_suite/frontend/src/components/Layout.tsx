import { ReactNode } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  AppBar,
  Box,
  Chip,
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
  Inventory2,
  LocalOffer,
  Logout,
  Palette,
  People,
  PersonSearch,
  Speed,
  Summarize,
  ViewKanban,
} from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'
import { APP_VERSION } from '../version'
import { AppSection, canAccess } from '../config/permissions'

const drawerWidth = 280

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
  { label: 'Dashboard', path: '/dashboard', section: 'dashboard', icon: <Speed /> },
  { label: 'Kalendarz wizyt', path: '/calendar', section: 'calendar', icon: <CalendarMonth /> },
  { label: 'Kartoteka klientow', path: '/clients', section: 'clients', icon: <PersonSearch /> },
  { label: 'Salony i zasoby', path: '/resources', section: 'resources', icon: <Groups /> },
  { label: 'Cennik uslug', path: '/services', section: 'services', icon: <LocalOffer /> },
  { label: 'Pakiety (forfety)', path: '/bundles', section: 'bundles', icon: <ViewKanban /> },
  { label: 'Farby i kolory', path: '/colors', section: 'colors', icon: <Palette /> },
  { label: 'Magazyn', path: '/inventory/stock-levels', section: 'inventory', icon: <Inventory2 /> },
  { label: 'Raporty', path: '/reports', section: 'reports', icon: <Summarize /> },
  { label: 'Uzytkownicy i role', path: '/users', section: 'users', icon: <People /> },
]

const Layout = ({ children }: LayoutProps) => {
  const { user, logout } = useAuth()
  const { salons: allSalons } = useBooking()
  const navigate = useNavigate()
  const location = useLocation()

  const visible = navItems.filter((item) => canAccess(user, item.section))
  const salons = allSalons.filter((salon) => user?.assigned_salon_ids?.includes(salon.id))
  const showSalonChips = user?.role !== 'receptionist'

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Booking Studio Suite
          </Typography>
          <Chip label={user?.role} size="small" sx={{ mr: 1, textTransform: 'uppercase' }} />
          <Chip
            label={APP_VERSION}
            size="small"
            sx={{
              mr: 2,
              bgcolor: '#ffeb3b',
              color: '#1a1a1a',
              fontWeight: 700,
              border: '1px solid #e0c700',
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
          '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        <Toolbar />
        <Box sx={{ p: 2, borderBottom: '1px solid #e5e7eb' }}>
          <Typography variant="overline">Zalogowany</Typography>
          <Typography variant="body1" sx={{ fontWeight: 700 }}>{user?.full_name}</Typography>
          <Typography variant="caption" color="text.secondary">{user?.username}</Typography>
          {showSalonChips && (
            <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {salons.map((salon) => (
                <Chip key={salon.id} size="small" label={salon.name} />
              ))}
            </Box>
          )}
        </Box>
        <List>
          {visible.map((item) => (
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
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3, bgcolor: 'background.default' }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  )
}

export default Layout
