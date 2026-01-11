import { io, Socket } from 'socket.io-client'

let socket: Socket | null = null

export const connectWebSocket = (): Socket => {
  if (!socket) {
    const token = localStorage.getItem('token')
    socket = io('http://localhost:8000', {
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



