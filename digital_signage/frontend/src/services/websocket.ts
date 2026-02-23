import { io, Socket } from 'socket.io-client'

let socket: Socket | null = null

const isLanHost = (host: string): boolean => {
  const h = host.toLowerCase()
  return (
    h === 'localhost' ||
    h === '127.0.0.1' ||
    h.startsWith('192.168.') ||
    h.startsWith('10.') ||
    /^172\.(1[6-9]|2\d|3[0-1])\./.test(h)
  )
}

export const connectWebSocket = (): Socket | null => {
  if (!isLanHost(window.location.hostname)) {
    return null
  }

  if (!socket) {
    const token = localStorage.getItem('token')
    const explicitUrl = import.meta.env.VITE_WS_URL as string | undefined
    const isDevPort = ['3000', '5173', '5174', '5175'].includes(window.location.port)
    const backendUrl = `${window.location.protocol}//${window.location.hostname}:8000`
    const wsUrl = explicitUrl || (isDevPort ? backendUrl : window.location.origin)

    socket = io(wsUrl, {
      auth: {
        token,
      },
      transports: ['websocket'],
    })
  }
  return socket
}

export const disconnectWebSocket = () => {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}

export const getSocket = (): Socket | null => {
  return socket
}
