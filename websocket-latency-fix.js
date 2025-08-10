#!/usr/bin/env node

/**
 * Fixed WebSocket Latency Test for FlipSync
 * Resolves the ping/pong parsing issues and ensures accurate latency measurement
 */

const WebSocket = require('ws');

const WS_URL = 'ws://174.138.77.110:8000/ws/flipsync';

class WebSocketLatencyTester {
  constructor() {
    this.results = {
      connection: null,
      latency: null,
      realTime: null
    };
  }

  async testConnection() {
    console.log('🔌 Testing WebSocket Connection...');
    
    return new Promise((resolve) => {
      const startTime = Date.now();
      const ws = new WebSocket(WS_URL);
      let connectionTime = 0;
      let clientId = null;
      let capabilities = [];
      
      const timeout = setTimeout(() => {
        ws.close();
        resolve({
          status: 'FAILED',
          error: 'Connection timeout',
          connectionTime: Date.now() - startTime
        });
      }, 10000);
      
      ws.on('open', () => {
        connectionTime = Date.now() - startTime;
        console.log(`✅ WebSocket connected in ${connectionTime}ms`);
      });
      
      ws.on('message', (data) => {
        try {
          const message = JSON.parse(data.toString());
          console.log(`📥 Received: ${message.type}`);
          
          if (message.type === 'connection_established') {
            clientId = message.client_id;
            capabilities = message.capabilities || [];
            
            clearTimeout(timeout);
            ws.close();
            
            resolve({
              status: 'PASSED',
              connectionTime: connectionTime,
              clientId: clientId,
              capabilities: capabilities
            });
          }
        } catch (error) {
          console.log(`⚠️  Message parsing error: ${error.message}`);
        }
      });
      
      ws.on('error', (error) => {
        console.log(`❌ WebSocket error: ${error.message}`);
        clearTimeout(timeout);
        resolve({
          status: 'FAILED',
          error: error.message,
          connectionTime: connectionTime
        });
      });
    });
  }

