#!/usr/bin/env node

/**
 * Dedicated WebSocket Latency Test for FlipSync
 * Tests WebSocket performance and real-time capabilities
 */

const WebSocket = require('ws');

const WS_URL = 'ws://174.138.77.110:8000/ws/flipsync';

async function testWebSocketLatency() {
  console.log('🔌 Testing WebSocket Latency Performance...');
  
  return new Promise((resolve) => {
    const ws = new WebSocket(WS_URL);
    const latencies = [];
    let pingsCompleted = 0;
    const totalPings = 5;
    let connectionTime = 0;
    const startTime = Date.now();
    
    const timeout = setTimeout(() => {
      ws.close();
      const avgLatency = latencies.length > 0 ? 
        Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length) : 999;
      
      resolve({
        status: avgLatency < 100 ? 'PASSED' : 'FAILED',
        averageLatency: avgLatency,
        pingsCompleted: pingsCompleted,
        latencies: latencies,
        connectionTime: connectionTime
      });
    }, 15000);
    
    ws.on('open', () => {
      connectionTime = Date.now() - startTime;
      console.log(`✅ WebSocket connected in ${connectionTime}ms`);
      
      // Send ping messages to test latency
      const sendPing = () => {
        if (pingsCompleted < totalPings) {
          const pingTime = Date.now();
          console.log(`📤 Sending ping ${pingsCompleted + 1}/${totalPings}...`);
          ws.send(JSON.stringify({
            type: 'ping',
            timestamp: pingTime,
            ping_id: pingsCompleted + 1
          }));
          
          setTimeout(sendPing, 2000); // Send ping every 2 seconds
        }
      };
      sendPing();
    });
    
    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data.toString());
        console.log(`📥 Received message: ${message.type}`);
        
        if (message.type === 'echo' && message.original_message?.type === 'ping') {
          const originalTime = message.original_message.timestamp;
          if (originalTime) {
            const latency = Date.now() - originalTime;
            latencies.push(latency);
            pingsCompleted++;
            
            console.log(`   ⏱️  Ping ${message.original_message.ping_id} latency: ${latency}ms`);
            
            if (pingsCompleted >= totalPings) {
              clearTimeout(timeout);
              const avgLatency = Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length);
              ws.close();
              
              console.log(`\n📊 Latency Test Results:`);
              console.log(`   Average Latency: ${avgLatency}ms`);
              console.log(`   Individual Latencies: ${latencies.join(', ')}ms`);
              console.log(`   Target: <100ms`);
              console.log(`   Status: ${avgLatency < 100 ? '✅ PASSED' : '❌ FAILED'}`);
              
              resolve({
                status: avgLatency < 100 ? 'PASSED' : 'FAILED',
                averageLatency: avgLatency,
                pingsCompleted: pingsCompleted,
                latencies: latencies,
                connectionTime: connectionTime
              });
            }
          }
        } else if (message.type === 'connection_established') {
          console.log(`✅ Connection established with client ID: ${message.client_id}`);
          console.log(`   Capabilities: ${message.capabilities?.join(', ') || 'N/A'}`);
        } else if (message.type === 'agent_status') {
          console.log(`📊 Agent status update received: ${JSON.stringify(message, null, 2)}`);
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
    
    ws.on('close', () => {
      console.log('🔌 WebSocket connection closed');
    });
  });
}

async function testRealTimeUpdates() {
  console.log('\n📡 Testing Real-Time Agent Status Updates...');
  
  return new Promise((resolve) => {
    const ws = new WebSocket(WS_URL);
    const messagesReceived = [];
    let connectionEstablished = false;
    
    const timeout = setTimeout(() => {
      ws.close();
      resolve({
        status: messagesReceived.length > 0 ? 'PASSED' : 'FAILED',
        messagesReceived: messagesReceived.length,
        messages: messagesReceived,
        error: messagesReceived.length === 0 ? 'No real-time updates received' : null
      });
    }, 10000);
    
    ws.on('open', () => {
      console.log('✅ WebSocket connected for real-time testing');
    });
    
    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data.toString());
        
        if (message.type === 'connection_established') {
          connectionEstablished = true;
          console.log(`✅ Connection established: ${message.client_id}`);
          
          // Subscribe to agent status updates
          ws.send(JSON.stringify({
            type: 'subscribe',
            channel: 'agent_status'
          }));
          console.log('📡 Subscribed to agent status updates');
          
        } else if (message.type === 'agent_status' || 
                   message.type === 'system_notification' ||
                   message.type === 'echo') {
          messagesReceived.push({
            type: message.type,
            timestamp: new Date().toISOString(),
            data: message
          });
          console.log(`📥 Real-time update received: ${message.type}`);
          
          // If we get any real-time message, consider it a success
          if (messagesReceived.length >= 1) {
            clearTimeout(timeout);
            ws.close();
            resolve({
              status: 'PASSED',
              messagesReceived: messagesReceived.length,
              messages: messagesReceived
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

async function main() {
  console.log('🚀 WebSocket Performance and Real-Time Testing');
  console.log('=' .repeat(60));
  
  try {
    // Test latency
    const latencyResults = await testWebSocketLatency();
    
    // Test real-time updates
    const realTimeResults = await testRealTimeUpdates();
    
    console.log('\n🎯 WEBSOCKET TEST SUMMARY');
    console.log('=' .repeat(60));
    console.log(`📊 Latency Test: ${latencyResults.status}`);
    console.log(`   Average Latency: ${latencyResults.averageLatency}ms (target: <100ms)`);
    console.log(`   Connection Time: ${latencyResults.connectionTime}ms`);
    
    console.log(`📡 Real-Time Updates: ${realTimeResults.status}`);
    console.log(`   Messages Received: ${realTimeResults.messagesReceived}`);
    
    const overallSuccess = latencyResults.status === 'PASSED' && realTimeResults.status === 'PASSED';
    console.log(`\n🎯 Overall WebSocket Status: ${overallSuccess ? '✅ PASSED' : '⚠️  NEEDS IMPROVEMENT'}`);
    
    // Save results
    const results = {
      latency: latencyResults,
      realTime: realTimeResults,
      overallStatus: overallSuccess ? 'PASSED' : 'NEEDS_IMPROVEMENT'
    };
    
    const fs = require('fs');
    fs.writeFileSync('websocket-test-results.json', JSON.stringify(results, null, 2));
    console.log('\n📄 Results saved to: websocket-test-results.json');
    
    process.exit(overallSuccess ? 0 : 1);
    
  } catch (error) {
    console.error('\n❌ WebSocket testing failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}
