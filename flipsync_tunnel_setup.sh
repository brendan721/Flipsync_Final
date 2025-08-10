
# FlipSync Cloudflare Tunnel Configuration
# Using separate tunnel token for complete isolation from proxy.equipment project

FLIPSYNC_TUNNEL_TOKEN='eyJhIjoiODFhZTdiOTUxN2Q2NWM5MmEyMjdlNWUwYzVkNTljN2YiLCJ0IjoiNjc5YmRhNDQtYjcyOC00N2IyLWEwZjAtNzIxYzAxMDU4M2JmIiwicyI6Ik5UYzVOREJqWm1RdE1qazJaQzAwT1dReUxXSXdOamt0WkdFNE1UUXhNRGhsTmpjeCJ9'

echo '✅ FlipSync tunnel token configured'
echo 'This will create:'
echo '  - proxmox.flipsyncai.com (SSH access)'
echo '  - app.flipsyncai.com (FlipSync application)'
echo '  - api.flipsyncai.com (FlipSync API)'
echo ''
echo 'Benefits:'
echo '  ✅ Complete separation from proxy.equipment project'
echo '  ✅ Proper FlipSync branding'
echo '  ✅ No interference with existing infrastructure'
echo '  ✅ Scalable subdomain structure'

