import { useEffect, useState } from 'react'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import { api } from '../services/api'
import { Group } from '../types'

const GroupsPage = () => {
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchGroups()
  }, [])

  const fetchGroups = async () => {
    try {
      const response = await api.get('/groups')
      setGroups(response.data || [])
    } catch (error) {
      console.error('Blad pobierania grup:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <Typography>Ladowanie...</Typography>
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Grupy
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Nazwa</TableCell>
              <TableCell>Typ</TableCell>
              <TableCell>Pietro</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {groups.map((group) => (
              <TableRow key={group.id}>
                <TableCell>{group.id}</TableCell>
                <TableCell>{group.name}</TableCell>
                <TableCell>{group.type}</TableCell>
                <TableCell>{group.floor || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}

export default GroupsPage
