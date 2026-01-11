import { ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  Tv as TvIcon,
  Folder as FolderIcon,
  Schedule as ScheduleIcon,
  Groups as GroupsIcon,
  Notifications as NotificationsIcon,
  Assessment as AssessmentIcon,
  NotificationsActive as BellIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'

const drawerWidth = 240

interface LayoutProps {
  children: ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Status', icon: <TvIcon />, path: '/status' },
    { text: 'Wyświetlacze', icon: <TvIcon />, path: '/displays' },
    { text: 'Treści', icon: <FolderIcon />, path: '/content' },
    { text: 'Harmonogramy', icon: <ScheduleIcon />, path: '/schedules' },
    { text: 'Grupy', icon: <GroupsIcon />, path: '/groups' },
    { text: 'Alerty', icon: <NotificationsIcon />, path: '/alerts' },
    { text: 'Raporty', icon: <AssessmentIcon />, path: '/reports' },
    { text: 'Dzwonki', icon: <BellIcon />, path: '/bells' },
  ]

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Digital Signage
          </Typography>
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
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton
                  selected={location.pathname === item.path}
                  onClick={() => navigate(item.path)}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
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

