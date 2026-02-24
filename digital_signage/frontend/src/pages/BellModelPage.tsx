import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  MenuItem,
  Paper,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Typography,
} from '@mui/material'
import { api } from '../services/api'

type TypZdarzenia = 'lesson' | 'break'

type WzorzecDzwieku = {
  id: string
  klucz: string
  nazwa: string
  opis?: string
}

type SzablonSygnalu = {
  id: string
  nazwa: string
  typ_zdarzenia: TypZdarzenia
  dzwonek_wzorzec: string
  zapowiedz_wzorzec: string
  zatrzymaj_muzyke: boolean
  uruchom_playliste?: string
}

type ZdarzenieDnia = {
  id: string
  godzina: string
  szablon_id: string
}

type TypDnia = {
  id: string
  nazwa: string
  zdarzenia: ZdarzenieDnia[]
}

type WpisKalendarza = {
  id: string
  data: string
  typ_dnia_id: string
  profil_dzwiekow: string
}

type PlanMiesiaca = {
  id: string
  miesiac: string
  nazwa: string
  typ_dnia_id: string
  profil_dzwiekow: string
}

type MapowanieProfilu = {
  id: string
  nazwa_profilu: string
  pliki: Record<string, string>
}

type Awaryjne = {
  stop_globalny: boolean
  powod: string
}

type KonfiguracjaOdtwarzania = {
  odtwarzaj_na_serwerze: boolean
  odtwarzaj_na_klientach: boolean
  dozwolone_display_ids: number[]
}

type ModelDzwonkowDraft = {
  wzorce_dzwiekow: WzorzecDzwieku[]
  szablony_sygnalow: SzablonSygnalu[]
  typy_dnia: TypDnia[]
  plany_miesieczne: PlanMiesiaca[]
  kalendarz: WpisKalendarza[]
  mapowania_profili: MapowanieProfilu[]
  awaryjne: Awaryjne
  konfiguracja_odtwarzania: KonfiguracjaOdtwarzania
}

type PlaylistaDto = {
  id: number
  name: string
}