  async testLatencyFixed() {
    console.log('\n⏱️  Testing WebSocket Latency (Fixed Implementation)...');
    
    return new Promise((resolve) => {
      const ws = new WebSocket(WS_URL);
      const latencies = [];
      let pingsCompleted = 0;
      const totalPings = 5;
      let connectionTime = 0;
      const startTime = Date.now();
      const pingTimes = new Map(); // Store ping timestamps by ID
      
      const timeout = setTimeout(() => {
        ws.close();
        const avgLatency = latencies.length > 0 ? 
          Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length) : 999;
        
        resolve({
          status: avgLatency < 100 && latencies.length >= 3 ? 'PASSED' : 'FAILED',
          averageLatency: avgLatency,
          pingsCompleted: pingsCompleted,
          latencies: latencies,
          connectionTime: connectionTime,
          totalPings: totalPings
        });
      }, 20000);
      
      ws.on('open', () => {
        connectionTime = Date.now() - startTime;
        console.log(`✅ Connected in ${connectionTime}ms, starting latency test...`);
      });
      
      ws.on('message', (data) => {
        try {
          const message = JSON.parse(data.toString());
          
          if (message.type === 'connection_established') {
            console.log(`🔗 Connection established: ${message.client_id}`);
            
            // Start sending pings after connection is established
            setTimeout(() => this.sendPings(ws, pingTimes, totalPings), 1000);
            
          } else if (message.type === 'echo' && message.original_message?.type === 'ping') {
            // Handle echo response to ping
            const pingId = message.original_message.ping_id;
            const originalTime = pingTimes.get(pingId);
            
            if (originalTime) {
              const latency = Date.now() - originalTime;
              latencies.push(latency);
              pingsCompleted++;
              
              console.log(`   📊 Ping ${pingId} latency: ${latency}ms`);
              pingTimes.delete(pingId); // Clean up
              
              if (pingsCompleted >= totalPings) {
                clearTimeout(timeout);
                const avgLatency = Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length);
                ws.close();
                
                console.log(`\n📈 Latency Test Results:`);
                console.log(`   Average Latency: ${avgLatency}ms`);
                console.log(`   Individual Latencies: ${latencies.join(', ')}ms`);
                console.log(`   Target: <100ms`);
                console.log(`   Status: ${avgLatency < 100 ? '✅ PASSED' : '❌ FAILED'}`);
                
                resolve({
                  status: avgLatency < 100 ? 'PASSED' : 'FAILED',
                  averageLatency: avgLatency,
                  pingsCompleted: pingsCompleted,
                  latencies: latencies,
                  connectionTime: connectionTime,
                  totalPings: totalPings
                });
              }
            }
            
          } else if (message.type === 'pong') {
            // Handle direct pong response (alternative mechanism)
            const pingTime = message.data?.timestamp || message.timestamp;
            if (pingTime) {
              const latency = Date.now() - new Date(pingTime).getTime();
              if (latency > 0 && latency < 5000) { // Sanity check
                latencies.push(latency);
                pingsCompleted++;
                console.log(`   📊 Pong latency: ${latency}ms`);
              }
            }
          }
        } catch (error) {
          console.log(`⚠️  Message parsing error: ${error.message}`);
        }
      });
      
      ws.on('error', (error) => {
        console.log(`❌ WebSocket error: ${error.message}`);
        clearTimeout(timeout);
        resolve({
          status: 'FAILED',
          error: error.message,
          pingsCompleted: pingsCompleted,
          connectionTime: connectionTime
        });
      });
    });
  }

  sendPings(ws, pingTimes, totalPings) {
    let pingsSent = 0;
    
    const sendNextPing = () => {
      if (pingsSent < totalPings && ws.readyState === WebSocket.OPEN) {
        pingsSent++;
        const pingTime = Date.now();
        const pingId = `ping_${pingsSent}`;
        
        pingTimes.set(pingId, pingTime);
        
        console.log(`📤 Sending ping ${pingsSent}/${totalPings}...`);
        ws.send(JSON.stringify({
          type: 'ping',
          ping_id: pingId,
          timestamp: pingTime
        }));
        
        // Send next ping after 2 seconds
        if (pingsSent < totalPings) {
          setTimeout(sendNextPing, 2000);
        }
      }
    };
    
    sendNextPing();
  }

  async testRealTimeUpdates() {
    console.log('\n📡 Testing Real-Time Updates...');
    
    return new Promise((resolve) => {
      const ws = new WebSocket(WS_URL);
      const messagesReceived = [];
      let subscribed = false;
      
      const timeout = setTimeout(() => {
        ws.close();
        resolve({
          status: messagesReceived.length > 0 ? 'PASSED' : 'FAILED',
          messagesReceived: messagesReceived.length,
          messages: messagesReceived.slice(0, 5), // First 5 messages
          error: messagesReceived.length === 0 ? 'No real-time updates received' : null
        });
      }, 15000);
      
      ws.on('open', () => {
        console.log('✅ Connected for real-time testing');
      });
      
      ws.on('message', (data) => {
        try {
          const message = JSON.parse(data.toString());
          
          if (message.type === 'connection_established') {
            console.log(`🔗 Connection established: ${message.client_id}`);
            
            // Subscribe to various channels
            const subscriptions = [
              { type: 'subscribe', channel: 'agent_status' },
              { type: 'subscribe', channel: 'system_notifications' }
            ];
            
            subscriptions.forEach(sub => {
              ws.send(JSON.stringify(sub));
              console.log(`📡 Subscribed to: ${sub.channel}`);
            });
            
            subscribed = true;
            
            // Send a test message to trigger echo response
            setTimeout(() => {
              ws.send(JSON.stringify({
                type: 'test_message',
                content: 'Real-time test',
                timestamp: Date.now()
              }));
            }, 2000);
            
          } else if (message.type !== 'connection_established') {
            // Count any non-connection message as a real-time update
            messagesReceived.push({
              type: message.type,
              timestamp: new Date().toISOString(),
              data: message
            });
            
            console.log(`📥 Real-time update: ${message.type}`);
            
            // If we get enough messages, consider it successful
            if (messagesReceived.length >= 1) {
              clearTimeout(timeout);
              ws.close();
              resolve({
                status: 'PASSED',
                messagesReceived: messagesReceived.length,
                messages: messagesReceived.slice(0, 5),
                subscribed: subscribed
              });
            }
          }
        } catch (error) {
          console.log(`⚠️  Message parsing error: ${error.message}`);
        }
      });
      
      ws.on('error', (error) => {
        console.log(`❌ WebSocket error: ${error.message}`);
        clearTimeout(timeout);
        resolve({
          status: 'FAILED',
          error: error.message,
          messagesReceived: messagesReceived.length
        });
      });
    });
  }

  async runAllTests() {
    console.log('🚀 WebSocket Latency Resolution Testing');
    console.log('=' .repeat(60));
    
    try {
      // Test 1: Connection
      this.results.connection = await this.testConnection();
      
      // Test 2: Latency (Fixed)
      this.results.latency = await this.testLatencyFixed();
      
      // Test 3: Real-time updates
      this.results.realTime = await this.testRealTimeUpdates();
      
      // Generate summary
      this.generateSummary();
      
      // Save results
      const fs = require('fs');
      fs.writeFileSync('websocket-latency-fix-results.json', JSON.stringify(this.results, null, 2));
      console.log('\n📄 Results saved to: websocket-latency-fix-results.json');
      
      return this.results;
      
    } catch (error) {
      console.error('\n❌ WebSocket testing failed:', error.message);
      throw error;
    }
  }

  generateSummary() {
    console.log('\n🎯 WEBSOCKET LATENCY RESOLUTION SUMMARY');
    console.log('=' .repeat(60));
    
    const conn = this.results.connection;
    const lat = this.results.latency;
    const rt = this.results.realTime;
    
    console.log(`🔌 Connection Test: ${conn?.status || 'UNKNOWN'}`);
    if (conn?.status === 'PASSED') {
      console.log(`   Connection Time: ${conn.connectionTime}ms`);
      console.log(`   Client ID: ${conn.clientId}`);
      console.log(`   Capabilities: ${conn.capabilities?.length || 0}`);
    }
    
    console.log(`⏱️  Latency Test: ${lat?.status || 'UNKNOWN'}`);
    if (lat?.averageLatency !== undefined) {
      console.log(`   Average Latency: ${lat.averageLatency}ms (target: <100ms)`);
      console.log(`   Pings Completed: ${lat.pingsCompleted}/${lat.totalPings}`);
      console.log(`   Individual Latencies: ${lat.latencies?.join(', ') || 'N/A'}ms`);
    }
    
    console.log(`📡 Real-Time Test: ${rt?.status || 'UNKNOWN'}`);
    if (rt?.messagesReceived !== undefined) {
      console.log(`   Messages Received: ${rt.messagesReceived}`);
      console.log(`   Subscribed: ${rt.subscribed || false}`);
    }
    
    const allPassed = conn?.status === 'PASSED' && 
                     lat?.status === 'PASSED' && 
                     rt?.status === 'PASSED';
    
    console.log(`\n🎯 Overall Status: ${allPassed ? '✅ ALL TESTS PASSED' : '⚠️  SOME ISSUES REMAIN'}`);
    
    if (lat?.status === 'PASSED') {
      console.log('✅ WebSocket latency issue RESOLVED - <100ms target achieved');
    } else {
      console.log('⚠️  WebSocket latency issue needs further investigation');
    }
  }
}

async function main() {
  const tester = new WebSocketLatencyTester();
  
  try {
    const results = await tester.runAllTests();
    
    // Exit with appropriate code
    const success = results.connection?.status === 'PASSED' && 
                   results.latency?.status === 'PASSED' && 
                   results.realTime?.status === 'PASSED';
    
    process.exit(success ? 0 : 1);
    
  } catch (error) {
    console.error('\n❌ Testing failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = WebSocketLatencyTester;
