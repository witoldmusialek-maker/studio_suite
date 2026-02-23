import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Grid,
  IconButton,
  InputAdornment,
  MenuItem,
  Paper,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Groups as GroupsIcon,
  Search as SearchIcon,
  Tv as TvIcon,
} from '@mui/icons-material'
import { api } from '../services/api'
import { Display, Group } from '../types'
import { useAuth } from '../contexts/AuthContext'

type GroupType = 'horizontal' | 'vertical' | 'mixed' | 'single'

type GroupFormData = {
  name: string
  type: GroupType
  floor: string
}

type LayoutTile = {
  display_id: number
  name: string
  x: number
  y: number
  width: number
  height: number
  rotation: 0 | 90 | 180 | 270
}

const defaultFormData: GroupFormData = {
  name: '',
  type: 'single',
  floor: '',
}

const groupTypeOptions: Array<{ value: GroupType; label: string }> = [
  { value: 'single', label: 'Pojedyncza' },
  { value: 'horizontal', label: 'Pozioma' },
  { value: 'vertical', label: 'Pionowa' },
  { value: 'mixed', label: 'Mieszana' },
]

const groupTypeLabel = (type: string) => {
  const found = groupTypeOptions.find((x) => x.value === type)
  return found?.label || type
}

const GroupsPage = () => {
  const { user } = useAuth()
  const [groups, setGroups] = useState<Group[]>([])
  const [displays, setDisplays] = useState<Display[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<'all' | GroupType>('all')
  const [floorOnly, setFloorOnly] = useState('')

  const [openGroupDialog, setOpenGroupDialog] = useState(false)
  const [editingGroup, setEditingGroup] = useState<Group | null>(null)
  const [formData, setFormData] = useState<GroupFormData>(defaultFormData)

  const [openMembersDialog, setOpenMembersDialog] = useState(false)
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null)
  const [selectedDisplayIds, setSelectedDisplayIds] = useState<number[]>([])
  const [openLayoutDialog, setOpenLayoutDialog] = useState(false)
  const [layoutGroup, setLayoutGroup] = useState<Group | null>(null)
  const [layoutTiles, setLayoutTiles] = useState<LayoutTile[]>([])

  useEffect(() => {
    fetchAll()
  }, [])

  const fetchAll = async () => {
    try {
      const [groupsRes, displaysRes] = await Promise.all([
        api.get('/groups'),
        api.get('/displays'),
      ])
      setGroups(groupsRes.data || [])
      setDisplays(displaysRes.data || [])
    } catch (fetchError: any) {
      setError(fetchError?.response?.data?.detail || 'Nie udało się pobrać danych grup.')
    } finally {
      setLoading(false)
    }
  }

  const displaysByGroup = useMemo(() => {
    const map = new Map<number, Display[]>()
    for (const g of groups) map.set(g.id, [])
    for (const d of displays) {
      if (d.group_id && map.has(d.group_id)) {
        map.get(d.group_id)!.push(d)
      }
    }
    return map
  }, [groups, displays])

  const availableFloors = useMemo(() => {
    return Array.from(new Set(groups.map((g) => g.floor).filter(Boolean))) as string[]
  }, [groups])

  const stats = useMemo(() => {
    const assigned = displays.filter((d) => !!d.group_id).length
    const unassigned = displays.length - assigned
    return {
      totalGroups: groups.length,
      assignedDisplays: assigned,
      unassignedDisplays: unassigned,
      floors: new Set(groups.map((g) => g.floor).filter(Boolean)).size,
    }
  }, [groups, displays])

  const filteredGroups = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()

    return groups.filter((group) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        group.name.toLowerCase().includes(normalizedSearch) ||
        (group.floor || '').toLowerCase().includes(normalizedSearch)
      const matchesType = typeFilter === 'all' || group.type === typeFilter
      const matchesFloor = floorOnly.length === 0 || (group.floor || '') === floorOnly
      return matchesSearch && matchesType && matchesFloor
    })
  }, [groups, search, typeFilter, floorOnly])

  const openCreateDialog = () => {
    setEditingGroup(null)
    setFormData(defaultFormData)
    setError('')
    setOpenGroupDialog(true)
  }

  const openEditDialog = (group: Group) => {
    setEditingGroup(group)
    setFormData({
      name: group.name,
      type: group.type as GroupType,
      floor: group.floor || '',
    })
    setError('')
    setOpenGroupDialog(true)
  }

  const saveGroup = async () => {
    setError('')
    try {
      const payload = {
        name: formData.name.trim(),
        type: formData.type,
        floor: formData.floor.trim() || null,
      }

      if (editingGroup) {
        await api.put(`/groups/${editingGroup.id}`, payload)
      } else {
        await api.post('/groups', payload)
      }

      setOpenGroupDialog(false)
      setEditingGroup(null)
      fetchAll()
    } catch (saveError: any) {
      setError(saveError?.response?.data?.detail || 'Nie udało się zapisać grupy.')
    }
  }

  const deleteGroup = async (groupId: number) => {
    if (!window.confirm('Usunąć tę grupę?')) return
    setError('')
    try {
      await api.delete(`/groups/${groupId}`)
      fetchAll()
    } catch (deleteError: any) {
      setError(deleteError?.response?.data?.detail || 'Nie udało się usunąć grupy.')
    }
  }

  const openGroupMembersDialog = (group: Group) => {
    const current = displays.filter((d) => d.group_id === group.id).map((d) => d.id)
    setSelectedGroup(group)
    setSelectedDisplayIds(current)
    setError('')
    setOpenMembersDialog(true)
  }

  const saveGroupMembers = async () => {
    if (!selectedGroup) return
    setError('')

    const currentIds = new Set(displays.filter((d) => d.group_id === selectedGroup.id).map((d) => d.id))
    const nextIds = new Set(selectedDisplayIds)

    const toAdd = [...nextIds].filter((id) => !currentIds.has(id))
    const toRemove = [...currentIds].filter((id) => !nextIds.has(id))

    try {
      for (const displayId of toRemove) {
        await api.delete(`/groups/${selectedGroup.id}/displays/${displayId}`)
      }
      for (const displayId of toAdd) {
        await api.post(`/groups/${selectedGroup.id}/displays/${displayId}`)
      }

      setOpenMembersDialog(false)
      fetchAll()
    } catch (membersError: any) {
      setError(membersError?.response?.data?.detail || 'Nie udało się zaktualizować składu grupy.')
    }
  }

  const normalizeLayoutForGroup = (group: Group): LayoutTile[] => {
    const members = displays.filter((d) => d.group_id === group.id)
    const existingTilesRaw = (group.layout_config as any)?.tiles
    const existingMap = new Map<number, any>(
      Array.isArray(existingTilesRaw)
        ? existingTilesRaw
            .filter((t: any) => Number.isFinite(Number(t?.display_id)))
            .map((t: any) => [Number(t.display_id), t])
        : []
    )

    let nextX = 0
    let nextY = 0
    return members.map((d) => {
      const effectiveWidth = d.orientation === 90 || d.orientation === 270 ? d.resolution_height : d.resolution_width
      const effectiveHeight = d.orientation === 90 || d.orientation === 270 ? d.resolution_width : d.resolution_height
      const existing = existingMap.get(d.id)

      const tile: LayoutTile = {
        display_id: d.id,
        name: d.name,
        x: Number.isFinite(Number(existing?.x)) ? Number(existing.x) : nextX,
        y: Number.isFinite(Number(existing?.y)) ? Number(existing.y) : nextY,
        width: Number.isFinite(Number(existing?.width)) ? Number(existing.width) : effectiveWidth,
        height: Number.isFinite(Number(existing?.height)) ? Number(existing.height) : effectiveHeight,
        rotation: [0, 90, 180, 270].includes(Number(existing?.rotation))
          ? Number(existing.rotation) as 0 | 90 | 180 | 270
          : (d.orientation as 0 | 90 | 180 | 270),
      }

      if (!existing) {
        if (group.type === 'vertical') {
          nextY += tile.height
        } else {
          nextX += tile.width
        }
      }
      return tile
    })
  }

  const openLayoutEditor = (group: Group) => {
    setLayoutGroup(group)
    setLayoutTiles(normalizeLayoutForGroup(group))
    setError('')
    setOpenLayoutDialog(true)
  }

  const applyLayoutPreset = (preset: 'vertical' | 'horizontal') => {
    let nextX = 0
    let nextY = 0
    setLayoutTiles((prev) =>
      prev.map((tile) => {
        const updated = {
          ...tile,
          x: nextX,
          y: nextY,
        }
        if (preset === 'vertical') {
          nextY += tile.height
        } else {
          nextX += tile.width
        }
        return updated
      })
    )
  }

  const saveLayoutConfig = async () => {
    if (!layoutGroup) return
    setError('')
    try {
      await api.put(`/groups/${layoutGroup.id}`, {
        layout_config: {
          mode: 'span',
          tiles: layoutTiles.map((t) => ({
            display_id: t.display_id,
            x: t.x,
            y: t.y,
            width: t.width,
            height: t.height,
            rotation: t.rotation,
          })),
          updated_at: new Date().toISOString(),
        },
      })
      setOpenLayoutDialog(false)
      fetchAll()
    } catch (layoutError: any) {
      setError(layoutError?.response?.data?.detail || 'Nie udało się zapisać układu ściany.')
    }
  }

  const layoutBounds = useMemo(() => {
    if (layoutTiles.length === 0) return { width: 1, height: 1, minX: 0, minY: 0 }
    const minX = Math.min(...layoutTiles.map((t) => t.x))
    const minY = Math.min(...layoutTiles.map((t) => t.y))
    const maxX = Math.max(...layoutTiles.map((t) => t.x + t.width))
    const maxY = Math.max(...layoutTiles.map((t) => t.y + t.height))
    return {
      minX,
      minY,
      width: Math.max(1, maxX - minX),
      height: Math.max(1, maxY - minY),
    }
  }, [layoutTiles])

  if (loading) {
    return <Typography>Ładowanie...</Typography>
  }

  return (
    <Box>
      <Paper
        sx={{
          mb: 2.5,
          p: 2.5,
          borderRadius: 3,
          background: 'linear-gradient(145deg, #f7faff 0%, #ffffff 65%)',
        }}
      >
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 1.5 }}>
          <Box>
            <Typography variant="h4">Grupy wyświetlaczy</Typography>
            <Typography color="text.secondary">Tworzenie grup i zarządzanie przypisaniem urządzeń</Typography>
          </Box>
          {user?.role === 'admin' && (
            <Button variant="contained" startIcon={<AddIcon />} size="large" onClick={openCreateDialog}>
              Dodaj grupę
            </Button>
          )}
        </Stack>

        <Grid container spacing={1.5} sx={{ mb: 1.5 }}>
          <Grid item xs={6} md={3}><Card variant="outlined"><CardContent><Typography variant="body2" color="text.secondary">Grupy</Typography><Typography variant="h5">{stats.totalGroups}</Typography></CardContent></Card></Grid>
          <Grid item xs={6} md={3}><Card variant="outlined"><CardContent><Typography variant="body2" color="text.secondary">Przypisane wyświetlacze</Typography><Typography variant="h5">{stats.assignedDisplays}</Typography></CardContent></Card></Grid>
          <Grid item xs={6} md={3}><Card variant="outlined"><CardContent><Typography variant="body2" color="text.secondary">Nieprzypisane</Typography><Typography variant="h5">{stats.unassignedDisplays}</Typography></CardContent></Card></Grid>
          <Grid item xs={6} md={3}><Card variant="outlined"><CardContent><Typography variant="body2" color="text.secondary">Piętra</Typography><Typography variant="h5">{stats.floors}</Typography></CardContent></Card></Grid>
        </Grid>

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
          <TextField
            fullWidth
            size="small"
            placeholder="Szukaj po nazwie lub piętrze..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
          <TextField
            select
            size="small"
            label="Typ"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as 'all' | GroupType)}
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="all">Wszystkie</MenuItem>
            {groupTypeOptions.map((type) => (
              <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>
            ))}
          </TextField>
          <TextField
            select
            size="small"
            label="Piętro"
            value={floorOnly}
            onChange={(e) => setFloorOnly(e.target.value)}
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="">Wszystkie</MenuItem>
            {availableFloors.map((floor) => (
              <MenuItem key={floor} value={floor}>{floor}</MenuItem>
            ))}
          </TextField>
        </Stack>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2}>
        {filteredGroups.map((group) => {
          const members = displaysByGroup.get(group.id) || []
          return (
            <Grid item xs={12} md={6} lg={4} key={group.id}>
              <Card sx={{ height: '100%', borderRadius: 3, border: '1px solid', borderColor: 'divider' }}>
                <CardContent>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                    <Typography variant="h6">{group.name}</Typography>
                    <Chip size="small" label={groupTypeLabel(group.type)} />
                  </Stack>

                  <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                    <Chip size="small" variant="outlined" label={`ID: ${group.id}`} />
                    <Chip size="small" variant="outlined" label={`Piętro: ${group.floor || '-'}`} />
                    {Array.isArray((group.layout_config as any)?.tiles) && (group.layout_config as any).tiles.length > 0 && (
                      <Chip size="small" color="info" variant="outlined" label="Układ ściany" />
                    )}
                  </Stack>

                  <Paper variant="outlined" sx={{ p: 1.2, borderRadius: 2, mb: 1.2 }}>
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.8 }}>
                      <GroupsIcon fontSize="small" />
                      <Typography variant="subtitle2">Członkowie grupy</Typography>
                    </Stack>
                    {members.length === 0 ? (
                      <Typography variant="body2" color="text.secondary">Brak przypisanych wyświetlaczy</Typography>
                    ) : (
                      <Stack direction="row" spacing={0.8} useFlexGap flexWrap="wrap">
                        {members.slice(0, 4).map((m) => (
                          <Chip key={m.id} size="small" icon={<TvIcon />} label={m.name} />
                        ))}
                        {members.length > 4 && <Chip size="small" label={`+${members.length - 4}`} />}
                      </Stack>
                    )}
                  </Paper>

                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Stack direction="row" spacing={1}>
                      <Button size="small" variant="outlined" onClick={() => openGroupMembersDialog(group)} disabled={user?.role !== 'admin'}>
                        Wyświetlacze
                      </Button>
                      <Button size="small" variant="outlined" onClick={() => openLayoutEditor(group)} disabled={user?.role !== 'admin'}>
                        Układ
                      </Button>
                    </Stack>
                    {user?.role === 'admin' && (
                      <Box>
                        <Tooltip title="Edytuj grupę">
                          <IconButton size="small" onClick={() => openEditDialog(group)}>
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Usuń grupę">
                          <IconButton size="small" color="error" onClick={() => deleteGroup(group.id)}>
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          )
        })}
      </Grid>

      {filteredGroups.length === 0 && (
        <Paper sx={{ textAlign: 'center', mt: 3, p: 4, borderRadius: 3 }}>
          <Typography variant="h6" color="text.secondary">Brak grup dla wybranych filtrów</Typography>
        </Paper>
      )}

      <Dialog open={openGroupDialog} onClose={() => setOpenGroupDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingGroup ? 'Edytuj grupę' : 'Nowa grupa'}</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Nazwa"
            margin="normal"
            value={formData.name}
            onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
          />
          <TextField
            fullWidth
            select
            label="Typ grupy"
            margin="normal"
            value={formData.type}
            onChange={(e) => setFormData((prev) => ({ ...prev, type: e.target.value as GroupType }))}
          >
            {groupTypeOptions.map((option) => (
              <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>
            ))}
          </TextField>
          <TextField
            fullWidth
            label="Piętro"
            margin="normal"
            value={formData.floor}
            onChange={(e) => setFormData((prev) => ({ ...prev, floor: e.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenGroupDialog(false)}>Anuluj</Button>
          <Button variant="contained" onClick={saveGroup}>Zapisz</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openMembersDialog} onClose={() => setOpenMembersDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Skład grupy: {selectedGroup?.name || '-'}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Możesz przypisać tylko wyświetlacze nieprzypisane lub już należące do tej grupy.
          </Typography>

          <Stack spacing={0.5}>
            {displays.map((display) => {
              const inThisGroup = selectedGroup ? display.group_id === selectedGroup.id : false
              const assignedToOtherGroup = !!display.group_id && !inThisGroup
              const checked = selectedDisplayIds.includes(display.id)

              return (
                <FormControlLabel
                  key={display.id}
                  control={(
                    <Switch
                      checked={checked}
                      disabled={assignedToOtherGroup || user?.role !== 'admin'}
                      onChange={(e) => {
                        setSelectedDisplayIds((prev) => {
                          if (e.target.checked) return [...prev, display.id]
                          return prev.filter((id) => id !== display.id)
                        })
                      }}
                    />
                  )}
                  label={
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography>{display.name}</Typography>
                      {display.group_id && !inThisGroup && (
                        <Chip size="small" label={`W grupie #${display.group_id}`} />
                      )}
                    </Stack>
                  }
                />
              )
            })}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenMembersDialog(false)}>Anuluj</Button>
          <Button variant="contained" onClick={saveGroupMembers} disabled={user?.role !== 'admin'}>
            Zapisz skład
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openLayoutDialog} onClose={() => setOpenLayoutDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Układ ściany: {layoutGroup?.name || '-'}</DialogTitle>
        <DialogContent>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} sx={{ mb: 1.5 }}>
            <Button variant="outlined" size="small" onClick={() => applyLayoutPreset('vertical')}>
              Preset: pionowo
            </Button>
            <Button variant="outlined" size="small" onClick={() => applyLayoutPreset('horizontal')}>
              Preset: poziomo
            </Button>
          </Stack>

          <Paper variant="outlined" sx={{ p: 1.5, mb: 1.5, borderRadius: 2 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Podgląd canvasu</Typography>
            <Box sx={{ position: 'relative', width: '100%', height: 240, bgcolor: '#f6f8fc', borderRadius: 2, overflow: 'hidden' }}>
              {layoutTiles.map((tile) => {
                const scaleX = 760 / layoutBounds.width
                const scaleY = 220 / layoutBounds.height
                const scale = Math.min(scaleX, scaleY)
                const left = (tile.x - layoutBounds.minX) * scale + 8
                const top = (tile.y - layoutBounds.minY) * scale + 8
                const width = Math.max(24, tile.width * scale)
                const height = Math.max(24, tile.height * scale)
                return (
                  <Box
                    key={tile.display_id}
                    sx={{
                      position: 'absolute',
                      left,
                      top,
                      width,
                      height,
                      border: '1px solid #5b7cfa',
                      bgcolor: 'rgba(91,124,250,0.12)',
                      borderRadius: 1,
                      p: 0.3,
                      overflow: 'hidden',
                    }}
                  >
                    <Typography variant="caption" sx={{ fontSize: 10, fontWeight: 700, lineHeight: 1 }}>
                      {tile.name}
                    </Typography>
                  </Box>
                )
              })}
            </Box>
          </Paper>

          <Stack spacing={1}>
            {layoutTiles.map((tile) => (
              <Paper key={tile.display_id} variant="outlined" sx={{ p: 1, borderRadius: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>{tile.name}</Typography>
                <Grid container spacing={1}>
                  <Grid item xs={6} md={2}>
                    <TextField
                      fullWidth
                      size="small"
                      type="number"
                      label="X"
                      value={tile.x}
                      onChange={(e) => setLayoutTiles((prev) => prev.map((t) => (t.display_id === tile.display_id ? { ...t, x: Number(e.target.value || 0) } : t)))}
                    />
                  </Grid>
                  <Grid item xs={6} md={2}>
                    <TextField
                      fullWidth
                      size="small"
                      type="number"
                      label="Y"
                      value={tile.y}
                      onChange={(e) => setLayoutTiles((prev) => prev.map((t) => (t.display_id === tile.display_id ? { ...t, y: Number(e.target.value || 0) } : t)))}
                    />
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <TextField
                      fullWidth
                      size="small"
                      type="number"
                      label="Szerokość"
                      value={tile.width}
                      onChange={(e) => setLayoutTiles((prev) => prev.map((t) => (t.display_id === tile.display_id ? { ...t, width: Math.max(1, Number(e.target.value || 1)) } : t)))}
                    />
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <TextField
                      fullWidth
                      size="small"
                      type="number"
                      label="Wysokość"
                      value={tile.height}
                      onChange={(e) => setLayoutTiles((prev) => prev.map((t) => (t.display_id === tile.display_id ? { ...t, height: Math.max(1, Number(e.target.value || 1)) } : t)))}
                    />
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      fullWidth
                      size="small"
                      select
                      label="Rotacja"
                      value={tile.rotation}
                      onChange={(e) => setLayoutTiles((prev) => prev.map((t) => (t.display_id === tile.display_id ? { ...t, rotation: Number(e.target.value) as 0 | 90 | 180 | 270 } : t)))}
                    >
                      <MenuItem value={0}>0°</MenuItem>
                      <MenuItem value={90}>90°</MenuItem>
                      <MenuItem value={180}>180°</MenuItem>
                      <MenuItem value={270}>270°</MenuItem>
                    </TextField>
                  </Grid>
                </Grid>
              </Paper>
            ))}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenLayoutDialog(false)}>Anuluj</Button>
          <Button variant="contained" onClick={saveLayoutConfig} disabled={user?.role !== 'admin' || !layoutGroup}>
            Zapisz układ
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default GroupsPage
