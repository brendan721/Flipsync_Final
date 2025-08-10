# FlipSync 4+1 Architecture Testing Frontend

A comprehensive React-based testing interface for the FlipSync 4+1 agentic system deployed on production droplet 174.138.77.110.

## 🎯 Purpose

This frontend application serves as a testing and monitoring interface for the FlipSync 4+1 architecture, allowing developers and stakeholders to:

- Monitor system health and agent status in real-time
- Test autonomous agent functionality
- View agent decisions and compliance metrics
- Interact with the conversational chat interface
- Monitor WebSocket connections and real-time updates

## 🏗️ Architecture Integration

The frontend integrates with the production FlipSync 4+1 architecture:

- **4 Autonomous Agents**: Market, Content, Executive, Logistics
- **1 Conversational Interface**: Strategic Chat Service with Gemini
- **Real-time WebSocket**: `/ws/monitoring` for public live updates (default)
  - For authenticated streams use `/ws/flipsync` (requires JWT) or 4+1 WS under `/api/v1/.../ws/*`
- **REST API**: 266+ endpoints for comprehensive system interaction

## 🚀 Quick Start

### Prerequisites

- Node.js 16+ and npm
- Access to production backend at 174.138.77.110:8000

### Installation & Setup

```bash
# Install dependencies
npm install

# Start development server
npm start

# The app will open at http://localhost:3000
# API requests are proxied to production backend
```

### Verify Connectivity

```bash
# Run API connectivity test
node test-api-connectivity.js
```

## 📊 Key Features

### System Status Dashboard
- **Health Monitoring**: Real-time system health checks
- **4+1 Agent Status**: Monitor all 10 agents (9 autonomous + 1 conversational)
- **Decision Tracking**: View agent decisions with compliance metrics
- **Performance Metrics**: Response times and system performance

### Agent Testing Interface
- **Individual Agent Testing**: Trigger specific agents with test payloads
- **Response Time Monitoring**: Track agent performance
- **Real-time Logs**: WebSocket-based agent activity monitoring
- **Test Result History**: Persistent test result tracking

### WebSocket Integration
- **Real-time Updates**: Live agent status and decision updates
- **Connection Monitoring**: WebSocket health and reconnection handling
- **Message Logging**: Comprehensive WebSocket message tracking

## 🔧 Configuration

### API Endpoints (Confirmed Working)

- **Health**: `/api/v1/health`
- **4+1 Agents Status**: `/api/v1/agents/4plus1/status`
- **Decisions (paginated)**: `/api/v1/decisions/4plus1/?limit=5`
- **Public WebSocket (no auth)**: `/ws/monitoring`
- **Authenticated WS**: `/ws/flipsync` (query ?token=...) and `/api/v1/agents/4plus1/ws/status`

### Environment Configuration

The app automatically detects environment:
- **Development**: Proxies API calls to production backend
- **Production**: Direct connection to backend

### Authentication

Authentication is optional for testing purposes. The app will:
- Attempt authentication if tokens are available
- Fall back to test mode if auth endpoints are unavailable
- Allow full functionality without authentication

## 🧪 Testing

### Manual Testing
1. Open http://localhost:3000
2. Navigate through dashboard components
3. Test agent triggers in Agent Tester
4. Monitor real-time updates in System Status

### Automated Testing
```bash
# API connectivity test
node test-api-connectivity.js

# Expected output: 4/4 tests passed
```

## 📁 Project Structure

```
testing-frontend/
├── src/
│   ├── components/          # React components
│   │   ├── Dashboard.js     # Main dashboard
│   │   ├── SystemStatus.js  # System monitoring
│   │   └── AgentTester.js   # Agent testing interface
│   ├── services/           # API and WebSocket services
│   │   ├── api.js          # REST API client
│   │   └── websocket.js    # WebSocket client
│   └── App.js              # Main application
├── package.json            # Dependencies and proxy config
└── test-api-connectivity.js # API test script
```

## 🔍 Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Verify production backend is running on 174.138.77.110:8000
   - Check proxy configuration in package.json

2. **WebSocket Connection Failed**
   - WebSocket connects directly to production (bypasses proxy)
   - Verify `/ws/flipsync` endpoint is available

3. **Authentication Errors**
   - App runs in test mode if auth endpoints unavailable
   - Check browser console for detailed error messages

### Debug Mode

Enable detailed logging by opening browser console:
- API requests/responses are logged
- WebSocket messages are logged
- Component state changes are logged

## 🎯 Production Deployment Status

✅ **Backend Status**: Fully operational on 174.138.77.110:8000
✅ **4+1 Architecture**: 10 agents active (9 autonomous + 1 conversational)
✅ **Database**: 4 decisions recorded, full schema operational
✅ **External Services**: Qdrant, Redis, Gemini all connected
✅ **API Endpoints**: 266 endpoints available
✅ **WebSocket**: Real-time communication active

## 📞 Support

For issues or questions:
1. Check browser console for error messages
2. Run `node test-api-connectivity.js` to verify backend connectivity
3. Verify production backend status at http://174.138.77.110:8000/api/v1/health
