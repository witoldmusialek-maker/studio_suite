import { User } from '../types'

export type BrandingPreset = {
  appTitle: string
  loginTitle: string
  loginSubtitle: string
  appBarBg: string
  appBarText: string
  appBarAccent: string
  sidebarBg: string
  sidebarBorder: string
  pageBg: string
}

const defaultBranding: BrandingPreset = {
  appTitle: 'Studio Suite - Panel Salonu',
  loginTitle: 'Studio Suite - Logowanie',
  loginSubtitle: 'Zaloguj się do panelu salonu.',
  appBarBg: '#0f5fa8',
  appBarText: '#ffffff',
  appBarAccent: '#ffeb3b',
  sidebarBg: '#ffffff',
  sidebarBorder: '#e5e7eb',
  pageBg: '#f2f5f9',
}

const lucianoInspiredBranding: BrandingPreset = {
  appTitle: 'Studio SARA - Panel Salonu',
  loginTitle: 'Studio SARA - Logowanie',
  loginSubtitle: 'Panel operacyjny i rezerwacje salonu.',
  appBarBg: 'linear-gradient(90deg, #0f0f12 0%, #201a11 58%, #3a2b15 100%)',
  appBarText: '#f8f4ea',
  appBarAccent: '#d7b26a',
  sidebarBg: '#f8f4ea',
  sidebarBorder: '#e5d8bc',
  pageBg: '#f6f3eb',
}

export const getBranding = (user: User | null): BrandingPreset => {
  if (!user) return defaultBranding
  if (user.tenant_id === 1) return lucianoInspiredBranding
  return defaultBranding
}

