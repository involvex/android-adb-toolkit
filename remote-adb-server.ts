#!/usr/bin/env ts-node
/**
 * remote-adb-server.ts -- WebSocket server for remote ADB access
 * Run Android ADB commands from anywhere via WebSocket
 * Usage: npx ts-node remote-adb-server.ts --port 3000
 */
import WebSocket from 'ws';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as http from 'http';

const execAsync = promisify(exec);

interface AdbRequest {
  id: string;
  command: string;
  device?: string;
}

interface AdbResponse {
  id: string;
  status: 'success' | 'error';
  output?: string;
  error?: string;
  timestamp: number;
}

const wss = new WebSocket.Server({ port: 3000 });
const clients = new Map<string, WebSocket>();

console.log('🔗 ADB WebSocket Server running on ws://localhost:3000');

wss.on('connection', (ws: WebSocket, req) => {
  const clientId = `client-${Date.now()}`;
  clients.set(clientId, ws);
  console.log(`[${clientId}] Connected`);

  ws.on('message', async (data: string) => {
    try {
      const req: AdbRequest = JSON.parse(data);
      const device = req.device ? `-s ${req.device}` : '';
      const cmd = `adb ${device} ${req.command}`;

      console.log(`[${clientId}] Executing: ${cmd}`);
      const { stdout, stderr } = await execAsync(cmd);
      
      const response: AdbResponse = {
        id: req.id,
        status: 'success',
        output: stdout || stderr,
        timestamp: Date.now(),
      };
      ws.send(JSON.stringify(response));
    } catch (err: any) {
      const response: AdbResponse = {
        id: req.id || 'unknown',
        status: 'error',
        error: err.message,
        timestamp: Date.now(),
      };
      ws.send(JSON.stringify(response));
    }
  });

  ws.on('close', () => {
    clients.delete(clientId);
    console.log(`[${clientId}] Disconnected`);
  });

  ws.on('error', (err) => {
    console.error(`[${clientId}] Error:`, err);
  });
});

// Health check HTTP endpoint
const server = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', clients: clients.size }));
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

server.listen(3001, () => {
  console.log('📊 Health check at http://localhost:3001/health');
});
