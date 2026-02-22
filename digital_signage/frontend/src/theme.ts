import { createTheme } from '@mui/material/styles'

export const theme = createTheme({
  palette: {
    primary: {
      main: '#0f5fa8',
      light: '#3d85c6',
      dark: '#0a4479',
    },
    secondary: {
      main: '#d26824',
      light: '#e58c55',
      dark: '#9e4a16',
    },
    background: {
      default: '#f2f5f9',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Segoe UI", "Trebuchet MS", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 700,
      letterSpacing: '-0.01em',
    },
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 8px 22px rgba(16, 35, 60, 0.06)',
        },
      },
    },
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
  },
})



