# CONTINUE 
 
## Current State 
- Source repo: witoldmusialek-maker/digital_signage (private) 
- Dev server: 192.168.200.116 
- Deploy path: ~/projects/digital_signage_repo/digital_signage 
- URL: https://dev.witold.ovh/ 
- API: /api/v1 (frontend uses relative API_URL) 
 
## Standard Deploy 
`ash 
cd ~/projects/digital_signage_repo 
git pull origin master 
cd digital_signage 
docker compose up -d --build 
docker compose ps 
` 
 
## Quick Diagnostics 
`ash 
docker compose logs backend --tail 80 
docker compose logs frontend --tail 80 
` 
 
## Notes 
- Websocket (socket.io) is LAN-only. 
- On dev.witold.ovh warnings are expected if backend has no socket endpoint.
