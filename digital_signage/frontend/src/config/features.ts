type FeatureFlags = {
  monitoring: boolean
  displays: boolean
  content: boolean
  bells: boolean
  reports: boolean
  alerts: boolean
  adminUsers: boolean
}

const envEnabled = (name: string, defaultValue: boolean): boolean => {
  const raw = import.meta.env[name]
  if (raw === undefined || raw === null || raw === '') return defaultValue
  return String(raw).toLowerCase() === 'true'
}

// Domyślna konfiguracja funkcji/sekcji.
// W kolejnym kroku można podmienić to na wartości z licencji/API.
export const FEATURE_FLAGS: FeatureFlags = {
  monitoring: envEnabled('VITE_FEATURE_MONITORING', true),
  displays: envEnabled('VITE_FEATURE_DISPLAYS', true),
  content: envEnabled('VITE_FEATURE_CONTENT', true),
  bells: envEnabled('VITE_FEATURE_BELLS', true),
  reports: envEnabled('VITE_FEATURE_REPORTS', true),
  alerts: envEnabled('VITE_FEATURE_ALERTS', true),
  adminUsers: envEnabled('VITE_FEATURE_ADMIN_USERS', true),
}

export type FeatureKey = keyof FeatureFlags