type PlaylistaUtworDto = {
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

type DzwiekBiblioteki = {
  id: number
  name: string
  file_path: string
}

type DisplayDto = {
  id: number
  name: string
  status: string
  ip_address?: string
}

type BellModelConfigResponse = {
  id?: number | null
  model_json?: Partial<ModelDzwonkowDraft> | null
  revision: number
  updated_at?: string | null
}

const STORAGE_KEY = 'modelDzwonkowDraftV5'
const uid = () => Math.random().toString(36).slice(2, 10)
const placeholderKeys = ['BELL_MAIN', 'BELL_SOFT', 'BELL_BREAK_START', 'BELL_BREAK_END']
const placeholderLabels: Record<string, string> = {
  BELL_MAIN: 'Dzwonek glowny',
  BELL_SOFT: 'Dzwonek lagodny',
  BELL_BREAK_START: 'Start przerwy',
  BELL_BREAK_END: 'Koniec przerwy',
}

const zbudujPusteMapowanie = (nazwaProfilu: string, wzorce: WzorzecDzwieku[]): MapowanieProfilu => {
  const pliki: Record<string, string> = {}
  for (const w of wzorce) {
    pliki[w.klucz] = ''
  }
  return { id: uid(), nazwa_profilu: nazwaProfilu, pliki }
}

const domyslnyDraft = (): ModelDzwonkowDraft => {
  const w1 = { id: uid(), klucz: 'DZWONEK_LEKCJA', nazwa: 'Dzwonek na lekcje' }
  const w2 = { id: uid(), klucz: 'DZWONEK_PRZERWA', nazwa: 'Dzwonek na przerwe' }
  const w3 = { id: uid(), klucz: 'ZAPOWIEDZ_LEKCJA_1', nazwa: 'Zapowiedź na lekcję pierwszą' }
  const w4 = { id: uid(), klucz: 'ZAPOWIEDZ_PRZERWA_1', nazwa: 'Zapowiedź na przerwę pierwszą' }

  const s1id = uid()
  const s2id = uid()
  const t1id = uid()

  const profil = 'Profil domyślny'

  return {
    wzorce_dzwiekow: [w1, w2, w3, w4],
    szablony_sygnalow: [
      {
        id: s1id,
        nazwa: 'Sygnal: lekcja 1 start',
        typ_zdarzenia: 'lesson',
        dzwonek_wzorzec: w1.klucz,
        zapowiedz_wzorzec: w3.klucz,
        zatrzymaj_muzyke: true,
      },
      {
        id: s2id,
        nazwa: 'Sygnal: przerwa po lekcji 1',
        typ_zdarzenia: 'break',
        dzwonek_wzorzec: w2.klucz,
        zapowiedz_wzorzec: w4.klucz,
        zatrzymaj_muzyke: true,
        uruchom_playliste: '',
      },
    ],
    typy_dnia: [
      {
        id: t1id,
        nazwa: 'Standard pn-pt',
        zdarzenia: [
          { id: uid(), godzina: '08:00', szablon_id: s1id },
          { id: uid(), godzina: '08:45', szablon_id: s2id },
        ],
      },
    ],
    plany_miesieczne: [
      {
        id: uid(),
        miesiac: new Date().toISOString().slice(0, 7),
        nazwa: 'Plan miesięczny domyślny',
        typ_dnia_id: t1id,
        profil_dzwiekow: profil,
      },
    ],
    kalendarz: [
      {
        id: uid(),
        data: new Date().toISOString().slice(0, 10),
        typ_dnia_id: t1id,
        profil_dzwiekow: profil,
      },
    ],
    mapowania_profili: [zbudujPusteMapowanie(profil, [w1, w2, w3, w4])],
    awaryjne: {
      stop_globalny: false,
      powod: '',
    },
    konfiguracja_odtwarzania: {
      odtwarzaj_na_serwerze: false,
      odtwarzaj_na_klientach: true,
      dozwolone_display_ids: [],
    },
  }
}

const znormalizujDraft = (raw: Partial<ModelDzwonkowDraft> | null | undefined): ModelDzwonkowDraft => {
  const base = domyslnyDraft()
  if (!raw) return base

  return {
    wzorce_dzwiekow: Array.isArray(raw.wzorce_dzwiekow) ? raw.wzorce_dzwiekow : base.wzorce_dzwiekow,
    szablony_sygnalow: Array.isArray(raw.szablony_sygnalow) ? raw.szablony_sygnalow : base.szablony_sygnalow,
    typy_dnia: Array.isArray(raw.typy_dnia) ? raw.typy_dnia : base.typy_dnia,
    plany_miesieczne: Array.isArray(raw.plany_miesieczne) ? raw.plany_miesieczne : base.plany_miesieczne,
    kalendarz: Array.isArray(raw.kalendarz) ? raw.kalendarz : base.kalendarz,
    mapowania_profili: Array.isArray(raw.mapowania_profili) ? raw.mapowania_profili : base.mapowania_profili,
    awaryjne: raw.awaryjne
      ? {
          stop_globalny: Boolean(raw.awaryjne.stop_globalny),
          powod: raw.awaryjne.powod || '',
        }
      : base.awaryjne,
    konfiguracja_odtwarzania: raw.konfiguracja_odtwarzania
      ? {
          odtwarzaj_na_serwerze: Boolean(raw.konfiguracja_odtwarzania.odtwarzaj_na_serwerze),
          odtwarzaj_na_klientach: raw.konfiguracja_odtwarzania.odtwarzaj_na_klientach !== false,
          dozwolone_display_ids: Array.isArray(raw.konfiguracja_odtwarzania.dozwolone_display_ids)
            ? raw.konfiguracja_odtwarzania.dozwolone_display_ids.map((id) => Number(id)).filter((id) => Number.isFinite(id))
            : [],
        }
      : base.konfiguracja_odtwarzania,
  }
}

interface PanelProps {
  value: number
  index: number
  children: React.ReactNode
}

function Panel({ value, index, children }: PanelProps) {
  if (value !== index) return null
  return <Box sx={{ mt: 2 }}>{children}</Box>
}

const BellModelPage = () => {
  const [draft, setDraft] = useState<ModelDzwonkowDraft>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) return domyslnyDraft()
      return znormalizujDraft(JSON.parse(raw) as Partial<ModelDzwonkowDraft>)
    } catch {
      return domyslnyDraft()
    }
  })

  const [tab, setTab] = useState(0)
  const [saveInfo, setSaveInfo] = useState('')
  const [wybranyTypDniaId, setWybranyTypDniaId] = useState('')
  const [playlisty, setPlaylisty] = useState<PlaylistaDto[]>([])
  const [dzwiekiBiblioteki, setDzwiekiBiblioteki] = useState<DzwiekBiblioteki[]>([])
  const [wyswietlacze, setWyswietlacze] = useState<DisplayDto[]>([])
  const [podgladData, setPodgladData] = useState(new Date().toISOString().slice(0, 10))
  const [podgladGodzina, setPodgladGodzina] = useState(new Date().toTimeString().slice(0, 5))
  const [symulacjaData, setSymulacjaData] = useState(new Date().toISOString().slice(0, 10))
  const [symulacjaGodzina, setSymulacjaGodzina] = useState(new Date().toTimeString().slice(0, 5))
  const [wybranyProfilMapowania, setWybranyProfilMapowania] = useState('')
  const [wybranyPlanMiesiacaId, setWybranyPlanMiesiacaId] = useState('')
  const [statusBiblioteki, setStatusBiblioteki] = useState('')
  const [bladBiblioteki, setBladBiblioteki] = useState('')
  const [backendRevision, setBackendRevision] = useState(0)
  const [odtwarzanyDzwiekId, setOdtwarzanyDzwiekId] = useState<number | null>(null)
  const audioBlobUrlRef = useRef<string | null>(null)
  const [wybranaPlaylistaId, setWybranaPlaylistaId] = useState<number | null>(null)
  const [utworyPlaylisty, setUtworyPlaylisty] = useState<PlaylistaUtworDto[]>([])
  const [zrodloUtworu, setZrodloUtworu] = useState<'sound' | 'placeholder'>('sound')
  const [wybranyDzwiekId, setWybranyDzwiekId] = useState('')
  const [wybranyPlaceholder, setWybranyPlaceholder] = useState('BELL_MAIN')
  const [tytulUtworu, setTytulUtworu] = useState('')
  const [kolejnoscUtworu, setKolejnoscUtworu] = useState('0')
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(draft))
    setSaveInfo('Model zapisany lokalnie.')
  }, [draft])

  useEffect(() => {
    if (!wybranyTypDniaId && draft.typy_dnia.length > 0) {
      setWybranyTypDniaId(draft.typy_dnia[0].id)
    }
  }, [draft.typy_dnia, wybranyTypDniaId])

  useEffect(() => {
    if (!wybranyPlanMiesiacaId && draft.plany_miesieczne.length > 0) {
      setWybranyPlanMiesiacaId(draft.plany_miesieczne[0].id)
    }
  }, [draft.plany_miesieczne, wybranyPlanMiesiacaId])

  useEffect(() => {
    const profileNames = Array.from(new Set(draft.kalendarz.map((k) => k.profil_dzwiekow).filter(Boolean)))
    if (!wybranyProfilMapowania && profileNames.length > 0) {
      setWybranyProfilMapowania(profileNames[0])
    }
  }, [draft.kalendarz, wybranyProfilMapowania])

  useEffect(() => {
    const nazwy = draft.mapowania_profili.map((m) => m.nazwa_profilu)
    if (nazwy.length === 0) return
    if (!wybranyProfilMapowania || !nazwy.includes(wybranyProfilMapowania)) {
      setWybranyProfilMapowania(nazwy[0])
    }
  }, [draft.mapowania_profili, wybranyProfilMapowania])

  const oznaczAktualizacjeInformacji = (komunikat: string) => {
    setStatusBiblioteki(komunikat)
  }

  const odswiezBiblioteke = async (komunikat = 'Pobrano aktualne informacje o bibliotece.') => {
    const [resPlaylisty, resDzwieki, resWyswietlacze] = await Promise.all([
      api.get<PlaylistaDto[]>('/bells/runtime/music-schedules'),
      api.get<DzwiekBiblioteki[]>('/bells/sounds'),
      api.get<DisplayDto[]>('/displays/'),
    ])
    setPlaylisty(resPlaylisty.data || [])
    setDzwiekiBiblioteki(resDzwieki.data || [])
    setWyswietlacze(resWyswietlacze.data || [])
    oznaczAktualizacjeInformacji(komunikat)
    if (wybranaPlaylistaId) {
      try {
        const resTracki = await api.get<PlaylistaUtworDto[]>(`/bells/runtime/music-schedules/${wybranaPlaylistaId}/tracks`)
        setUtworyPlaylisty(resTracki.data || [])
      } catch {
        setUtworyPlaylisty([])
      }
    }
  }

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const [resPlaylisty, resDzwieki, resWyswietlacze] = await Promise.all([
          api.get<PlaylistaDto[]>('/bells/runtime/music-schedules'),
          api.get<DzwiekBiblioteki[]>('/bells/sounds'),
          api.get<DisplayDto[]>('/displays/'),
        ])
        if (!mounted) return
        setPlaylisty(resPlaylisty.data || [])
        setDzwiekiBiblioteki(resDzwieki.data || [])
        setWyswietlacze(resWyswietlacze.data || [])
        oznaczAktualizacjeInformacji('Pobrano dane startowe biblioteki i playlist.')
      } catch {
        if (!mounted) return
        setPlaylisty([])
        setDzwiekiBiblioteki([])
        setWyswietlacze([])
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    let mounted = true
    const loadModel = async () => {
      try {
        const res = await api.get<BellModelConfigResponse>('/bells/runtime/model-config')
        if (!mounted) return
        const modelJson = res.data?.model_json
        if (modelJson && typeof modelJson === 'object') {
          const normalized = znormalizujDraft(modelJson)
          setDraft(normalized)
          setWybranyTypDniaId(normalized.typy_dnia[0]?.id || '')
          setWybranyProfilMapowania(normalized.mapowania_profili[0]?.nazwa_profilu || '')
          setSaveInfo('Model załadowany z backendu.')
        }
        setBackendRevision(res.data?.revision || 0)
      } catch {
        // fallback pozostaje lokalny
      }
    }
    loadModel()
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
      if (audioBlobUrlRef.current) {
        URL.revokeObjectURL(audioBlobUrlRef.current)
        audioBlobUrlRef.current = null
      }
    }
  }, [])

  const wybranyTypDnia = useMemo(
    () => draft.typy_dnia.find((t) => t.id === wybranyTypDniaId) || null,
    [draft.typy_dnia, wybranyTypDniaId]
  )

  const mapaSzablonow = useMemo(() => {
    const m = new Map<string, SzablonSygnalu>()
    draft.szablony_sygnalow.forEach((s) => m.set(s.id, s))
    return m
  }, [draft.szablony_sygnalow])

  const planMiesiacaDlaPodgladu = useMemo(() => {
    const miesiac = symulacjaData.slice(0, 7)
    return draft.plany_miesieczne.find((p) => p.miesiac === miesiac) || null
  }, [draft.plany_miesieczne, symulacjaData])

  const wpisWyjatkuDnia = useMemo(() => draft.kalendarz.find((k) => k.data === symulacjaData) || null, [draft.kalendarz, symulacjaData])

  const wpisDnia = useMemo(() => {
    if (wpisWyjatkuDnia) return wpisWyjatkuDnia
    if (!planMiesiacaDlaPodgladu) return null
    return {
      id: `plan-${planMiesiacaDlaPodgladu.id}-${symulacjaData}`,
      data: symulacjaData,
      typ_dnia_id: planMiesiacaDlaPodgladu.typ_dnia_id,
      profil_dzwiekow: planMiesiacaDlaPodgladu.profil_dzwiekow,
    } as WpisKalendarza
  }, [wpisWyjatkuDnia, planMiesiacaDlaPodgladu, symulacjaData])

  const typDniaPodgladu = useMemo(() => {
    if (!wpisDnia) return null
    return draft.typy_dnia.find((t) => t.id === wpisDnia.typ_dnia_id) || null
  }, [wpisDnia, draft.typy_dnia])

  const mapowanieProfiluPodgladu = useMemo(() => {
    if (!wpisDnia) return null
    return draft.mapowania_profili.find((m) => m.nazwa_profilu === wpisDnia.profil_dzwiekow) || null
  }, [wpisDnia, draft.mapowania_profili])

  const aktualnieWykonywaneId = useMemo(() => {
    if (!typDniaPodgladu) return null
    const teraz = Number(symulacjaGodzina.slice(0, 2)) * 60 + Number(symulacjaGodzina.slice(3, 5))
    let found: string | null = null
    for (const z of typDniaPodgladu.zdarzenia) {
      const m = Number(z.godzina.slice(0, 2)) * 60 + Number(z.godzina.slice(3, 5))
      if (m <= teraz) found = z.id
    }
    return found
  }, [typDniaPodgladu, symulacjaGodzina])

  const nastepneZdarzenieId = useMemo(() => {
    if (!typDniaPodgladu) return null
    const teraz = Number(symulacjaGodzina.slice(0, 2)) * 60 + Number(symulacjaGodzina.slice(3, 5))
    const next = typDniaPodgladu.zdarzenia
      .slice()
      .sort((a, b) => a.godzina.localeCompare(b.godzina))
      .find((z) => {
        const m = Number(z.godzina.slice(0, 2)) * 60 + Number(z.godzina.slice(3, 5))
        return m > teraz
      })
    return next?.id || null
  }, [typDniaPodgladu, symulacjaGodzina])

  const ensureProfileMapping = (profil: string) => {
    if (!profil.trim()) return
    setDraft((prev) => {
      const exists = prev.mapowania_profili.some((m) => m.nazwa_profilu === profil)
      if (exists) return prev
      return {
        ...prev,
        mapowania_profili: [...prev.mapowania_profili, zbudujPusteMapowanie(profil, prev.wzorce_dzwiekow)],
      }
    })
  }

  const dodajProfilDzwiekow = () => {
    setDraft((prev) => {
      let i = 1
      let nazwa = `Profil ${i}`
      const istnieje = (n: string) => prev.mapowania_profili.some((m) => m.nazwa_profilu === n)
      while (istnieje(nazwa)) {
        i += 1
        nazwa = `Profil ${i}`
      }
      return {
        ...prev,
        mapowania_profili: [...prev.mapowania_profili, zbudujPusteMapowanie(nazwa, prev.wzorce_dzwiekow)],
      }
    })
  }

  const usunProfilDzwiekow = (id: string) => {
    setDraft((prev) => {
      if (prev.mapowania_profili.length <= 1) return prev
      const del = prev.mapowania_profili.find((m) => m.id === id)
      if (!del) return prev
      const nextProfiles = prev.mapowania_profili.filter((m) => m.id !== id)
      const fallback = nextProfiles[0]?.nazwa_profilu || 'Profil domyślny'
      return {
        ...prev,
        mapowania_profili: nextProfiles,
        plany_miesieczne: prev.plany_miesieczne.map((p) =>
          p.profil_dzwiekow === del.nazwa_profilu ? { ...p, profil_dzwiekow: fallback } : p
        ),
        kalendarz: prev.kalendarz.map((k) =>
          k.profil_dzwiekow === del.nazwa_profilu ? { ...k, profil_dzwiekow: fallback } : k
        ),
      }
    })
  }

  const dodajWzorzec = () => {
    const nowy = { id: uid(), klucz: `NOWY_${draft.wzorce_dzwiekow.length + 1}`, nazwa: 'Nowy wzorzec dźwięku' }
    setDraft((prev) => ({
      ...prev,
      wzorce_dzwiekow: [...prev.wzorce_dzwiekow, nowy],
      mapowania_profili: prev.mapowania_profili.map((m) => ({
        ...m,
        pliki: { ...m.pliki, [nowy.klucz]: '' },
      })),
    }))
  }

  const usunWzorzec = (id: string) => {
    setDraft((prev) => {
      const del = prev.wzorce_dzwiekow.find((w) => w.id === id)
      if (!del) return prev
      const nextMappings = prev.mapowania_profili.map((m) => {
        const next = { ...m.pliki }
        delete next[del.klucz]
        return { ...m, pliki: next }
      })
      return {
        ...prev,
        wzorce_dzwiekow: prev.wzorce_dzwiekow.filter((w) => w.id !== id),
        mapowania_profili: nextMappings,
      }
    })
  }

  const dodajSzablon = () => {
    const w = draft.wzorce_dzwiekow[0]
    setDraft((prev) => ({
      ...prev,
      szablony_sygnalow: [
        ...prev.szablony_sygnalow,
        {
          id: uid(),
          nazwa: 'Nowy sygnał',
          typ_zdarzenia: 'lesson',
          dzwonek_wzorzec: w?.klucz || '',
          zapowiedz_wzorzec: w?.klucz || '',
          zatrzymaj_muzyke: true,
          uruchom_playliste: '',
        },
      ],
    }))
  }

  const usunSzablon = (id: string) => {
    setDraft((prev) => ({
      ...prev,
      szablony_sygnalow: prev.szablony_sygnalow.filter((s) => s.id !== id),
      typy_dnia: prev.typy_dnia.map((t) => ({
        ...t,
        zdarzenia: t.zdarzenia.filter((z) => z.szablon_id !== id),
      })),
    }))
  }

  const dodajTypDnia = () => {
    const id = uid()
    setDraft((prev) => ({
      ...prev,
      typy_dnia: [...prev.typy_dnia, { id, nazwa: 'Nowy typ dnia', zdarzenia: [] }],
    }))
    setWybranyTypDniaId(id)
  }

  const usunTypDnia = (id: string) => {
    setDraft((prev) => ({
      ...prev,
      typy_dnia: prev.typy_dnia.filter((t) => t.id !== id),
      kalendarz: prev.kalendarz.filter((k) => k.typ_dnia_id !== id),
    }))
  }

  const dodajZdarzenie = () => {
    if (!wybranyTypDnia || draft.szablony_sygnalow.length === 0) return
    const pierwszySzablon = draft.szablony_sygnalow[0].id
    setDraft((prev) => ({
      ...prev,
      typy_dnia: prev.typy_dnia.map((t) =>
        t.id === wybranyTypDnia.id
          ? { ...t, zdarzenia: [...t.zdarzenia, { id: uid(), godzina: '08:00', szablon_id: pierwszySzablon }] }
          : t
      ),
    }))
  }

  const usunZdarzenie = (zdarzenieId: string) => {
    if (!wybranyTypDnia) return
    setDraft((prev) => ({
      ...prev,
      typy_dnia: prev.typy_dnia.map((t) =>
        t.id === wybranyTypDnia.id ? { ...t, zdarzenia: t.zdarzenia.filter((z) => z.id !== zdarzenieId) } : t
      ),
    }))
  }

  const dodajPlanMiesiaca = () => {
    if (draft.typy_dnia.length === 0) return
    const profil = 'Profil domyślny'
    ensureProfileMapping(profil)
    const id = uid()
    setDraft((prev) => ({
      ...prev,
      plany_miesieczne: [
        ...prev.plany_miesieczne,
        {
          id,
          miesiac: new Date().toISOString().slice(0, 7),
          nazwa: 'Nowy plan miesięczny',
          typ_dnia_id: prev.typy_dnia[0].id,
          profil_dzwiekow: profil,
        },
      ],
    }))
    setWybranyPlanMiesiacaId(id)
  }

  const usunPlanMiesiaca = (id: string) => {
    setDraft((prev) => ({
      ...prev,
      plany_miesieczne: prev.plany_miesieczne.filter((p) => p.id !== id),
    }))
  }

  const dodajWpisKalendarza = () => {
    if (draft.typy_dnia.length === 0) return
    const profil = 'Profil domyślny'
    ensureProfileMapping(profil)
    setDraft((prev) => ({
      ...prev,
      kalendarz: [
        ...prev.kalendarz,
        {
          id: uid(),
          data: new Date().toISOString().slice(0, 10),
          typ_dnia_id: prev.typy_dnia[0].id,
          profil_dzwiekow: profil,
        },
      ],
    }))
  }

  const usunWpisKalendarza = (id: string) => {
    setDraft((prev) => ({
      ...prev,
      kalendarz: prev.kalendarz.filter((k) => k.id !== id),
    }))
  }

  const zastosujSymulacje = () => {
    setSymulacjaData(podgladData)
    setSymulacjaGodzina(podgladGodzina)
  }

  const wgrajDzwiek = async (file: File, nazwa: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('name', nazwa.trim() || file.name.replace(/\.[^/.]+$/, ''))
    await api.post('/bells/upload-sound', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    await odswiezBiblioteke('Dźwięk dodany do biblioteki.')
  }

  const zmienNazweDzwieku = async (id: number, nowaNazwa: string) => {
    await api.put(`/bells/sounds/${id}`, { name: nowaNazwa.trim() })
    await odswiezBiblioteke('Nazwa dźwięku zaktualizowana.')
  }

  const usunDzwiekBiblioteki = async (id: number) => {
    await api.delete(`/bells/sounds/${id}`)
    await odswiezBiblioteke('Dźwięk usunięty z biblioteki.')
  }
  const odsluchajDzwiek = async (id: number) => {
    let nextBlobUrl: string | null = null
    try {
      setBladBiblioteki('')
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.currentTime = 0
      }
      const res = await api.get(`/bells/sounds/${id}/file`, { responseType: 'arraybuffer' })
      const contentType = (res.headers?.['content-type'] as string | undefined) || 'audio/mpeg'
      const blob = new Blob([res.data], { type: contentType })
      nextBlobUrl = URL.createObjectURL(blob)
      if (audioBlobUrlRef.current) {
        URL.revokeObjectURL(audioBlobUrlRef.current)
      }
      audioBlobUrlRef.current = nextBlobUrl
      const audio = new Audio(nextBlobUrl)
      audioRef.current = audio
      setOdtwarzanyDzwiekId(id)
      audio.onended = () => setOdtwarzanyDzwiekId((prev) => (prev === id ? null : prev))
      audio.onerror = () => {
        setOdtwarzanyDzwiekId((prev) => (prev === id ? null : prev))
        setBladBiblioteki('Nie udało się odtworzyć dźwięku.')
      }
      const playPromise = audio.play()
      if (playPromise) {
        await playPromise
      }
    } catch (err: any) {
      if (nextBlobUrl) {
        URL.revokeObjectURL(nextBlobUrl)
      }
      setOdtwarzanyDzwiekId(null)
      setBladBiblioteki(err?.response?.data?.detail || err?.message || 'Nie udało się odtworzyć dźwięku.')
    }
  }

  const zatrzymajOdsluch = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
    }
    if (audioBlobUrlRef.current) {
      URL.revokeObjectURL(audioBlobUrlRef.current)
      audioBlobUrlRef.current = null
    }
    setOdtwarzanyDzwiekId(null)
  }
  const dodajPlayliste = async (nazwa: string) => {
    await api.post('/bells/runtime/music-schedules', {
      name: nazwa.trim(),
      start_time: '08:45:00',
      end_time: '08:55:00',
      days_of_week: [1, 2, 3, 4, 5],
      volume: 35,
      priority: 0,
      active: true,
    })
    await odswiezBiblioteke('Playlista dodana.')
  }

  const zmienNazwePlaylisty = async (id: number, nowaNazwa: string) => {
    await api.put(`/bells/runtime/music-schedules/${id}`, { name: nowaNazwa.trim() })
    await odswiezBiblioteke('Nazwa playlisty zaktualizowana.')
  }

  const usunPlayliste = async (id: number) => {
    await api.delete(`/bells/runtime/music-schedules/${id}`)
    if (wybranaPlaylistaId === id) {
      setWybranaPlaylistaId(null)
      setUtworyPlaylisty([])
    }
    await odswiezBiblioteke('Playlista usunięta.')
  }

  const zaladujUtworyPlaylisty = async (playlistId: number) => {
    const res = await api.get<PlaylistaUtworDto[]>(`/bells/runtime/music-schedules/${playlistId}/tracks`)
    setUtworyPlaylisty(res.data || [])
  }

  const dodajUtworDoPlaylisty = async () => {
    if (!wybranaPlaylistaId) return

    const payload: Record<string, unknown> = {
      title: tytulUtworu.trim() || null,
      sort_order: Number(kolejnoscUtworu || 0),
      active: true,
    }

    if (zrodloUtworu === 'sound') {
      if (!wybranyDzwiekId) return
      payload.sound_id = Number(wybranyDzwiekId)
    } else {
      if (!wybranyPlaceholder.trim()) return
      payload.placeholder_key = wybranyPlaceholder.trim().toUpperCase()
    }

    await api.post(`/bells/runtime/music-schedules/${wybranaPlaylistaId}/tracks`, payload)
    setTytulUtworu('')
    setKolejnoscUtworu('0')
    setWybranyDzwiekId('')
    setWybranyPlaceholder('BELL_MAIN')
    await zaladujUtworyPlaylisty(wybranaPlaylistaId)
    oznaczAktualizacjeInformacji('Dodano utwor do playlisty.')
  }

  const usunUtworZPlaylisty = async (trackId: number) => {
    await api.delete(`/bells/runtime/music-tracks/${trackId}`)
    if (wybranaPlaylistaId) {
      await zaladujUtworyPlaylisty(wybranaPlaylistaId)
    }
    oznaczAktualizacjeInformacji('Usunieto utwor z playlisty.')
  }

  const resetModelu = () => {
    const next = domyslnyDraft()
    setDraft(next)
    setWybranyTypDniaId(next.typy_dnia[0]?.id || '')
    setWybranyProfilMapowania(next.mapowania_profili[0]?.nazwa_profilu || '')
    localStorage.removeItem(STORAGE_KEY)
  }

  const zapiszModelDoBackendu = async () => {
    const payload = { model_json: draft }
    const res = await api.put<BellModelConfigResponse>('/bells/runtime/model-config', payload)
    setBackendRevision(res.data?.revision || 0)
    setSaveInfo(`Model zapisany w backendzie (rev ${res.data?.revision || 0}).`)
  }

  const pobierzModelZBackendu = async () => {
    const res = await api.get<BellModelConfigResponse>('/bells/runtime/model-config')
    const modelJson = res.data?.model_json
    if (!modelJson || typeof modelJson !== 'object') {
      setSaveInfo('Brak modelu w backendzie.')
      setBackendRevision(res.data?.revision || 0)
      return
    }
    const normalized = znormalizujDraft(modelJson)
    setDraft(normalized)
    setWybranyTypDniaId(normalized.typy_dnia[0]?.id || '')
    setWybranyProfilMapowania(normalized.mapowania_profili[0]?.nazwa_profilu || '')
    setBackendRevision(res.data?.revision || 0)
    setSaveInfo(`Model pobrany z backendu (rev ${res.data?.revision || 0}).`)
  }

  const profileNames = draft.mapowania_profili.map((m) => m.nazwa_profilu)
  const wybraneWyswietlacze = draft.konfiguracja_odtwarzania.dozwolone_display_ids
  const liczbaOnlineWyswietlaczy = wyswietlacze.filter((d) => d.status === 'online').length
  const activeMapping = draft.mapowania_profili.find((m) => m.nazwa_profilu === wybranyProfilMapowania) || null
  const wybranyPlanMiesiaca = draft.plany_miesieczne.find((p) => p.id === wybranyPlanMiesiacaId) || null
  const aktualneZdarzenie = typDniaPodgladu?.zdarzenia.find((z) => z.id === aktualnieWykonywaneId) || null
  const nastepneZdarzenie = typDniaPodgladu?.zdarzenia.find((z) => z.id === nastepneZdarzenieId) || null
  const aktualnySzablon = aktualneZdarzenie ? mapaSzablonow.get(aktualneZdarzenie.szablon_id) || null : null
  const nastepnySzablon = nastepneZdarzenie ? mapaSzablonow.get(nastepneZdarzenie.szablon_id) || null : null

  return (
    <Box sx={{ maxWidth: '100%', overflowX: 'clip' }}>
      <Typography variant="h4" sx={{ mb: 1 }}>Model docelowy dzwonków</Typography>
      <Alert severity="info" sx={{ mb: 2 }}>Model logiki dzwonków. Zapis i odczyt są podłączone do backendu.</Alert>
      <Paper variant="outlined" sx={{ mb: 2, p: 1.5 }}>
        <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
          README / HELP
        </Typography>
        <Typography variant="body2" color="text.secondary">
          1) Po deployu sprawdź wersję aplikacji w lewym panelu. 2) Upewnij się, że działają oba profile:
          operator wyświetlaczy i operator dzwonków. 3) Konta tworzysz i resetujesz hasła w sekcji
          Administracja {'->'} Użytkownicy. 4) Po zmianach modelu dzwonków użyj „Zapisz do backendu” i
          odśwież klientów.
        </Typography>
      </Paper>
      {saveInfo && <Alert severity="success" sx={{ mb: 2 }}>{saveInfo}</Alert>}

      <Paper
        sx={{
          p: 1.5,
          mb: 2,
          position: 'sticky',
          top: 12,
          zIndex: 10,
          border: '1px solid',
          borderColor: 'divider',
          backgroundColor: 'background.paper',
        }}
      >
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={1.5}
          alignItems={{ xs: 'stretch', md: 'center' }}
          sx={{ flexWrap: { md: 'wrap' }, rowGap: 1, columnGap: 1 }}
        >
          <Chip
            color={draft.awaryjne.stop_globalny ? 'warning' : 'success'}
            label={draft.awaryjne.stop_globalny ? 'TRYB AWARYJNY: AKTYWNY' : 'TRYB AWARYJNY: NIEAKTYWNY'}
          />
          <Chip label={`Symulacja: ${symulacjaData} ${symulacjaGodzina}`} />
          <Chip label={`Profil: ${wpisDnia?.profil_dzwiekow || '-'}`} />
          <Chip
            color={draft.konfiguracja_odtwarzania.odtwarzaj_na_serwerze ? 'warning' : 'default'}
            label={`Serwer audio: ${draft.konfiguracja_odtwarzania.odtwarzaj_na_serwerze ? 'ON' : 'OFF'}`}
          />
          <Chip
            color={draft.konfiguracja_odtwarzania.odtwarzaj_na_klientach ? 'success' : 'default'}
            label={`Klienci audio: ${draft.konfiguracja_odtwarzania.odtwarzaj_na_klientach ? 'ON' : 'OFF'}`}
          />
          <Chip
            variant="outlined"
            label={`Klienci docelowi: ${wybraneWyswietlacze.length > 0 ? wybraneWyswietlacze.length : 'wszyscy'}`}
          />
          <Chip
            label={`Teraz: ${aktualnySzablon ? `${aktualneZdarzenie?.godzina} ${aktualnySzablon.nazwa}` : 'brak zdarzenia'}`}
            color={aktualnySzablon ? 'primary' : 'default'}
          />
          <Chip
            label={`Następne: ${nastepnySzablon ? `${nastepneZdarzenie?.godzina} ${nastepnySzablon.nazwa}` : 'brak'} `}
            variant="outlined"
          />
          <Chip label={`Backend rev: ${backendRevision}`} variant="outlined" />
          <Button
            variant="contained"
            color={draft.awaryjne.stop_globalny ? 'success' : 'warning'}
            onClick={() => setDraft((prev) => ({ ...prev, awaryjne: { ...prev.awaryjne, stop_globalny: !prev.awaryjne.stop_globalny } }))}
          >
            {draft.awaryjne.stop_globalny ? 'Wznów dzwonki' : 'Awaryjne STOP'}
          </Button>
          <Button
            variant="contained"
            onClick={async () => {
              try {
                await zapiszModelDoBackendu()
              } catch (err: any) {
                setSaveInfo(err?.response?.data?.detail || 'Nie udało się zapisać modelu do backendu.')
              }
            }}
          >
            Zapisz do backendu
          </Button>
          <Button
            variant="outlined"
            onClick={async () => {
              try {
                await pobierzModelZBackendu()
              } catch (err: any) {
                setSaveInfo(err?.response?.data?.detail || 'Nie udało się pobrać modelu z backendu.')
              }
            }}
          >
            Pobierz z backendu
          </Button>
          <Button variant="outlined" color="error" onClick={resetModelu}>Reset modelu</Button>
          <Button
            variant="outlined"
            component="a"
            href="/download/windows_bell_client.exe"
            target="_blank"
            rel="noopener noreferrer"
          >
            Pobierz klienta Windows (EXE)
          </Button>
        </Stack>
        <TextField
          fullWidth
          size="small"
          sx={{ mt: 1 }}
          label="Powód awaryjny"
          value={draft.awaryjne.powod}
          onChange={(e) => setDraft((prev) => ({ ...prev, awaryjne: { ...prev.awaryjne, powod: e.target.value } }))}
        />
      </Paper>

      <Paper sx={{ p: 1 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" scrollButtons="auto" allowScrollButtonsMobile>
          <Tab label="1. Podgląd dnia" />
          <Tab label="2. Kalendarz i profile" />
          <Tab label="3. Sygnały" />
          <Tab label="4. Biblioteka i playlisty" />
          <Tab label="5. Wzorce dźwięków" />
          <Tab label="6. Typy dnia" />
        </Tabs>
      </Paper>

      <Panel value={tab} index={4}>
        <Card>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" sx={{ mb: 1 }}>
              <Typography variant="h6">Lista wzorców dźwięków</Typography>
              <Button variant="contained" size="small" onClick={dodajWzorzec}>Dodaj wzorzec</Button>
            </Stack>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Klucz</TableCell>
                    <TableCell>Nazwa (duży tekst)</TableCell>
                    <TableCell>Opis</TableCell>
                    <TableCell>Akcje</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {draft.wzorce_dzwiekow.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell>
                        <TextField size="small" value={p.klucz} onChange={(e) => setDraft((prev) => ({ ...prev, wzorce_dzwiekow: prev.wzorce_dzwiekow.map((x) => x.id === p.id ? { ...x, klucz: e.target.value.toUpperCase() } : x) }))} />
                      </TableCell>
                      <TableCell sx={{ minWidth: 320 }}>
                        <TextField size="small" fullWidth value={p.nazwa} onChange={(e) => setDraft((prev) => ({ ...prev, wzorce_dzwiekow: prev.wzorce_dzwiekow.map((x) => x.id === p.id ? { ...x, nazwa: e.target.value } : x) }))} />
                      </TableCell>
                      <TableCell>
                        <TextField size="small" value={p.opis || ''} onChange={(e) => setDraft((prev) => ({ ...prev, wzorce_dzwiekow: prev.wzorce_dzwiekow.map((x) => x.id === p.id ? { ...x, opis: e.target.value } : x) }))} />
                      </TableCell>
                      <TableCell>
                        <Button color="error" size="small" onClick={() => usunWzorzec(p.id)}>Usuń</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Panel>

      <Panel value={tab} index={2}>
        <Card>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" sx={{ mb: 1 }}>
              <Typography variant="h6">Szablony sygnałów (lekcja/przerwa)</Typography>
              <Button variant="contained" size="small" onClick={dodajSzablon}>Dodaj szablon</Button>
            </Stack>
            <Paper variant="outlined" sx={{ p: 1.5, mb: 1.5 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Konfiguracja odtwarzania dźwięku</Typography>
              <Grid container spacing={1}>
                <Grid item xs={12} md={3}>
                  <TextField
                    fullWidth
                    size="small"
                    select
                    label="Odtwarzanie na serwerze"
                    value={draft.konfiguracja_odtwarzania.odtwarzaj_na_serwerze ? 'true' : 'false'}
                    onChange={(e) =>
                      setDraft((prev) => ({
                        ...prev,
                        konfiguracja_odtwarzania: {
                          ...prev.konfiguracja_odtwarzania,
                          odtwarzaj_na_serwerze: e.target.value === 'true',
                        },
                      }))
                    }
                  >
                    <MenuItem value="false">Wyłączone</MenuItem>
                    <MenuItem value="true">Włączone</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={12} md={3}>
                  <TextField
                    fullWidth
                    size="small"
                    select
                    label="Odtwarzanie na klientach"
                    value={draft.konfiguracja_odtwarzania.odtwarzaj_na_klientach ? 'true' : 'false'}
                    onChange={(e) =>
                      setDraft((prev) => ({
                        ...prev,
                        konfiguracja_odtwarzania: {
                          ...prev.konfiguracja_odtwarzania,
                          odtwarzaj_na_klientach: e.target.value === 'true',
                        },
                      }))
                    }
                  >
                    <MenuItem value="true">Włączone</MenuItem>
                    <MenuItem value="false">Wyłączone</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    size="small"
                    select
                    SelectProps={{ multiple: true }}
                    label="Dozwoleni klienci (displaye)"
                    value={wybraneWyswietlacze}
                    onChange={(e) => {
                      const value = e.target.value as unknown as Array<string | number>
                      const ids = value.map((v) => Number(v)).filter((v) => Number.isFinite(v))
                      setDraft((prev) => ({
                        ...prev,
                        konfiguracja_odtwarzania: {
                          ...prev.konfiguracja_odtwarzania,
                          dozwolone_display_ids: ids,
                        },
                      }))
                    }}
                    helperText={wybraneWyswietlacze.length === 0
                      ? `Brak ograniczenia (wszyscy klienci), online: ${liczbaOnlineWyswietlaczy}/${wyswietlacze.length}`
                      : `Wybrano: ${wybraneWyswietlacze.length}, online: ${liczbaOnlineWyswietlaczy}/${wyswietlacze.length}`}
                  >
                    {wyswietlacze.map((d) => (
                      <MenuItem key={d.id} value={d.id}>
                        #{d.id} {d.name} ({d.status})
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>
              </Grid>
              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => {
                    const ids = wyswietlacze.filter((d) => d.status === 'online').map((d) => d.id)
                    setDraft((prev) => ({
                      ...prev,
                      konfiguracja_odtwarzania: {
                        ...prev.konfiguracja_odtwarzania,
                        dozwolone_display_ids: ids,
                      },
                    }))
                  }}
                >
                  Wybierz tylko online
                </Button>
                <Button
                  size="small"
                  variant="text"
                  onClick={() =>
                    setDraft((prev) => ({
                      ...prev,
                      konfiguracja_odtwarzania: {
                        ...prev.konfiguracja_odtwarzania,
                        dozwolone_display_ids: [],
                      },
                    }))
                  }
                >
                  Wyczyść ograniczenie klientów
                </Button>
              </Stack>
            </Paper>
            {draft.szablony_sygnalow.map((s) => (
              <Paper key={s.id} sx={{ p: 1, mb: 1 }}>
                <Grid container spacing={1}>
                  <Grid item xs={12} md={4}>
                    <TextField fullWidth size="small" label="Nazwa sygnału" value={s.nazwa} onChange={(e) => setDraft((prev) => ({ ...prev, szablony_sygnalow: prev.szablony_sygnalow.map((x) => x.id === s.id ? { ...x, nazwa: e.target.value } : x) }))} />
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      fullWidth
                      size="small"
                      select
                      label="Typ"
                      value={s.typ_zdarzenia}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          szablony_sygnalow: prev.szablony_sygnalow.map((x) =>
                            x.id === s.id
                              ? {
                                  ...x,
                                  typ_zdarzenia: e.target.value as TypZdarzenia,
                                  uruchom_playliste: e.target.value === 'break' ? x.uruchom_playliste : '',
                                }
                              : x
                          ),
                        }))
                      }
                    >
                      <MenuItem value="lesson">Lekcja</MenuItem>
                      <MenuItem value="break">Przerwa</MenuItem>
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <TextField fullWidth size="small" select label="Wzorzec dzwonka" value={s.dzwonek_wzorzec} onChange={(e) => setDraft((prev) => ({ ...prev, szablony_sygnalow: prev.szablony_sygnalow.map((x) => x.id === s.id ? { ...x, dzwonek_wzorzec: e.target.value } : x) }))}>
                      {draft.wzorce_dzwiekow.map((p) => <MenuItem key={p.id} value={p.klucz}><Typography variant="subtitle1" sx={{ whiteSpace: 'normal' }}>{p.nazwa}</Typography></MenuItem>)}
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <TextField fullWidth size="small" select label="Wzorzec zapowiedzi" value={s.zapowiedz_wzorzec} onChange={(e) => setDraft((prev) => ({ ...prev, szablony_sygnalow: prev.szablony_sygnalow.map((x) => x.id === s.id ? { ...x, zapowiedz_wzorzec: e.target.value } : x) }))}>
                      {draft.wzorce_dzwiekow.map((p) => <MenuItem key={p.id} value={p.klucz}><Typography variant="subtitle1" sx={{ whiteSpace: 'normal' }}>{p.nazwa}</Typography></MenuItem>)}
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <TextField fullWidth size="small" select label="Zatrzymaj muzykę" value={s.zatrzymaj_muzyke ? 'true' : 'false'} onChange={(e) => setDraft((prev) => ({ ...prev, szablony_sygnalow: prev.szablony_sygnalow.map((x) => x.id === s.id ? { ...x, zatrzymaj_muzyke: e.target.value === 'true' } : x) }))}>
                      <MenuItem value="true">Tak</MenuItem>
                      <MenuItem value="false">Nie</MenuItem>
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      size="small"
                      select
                      label={s.typ_zdarzenia === 'break' ? 'Playlista na przerwę' : 'Playlista'}
                      value={s.typ_zdarzenia === 'break' ? (s.uruchom_playliste || '') : ''}
                      disabled={s.typ_zdarzenia !== 'break'}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          szablony_sygnalow: prev.szablony_sygnalow.map((x) =>
                            x.id === s.id ? { ...x, uruchom_playliste: e.target.value } : x
                          ),
                        }))
                      }
                    >
                      <MenuItem value="">Brak</MenuItem>
                      {s.typ_zdarzenia === 'break' && playlisty.map((p) => <MenuItem key={p.id} value={p.name}>{p.name}</MenuItem>)}
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <Button color="error" variant="outlined" size="small" onClick={() => usunSzablon(s.id)}>Usuń szablon</Button>
                  </Grid>
                </Grid>
              </Paper>
            ))}
          </CardContent>
        </Card>
      </Panel>

      <Panel value={tab} index={5}>
        <Card>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" sx={{ mb: 1 }}>
              <Typography variant="h6">Typy dnia i zdarzenia</Typography>
              <Button variant="contained" size="small" onClick={dodajTypDnia}>Dodaj typ dnia</Button>
            </Stack>

            <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
              <TextField fullWidth size="small" select label="Wybrany typ dnia" value={wybranyTypDniaId} onChange={(e) => setWybranyTypDniaId(e.target.value)}>
                {draft.typy_dnia.map((t) => <MenuItem key={t.id} value={t.id}>{t.nazwa}</MenuItem>)}
              </TextField>
              {wybranyTypDnia && <Button color="error" variant="outlined" size="small" onClick={() => usunTypDnia(wybranyTypDnia.id)}>Usuń typ</Button>}
            </Stack>

            {wybranyTypDnia && (
              <>
                <TextField fullWidth size="small" label="Nazwa typu dnia" value={wybranyTypDnia.nazwa} onChange={(e) => setDraft((prev) => ({ ...prev, typy_dnia: prev.typy_dnia.map((t) => t.id === wybranyTypDnia.id ? { ...t, nazwa: e.target.value } : t) }))} sx={{ mb: 1 }} />
                <Button variant="outlined" size="small" onClick={dodajZdarzenie} sx={{ mb: 1 }}>Dodaj zdarzenie</Button>

                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Godzina</TableCell>
                        <TableCell>Szablon sygnału</TableCell>
                        <TableCell>Akcje</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {wybranyTypDnia.zdarzenia.map((z) => (
                        <TableRow key={z.id}>
                          <TableCell>
                            <TextField size="small" type="time" value={z.godzina} onChange={(e) => setDraft((prev) => ({ ...prev, typy_dnia: prev.typy_dnia.map((t) => t.id === wybranyTypDnia.id ? { ...t, zdarzenia: t.zdarzenia.map((x) => x.id === z.id ? { ...x, godzina: e.target.value } : x) } : t) }))} />
                          </TableCell>
                          <TableCell>
                            <TextField size="small" select value={z.szablon_id} onChange={(e) => setDraft((prev) => ({ ...prev, typy_dnia: prev.typy_dnia.map((t) => t.id === wybranyTypDnia.id ? { ...t, zdarzenia: t.zdarzenia.map((x) => x.id === z.id ? { ...x, szablon_id: e.target.value } : x) } : t) }))}>
                              {draft.szablony_sygnalow.map((s) => <MenuItem key={s.id} value={s.id}>{s.nazwa}</MenuItem>)}
                            </TextField>
                          </TableCell>
                          <TableCell>
                            <Button color="error" size="small" onClick={() => usunZdarzenie(z.id)}>Usuń</Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
          </CardContent>
        </Card>
      </Panel>

      <Panel value={tab} index={1}>
        <Card>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" sx={{ mb: 1 }}>
              <Typography variant="h6">Kalendarz: plan miesięczny + wyjątki dat</Typography>
              <Button variant="outlined" size="small" onClick={dodajWpisKalendarza}>Dodaj wyjątek daty</Button>
            </Stack>

            <Alert severity="info" sx={{ mb: 2 }}>
              Domyślnie planujesz raz na miesiąc. Wyjątki dat nadpisują plan miesięczny.
            </Alert>

            <Typography variant="subtitle1" sx={{ mb: 1 }}>Wyjątki dat (nadpisują plan miesięczny)</Typography>
            <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Data</TableCell>
                    <TableCell>Typ dnia</TableCell>
                    <TableCell>Profil dźwięków</TableCell>
                    <TableCell>Akcje</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {draft.kalendarz.map((w) => (
                    <TableRow key={w.id}>
                      <TableCell>
                        <TextField size="small" type="date" value={w.data} onChange={(e) => setDraft((prev) => ({ ...prev, kalendarz: prev.kalendarz.map((x) => x.id === w.id ? { ...x, data: e.target.value } : x) }))} />
                      </TableCell>
                      <TableCell>
                        <TextField size="small" select value={w.typ_dnia_id} onChange={(e) => setDraft((prev) => ({ ...prev, kalendarz: prev.kalendarz.map((x) => x.id === w.id ? { ...x, typ_dnia_id: e.target.value } : x) }))}>
                          {draft.typy_dnia.map((t) => <MenuItem key={t.id} value={t.id}>{t.nazwa}</MenuItem>)}
                        </TextField>
                      </TableCell>
                      <TableCell>
                        <TextField size="small" select value={w.profil_dzwiekow} onChange={(e) => setDraft((prev) => ({ ...prev, kalendarz: prev.kalendarz.map((x) => x.id === w.id ? { ...x, profil_dzwiekow: e.target.value } : x) }))}>
                          {profileNames.map((nazwa) => <MenuItem key={nazwa} value={nazwa}>{nazwa}</MenuItem>)}
                        </TextField>
                      </TableCell>
                      <TableCell>
                        <Button color="error" size="small" onClick={() => usunWpisKalendarza(w.id)}>Usuń</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Stack direction="row" justifyContent="space-between" sx={{ mb: 1 }}>
              <Typography variant="subtitle1">Plan miesięczny (domyślny)</Typography>
              <Button variant="contained" size="small" onClick={dodajPlanMiesiaca}>Dodaj plan miesiąca</Button>
            </Stack>
            <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
              <TextField fullWidth size="small" select label="Wybrany plan miesiąca" value={wybranyPlanMiesiacaId} onChange={(e) => setWybranyPlanMiesiacaId(e.target.value)}>
                {draft.plany_miesieczne.map((p) => (
                  <MenuItem key={p.id} value={p.id}>{`${p.miesiac} - ${p.nazwa}`}</MenuItem>
                ))}
              </TextField>
              {wybranyPlanMiesiaca && (
                <Button color="error" variant="outlined" size="small" onClick={() => usunPlanMiesiaca(wybranyPlanMiesiaca.id)}>
                  Usuń plan
                </Button>
              )}
            </Stack>

            {wybranyPlanMiesiaca && (
              <Paper variant="outlined" sx={{ p: 1, mb: 2 }}>
                <Grid container spacing={1}>
                  <Grid item xs={12} md={3}>
                    <TextField
                      fullWidth
                      size="small"
                      type="month"
                      label="Miesiąc"
                      InputLabelProps={{ shrink: true }}
                      value={wybranyPlanMiesiaca.miesiac}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          plany_miesieczne: prev.plany_miesieczne.map((p) =>
                            p.id === wybranyPlanMiesiaca.id ? { ...p, miesiac: e.target.value } : p
                          ),
                        }))
                      }
                    />
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Nazwa planu"
                      value={wybranyPlanMiesiaca.nazwa}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          plany_miesieczne: prev.plany_miesieczne.map((p) =>
                            p.id === wybranyPlanMiesiaca.id ? { ...p, nazwa: e.target.value } : p
                          ),
                        }))
                      }
                    />
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <TextField
                      fullWidth
                      size="small"
                      select
                      label="Typ dnia domyślny"
                      value={wybranyPlanMiesiaca.typ_dnia_id}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          plany_miesieczne: prev.plany_miesieczne.map((p) =>
                            p.id === wybranyPlanMiesiaca.id ? { ...p, typ_dnia_id: e.target.value } : p
                          ),
                        }))
                      }
                    >
                      {draft.typy_dnia.map((t) => <MenuItem key={t.id} value={t.id}>{t.nazwa}</MenuItem>)}
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <TextField
                      fullWidth
                      size="small"
                      select
                      label="Profil dźwięków domyślny"
                      value={wybranyPlanMiesiaca.profil_dzwiekow}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          plany_miesieczne: prev.plany_miesieczne.map((p) =>
                            p.id === wybranyPlanMiesiaca.id ? { ...p, profil_dzwiekow: e.target.value } : p
                          ),
                        }))
                      }
                    >
                      {profileNames.map((nazwa) => <MenuItem key={nazwa} value={nazwa}>{nazwa}</MenuItem>)}
                    </TextField>
                  </Grid>
                </Grid>
              </Paper>
            )}

            <Stack direction="row" justifyContent="space-between" sx={{ mb: 1 }}>
              <Typography variant="h6">Profile dźwięków</Typography>
              <Button variant="outlined" size="small" onClick={dodajProfilDzwiekow}>Dodaj profil</Button>
            </Stack>
            <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Nazwa profilu</TableCell>
                    <TableCell>Akcje</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {draft.mapowania_profili.map((profil) => (
                    <TableRow key={profil.id}>
                      <TableCell>
                        <TextField
                          size="small"
                          fullWidth
                          value={profil.nazwa_profilu}
                          onChange={(e) => {
                            const nowa = e.target.value
                            const stara = profil.nazwa_profilu
                            setDraft((prev) => ({
                              ...prev,
                              mapowania_profili: prev.mapowania_profili.map((m) =>
                                m.id === profil.id ? { ...m, nazwa_profilu: nowa } : m
                              ),
                              plany_miesieczne: prev.plany_miesieczne.map((p) =>
                                p.profil_dzwiekow === stara ? { ...p, profil_dzwiekow: nowa } : p
                              ),
                              kalendarz: prev.kalendarz.map((k) =>
                                k.profil_dzwiekow === stara ? { ...k, profil_dzwiekow: nowa } : k
                              ),
                            }))
                            if (wybranyProfilMapowania === stara) setWybranyProfilMapowania(nowa)
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Button color="error" size="small" onClick={() => usunProfilDzwiekow(profil.id)} disabled={draft.mapowania_profili.length <= 1}>
                          Usuń
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" sx={{ mb: 1 }}>Mapowanie dźwięków dla profilu</Typography>
            <TextField fullWidth size="small" select label="Profil" value={wybranyProfilMapowania} onChange={(e) => setWybranyProfilMapowania(e.target.value)} sx={{ mb: 1 }}>
              {profileNames.map((p) => <MenuItem key={p} value={p}>{p}</MenuItem>)}
            </TextField>

            {activeMapping && (
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Wzorzec</TableCell>
                      <TableCell>Plik docelowy (nazwa lub ścieżka)</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {draft.wzorce_dzwiekow.map((w) => (
                      <TableRow key={`${activeMapping.id}-${w.id}`}>
                        <TableCell><Typography variant="subtitle1">{w.nazwa}</Typography></TableCell>
                        <TableCell>
                          <TextField
                            fullWidth
                            size="small"
                            select
                            value={activeMapping.pliki[w.klucz] || ''}
                            onChange={(e) => setDraft((prev) => ({
                              ...prev,
                              mapowania_profili: prev.mapowania_profili.map((m) =>
                                m.id === activeMapping.id
                                  ? { ...m, pliki: { ...m.pliki, [w.klucz]: e.target.value } }
                                  : m
                              ),
                            }))}
                          >
                            <MenuItem value="">Brak przypisania</MenuItem>
                            {dzwiekiBiblioteki.map((d) => (
                              <MenuItem key={d.id} value={d.name}>
                                {d.name}
                              </MenuItem>
                            ))}
                          </TextField>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </Panel>

      <Panel value={tab} index={3}>
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>Biblioteka dźwięków i playlist</Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ xs: 'stretch', sm: 'center' }} sx={{ mb: 1 }}>
              <Button
                size="small"
                variant="outlined"
                onClick={async () => {
                  try {
                    setBladBiblioteki('')
                    await odswiezBiblioteke('Ręcznie odświeżono informacje o bibliotece.')
                  } catch (err: any) {
                    setBladBiblioteki(err?.response?.data?.detail || 'Nie udało się odświeżyć informacji.')
                  }
                }}
              >
                Aktualizuj informacje
              </Button>
            </Stack>
            {statusBiblioteki && <Alert severity="success" sx={{ mb: 1 }}>{statusBiblioteki}</Alert>}
            {bladBiblioteki && <Alert severity="error" sx={{ mb: 1 }}>{bladBiblioteki}</Alert>}

            <Typography variant="subtitle1" sx={{ mb: 1 }}>Biblioteka dźwięków</Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ mb: 2 }}>
              <Button
                variant="outlined"
                component="label"
              >
                Wgraj dźwięk (WAV/MP3)
                <input
                  hidden
                  type="file"
                  accept=".wav,.mp3"
                  onChange={async (e) => {
                    const file = e.target.files?.[0]
                    if (!file) return
                    const nazwa = window.prompt('Nazwa dźwięku:', file.name.replace(/\.[^/.]+$/, '')) || ''
                    try {
                      setBladBiblioteki('')
                      await wgrajDzwiek(file, nazwa)
                    } catch (err: any) {
                      setBladBiblioteki(err?.response?.data?.detail || 'Nie udało się wgrać dźwięku.')
                    } finally {
                      e.currentTarget.value = ''
                    }
                  }}
                />
              </Button>
            </Stack>

            <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Nazwa</TableCell>
                    <TableCell>Plik</TableCell>
                    <TableCell>Akcje</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dzwiekiBiblioteki.map((d) => (
                    <TableRow key={d.id}>
                      <TableCell>{d.name}</TableCell>
                      <TableCell>{d.file_path?.split('/').pop() || '-'}</TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1}>
                          <Button
                            size="small"
                            variant={odtwarzanyDzwiekId === d.id ? 'contained' : 'outlined'}
                            onClick={() => {
                              if (odtwarzanyDzwiekId === d.id) {
                                zatrzymajOdsluch()
                                return
                              }
                              odsluchajDzwiek(d.id)
                            }}
                          >
                            {odtwarzanyDzwiekId === d.id ? 'Stop' : 'Podsłuch'}
                          </Button>
                          <Button
                            size="small"
                            onClick={async () => {
                              const nowaNazwa = window.prompt('Nowa nazwa dźwięku:', d.name)
                              if (!nowaNazwa || nowaNazwa === d.name) return
                              try {
                                setBladBiblioteki('')
                                await zmienNazweDzwieku(d.id, nowaNazwa)
                              } catch (err: any) {
                                setBladBiblioteki(err?.response?.data?.detail || 'Nie udało się zmienić nazwy dźwięku.')
                              }
                            }}
                          >
                            Zmień nazwę
                          </Button>
                          <Button
                            size="small"
                            color="error"
                            onClick={async () => {
                              if (!window.confirm(`Usunąć dźwięk: ${d.name}?`)) return
                              try {
                                setBladBiblioteki('')
                                await usunDzwiekBiblioteki(d.id)
                              } catch (err: any) {
                                setBladBiblioteki(err?.response?.data?.detail || 'Nie udało się usunąć dźwięku.')
                              }
                            }}
                          >
                            Usuń
                          </Button>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                  {dzwiekiBiblioteki.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={3}>Brak dźwięków w bibliotece.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="subtitle1" sx={{ mb: 1 }}>Playlisty</Typography>
            <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
              <Button
                variant="outlined"
                onClick={async () => {
                  const nazwa = window.prompt('Nazwa nowej playlisty:', '')
                  if (!nazwa?.trim()) return
                  try {
                    setBladBiblioteki('')
                    await dodajPlayliste(nazwa)
                  } catch (err: any) {
                    setBladBiblioteki(err?.response?.data?.detail || 'Nie udało się dodać playlisty.')
                  }
                }}
              >
                Dodaj playlistę
              </Button>
            </Stack>

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Nazwa</TableCell>
                    <TableCell>Akcje</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {playlisty.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell>{p.name}</TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1}>
                          <Button
                            size="small"
                            variant={wybranaPlaylistaId === p.id ? 'contained' : 'outlined'}
                            onClick={async () => {
                              if (wybranaPlaylistaId === p.id) {
                                setWybranaPlaylistaId(null)
                                setUtworyPlaylisty([])
                                return
                              }
                              try {
                                setBladBiblioteki('')
                                setWybranaPlaylistaId(p.id)
                                await zaladujUtworyPlaylisty(p.id)
                              } catch (err: any) {
                                setBladBiblioteki(err?.response?.data?.detail || 'Nie udalo sie pobrac utworow playlisty.')
                              }
                            }}
                          >
                            {wybranaPlaylistaId === p.id ? 'Ukryj utwory' : 'Edytuj utwory'}
                          </Button>
                          <Button
                            size="small"
                            onClick={async () => {
                              const nowaNazwa = window.prompt('Nowa nazwa playlisty:', p.name)
                              if (!nowaNazwa || nowaNazwa === p.name) return
                              try {
                                setBladBiblioteki('')
                                await zmienNazwePlaylisty(p.id, nowaNazwa)
                              } catch (err: any) {
                                setBladBiblioteki(err?.response?.data?.detail || 'Nie udało się zmienić nazwy playlisty.')
                              }
                            }}
                          >
                            Zmień nazwę
                          </Button>
                          <Button
                            size="small"
                            color="error"
                            onClick={async () => {
                              if (!window.confirm(`Usunąć playlistę: ${p.name}?`)) return
                              try {
                                setBladBiblioteki('')
                                await usunPlayliste(p.id)
                              } catch (err: any) {
                                setBladBiblioteki(err?.response?.data?.detail || 'Nie udało się usunąć playlisty.')
                              }
                            }}
                          >
                            Usuń
                          </Button>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                  {playlisty.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={2}>Brak playlist.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            {wybranaPlaylistaId && (
              <Paper variant="outlined" sx={{ mt: 2, p: 1.5 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  Utwory playlisty: {playlisty.find((p) => p.id === wybranaPlaylistaId)?.name || `#${wybranaPlaylistaId}`}
                </Typography>
                <Grid container spacing={1} sx={{ mb: 2 }} alignItems="center">
                  <Grid item xs={12} md={2}>
                    <TextField
                      fullWidth
                      size="small"
                      select
                      label="Zrodlo"
                      value={zrodloUtworu}
                      onChange={(e) => setZrodloUtworu(e.target.value as 'sound' | 'placeholder')}
                    >
                      <MenuItem value="sound">Dzwiek</MenuItem>
                      <MenuItem value="placeholder">Placeholder</MenuItem>
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      size="small"
                      select
                      label={zrodloUtworu === 'sound' ? 'Wybierz dzwiek' : 'Wybierz placeholder'}
                      value={zrodloUtworu === 'sound' ? wybranyDzwiekId : wybranyPlaceholder}
                      onChange={(e) => {
                        if (zrodloUtworu === 'sound') {
                          setWybranyDzwiekId(e.target.value)
                        } else {
                          setWybranyPlaceholder(e.target.value)
                        }
                      }}
                    >
                      <MenuItem value="">-- Wybierz --</MenuItem>
                      {zrodloUtworu === 'sound' && dzwiekiBiblioteki.map((d) => (
                        <MenuItem key={d.id} value={String(d.id)}>
                          {d.name}
                        </MenuItem>
                      ))}
                      {zrodloUtworu === 'placeholder' && placeholderKeys.map((key) => (
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
                      label="Tytul (opcjonalnie)"
                      value={tytulUtworu}
                      onChange={(e) => setTytulUtworu(e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={6} md={2}>
                    <TextField
                      fullWidth
                      size="small"
                      type="number"
                      label="Kolejnosc"
                      value={kolejnoscUtworu}
                      onChange={(e) => setKolejnoscUtworu(e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={6} md={1}>
                    <Button
                      fullWidth
                      variant="contained"
                      onClick={async () => {
                        try {
                          setBladBiblioteki('')
                          await dodajUtworDoPlaylisty()
                        } catch (err: any) {
                          setBladBiblioteki(err?.response?.data?.detail || 'Nie udalo sie dodac utworu do playlisty.')
                        }
                      }}
                      disabled={zrodloUtworu === 'sound' ? !wybranyDzwiekId : !wybranyPlaceholder}
                    >
                      Dodaj
                    </Button>
                  </Grid>
                </Grid>

                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>#</TableCell>
                        <TableCell>Zrodlo</TableCell>
                        <TableCell>Resolved</TableCell>
                        <TableCell>Akcje</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {utworyPlaylisty.map((u, idx) => (
                        <TableRow key={u.id}>
                          <TableCell>{idx + 1}</TableCell>
                          <TableCell>{u.title || (u.placeholder_key ? (placeholderLabels[u.placeholder_key] || u.placeholder_key) : u.file_path)}</TableCell>
                          <TableCell>{u.resolved_name || u.resolved_file_path || '-'}</TableCell>
                          <TableCell>
                            <Button
                              size="small"
                              color="error"
                              onClick={async () => {
                                try {
                                  setBladBiblioteki('')
                                  await usunUtworZPlaylisty(u.id)
                                } catch (err: any) {
                                  setBladBiblioteki(err?.response?.data?.detail || 'Nie udalo sie usunac utworu.')
                                }
                              }}
                            >
                              Usun
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                      {utworyPlaylisty.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={4}>Brak utworow w playliscie.</TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            )}
          </CardContent>
        </Card>
      </Panel>

      <Panel value={tab} index={0}>
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>Podgląd dnia i wykonywania</Typography>
            <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
              <TextField size="small" type="date" label="Data" InputLabelProps={{ shrink: true }} value={podgladData} onChange={(e) => setPodgladData(e.target.value)} />
              <TextField size="small" type="time" label="Godzina" InputLabelProps={{ shrink: true }} value={podgladGodzina} onChange={(e) => setPodgladGodzina(e.target.value)} />
              <Button variant="contained" onClick={zastosujSymulacje}>Pokaż symulację</Button>
            </Stack>

            <Alert severity="info" sx={{ mb: 1 }}>
              Symulacja dla: {symulacjaData} {symulacjaGodzina}
            </Alert>

            {!wpisDnia && <Alert severity="warning" sx={{ mb: 1 }}>Brak wpisu kalendarza dla tej daty.</Alert>}
            {wpisDnia && (
              <Alert severity="info" sx={{ mb: 1 }}>
                Typ dnia: {draft.typy_dnia.find((t) => t.id === wpisDnia.typ_dnia_id)?.nazwa || '-'} | Profil: {wpisDnia.profil_dzwiekow}
              </Alert>
            )}

            {typDniaPodgladu && (
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Godzina</TableCell>
                      <TableCell>Zdarzenie</TableCell>
                      <TableCell>Dzwonek (podstawiony)</TableCell>
                      <TableCell>Zapowiedź (podstawiona)</TableCell>
                      <TableCell>Playlista</TableCell>
                      <TableCell>Stan</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {typDniaPodgladu.zdarzenia
                      .slice()
                      .sort((a, b) => a.godzina.localeCompare(b.godzina))
                      .map((z) => {
                        const s = mapaSzablonow.get(z.szablon_id)
                        if (!s) return null
                        const dzw = mapowanieProfiluPodgladu?.pliki[s.dzwonek_wzorzec] || `(brak mapowania: ${s.dzwonek_wzorzec})`
                        const zap = mapowanieProfiluPodgladu?.pliki[s.zapowiedz_wzorzec] || `(brak mapowania: ${s.zapowiedz_wzorzec})`
                        const aktywne = aktualnieWykonywaneId === z.id
                        return (
                          <TableRow key={z.id} sx={aktywne ? { bgcolor: 'rgba(76, 175, 80, 0.12)' } : undefined}>
                            <TableCell>{z.godzina}</TableCell>
                            <TableCell>{s.nazwa}</TableCell>
                            <TableCell>{dzw}</TableCell>
                            <TableCell>{zap}</TableCell>
                            <TableCell>{s.typ_zdarzenia === 'break' ? (s.uruchom_playliste || '-') : '-'}</TableCell>
                            <TableCell>{aktywne ? 'Wykonywane teraz' : 'Oczekuje / wykonane'}</TableCell>
                          </TableRow>
                        )
                      })}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </Panel>

    </Box>
  )
}

export default BellModelPage



