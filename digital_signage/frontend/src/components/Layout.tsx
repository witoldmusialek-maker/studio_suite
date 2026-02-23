import { ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Chip,
  Divider,
  List,
  ListSubheader,
  Typography,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  Tv as TvIcon,
  Folder as FolderIcon,
  Schedule as ScheduleIcon,
  GridView as GroupsIcon,
  Notifications as AlertsIcon,
  Assessment as ReportsIcon,
  MusicNote as BellsIcon,
  Logout as LogoutIcon,
  ManageAccounts as ManageAccountsIcon,
} from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'
import { APP_VERSION } from '../version'
import { FEATURE_FLAGS, FeatureKey } from '../config/features'

const drawerWidth = 240

interface LayoutProps {
  children: ReactNode
}

type MenuItemDef = {
  text: string
  icon: ReactNode
  path: string
  feature?: FeatureKey
  adminOnly?: boolean
}

type MenuSectionDef = {
  title: string
  feature?: FeatureKey
  items: MenuItemDef[]
}

const Layout = ({ children }: LayoutProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()

  const menuSections: MenuSectionDef[] = [
    {
      title: 'Start',
      items: [{ text: 'Dashboard', icon: <DashboardIcon />, path: '/' }],
    },
    {
      title: 'Monitoring',
      feature: 'monitoring',
      items: [
        { text: 'Status', icon: <TvIcon />, path: '/status' },
        { text: 'Alerty', icon: <AlertsIcon />, path: '/alerts', feature: 'alerts' },
        { text: 'Raporty', icon: <ReportsIcon />, path: '/reports', feature: 'reports' },
      ],
    },
    {
      title: 'Wyświetlacze',
      feature: 'displays',
      items: [
        { text: 'Wyświetlacze', icon: <TvIcon />, path: '/displays' },
        { text: 'Grupy wyświetlaczy', icon: <GroupsIcon />, path: '/groups' },
      ],
    },
    {
      title: 'Treści',
      feature: 'content',
      items: [
        { text: 'Harmonogramy treści', icon: <ScheduleIcon />, path: '/schedules' },
        { text: 'Biblioteka treści', icon: <FolderIcon />, path: '/content' },
        { text: 'Dzwonki: model i biblioteka', icon: <BellsIcon />, path: '/bells/model', feature: 'bells' },
      ],
    },
    {
      title: 'Administracja',
      items: [
        {
          text: 'Użytkownicy',
          icon: <ManageAccountsIcon />,
          path: '/admin/users',
          feature: 'adminUsers',
          adminOnly: true,
        },
      ],
    },
  ]

  const visibleSections = menuSections
    .filter((section) => !section.feature || FEATURE_FLAGS[section.feature])
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => {
        if (item.feature && !FEATURE_FLAGS[item.feature]) return false
        if (item.adminOnly && user?.role !== 'admin') return false
        return true
      }),
    }))
    .filter((section) => section.items.length > 0)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Digital Signage
          </Typography>
          <Chip
            size="small"
            label={APP_VERSION}
            sx={{
              mr: 2,
              fontWeight: 700,
              color: '#1a1a1a',
              bgcolor: '#ffd54f',
              border: '1px solid #fbc02d',
            }}
          />
          <Typography variant="body2" sx={{ mr: 2 }}>
            {user?.username} ({user?.role})
          </Typography>
          <ListItemButton onClick={handleLogout} sx={{ color: 'white' }}>
            <ListItemIcon sx={{ color: 'white' }}>
              <LogoutIcon />
            </ListItemIcon>
          </ListItemButton>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflowY: 'auto', height: 'calc(100vh - 64px)' }}>
          {visibleSections.map((section, sectionIndex) => (
            <List
              key={section.title}
              subheader={
                <ListSubheader component="div" sx={{ lineHeight: 1.8 }}>
                  {section.title}
                </ListSubheader>
              }
            >
              {section.items.map((item) => {
                const selected =
                  item.path === '/'
                    ? location.pathname === '/'
                    : location.pathname === item.path || location.pathname.startsWith(`${item.path}/`)

                return (
                  <ListItem key={item.text} disablePadding>
                    <ListItemButton selected={selected} onClick={() => navigate(item.path)}>
                      <ListItemIcon>{item.icon}</ListItemIcon>
                      <ListItemText primary={item.text} />
                    </ListItemButton>
                  </ListItem>
                )
              })}
              {sectionIndex < visibleSections.length - 1 && <Divider sx={{ mt: 1 }} />}
            </List>
          ))}
          <Box sx={{ px: 2, py: 1.5 }}>
            <Typography variant="caption" color="text.secondary">
              Wersja: {APP_VERSION}
            </Typography>
          </Box>
        </Box>
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: 'background.default',
          p: 3,
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  )
}

export default Layout

