# 🔍 Network Sniffer TS

Lightweight TypeScript/Node.js tool to analyze Android network traffic via ADB tcpdump.

## Install
```bash
npm install -g
# or: npm install && npm run build
```

## Usage
```bash
# Capture and analyze traffic from specific app
network-sniffer com.example.app --duration 30

# Filter by protocol
network-sniffer --filter dns --filter http

# Export to JSON for processing
network-sniffer --output traffic.json
```

## Features
- Stream tcpdump output from ADB in real-time
- Parse TCP, UDP, DNS, HTTP traffic
- Filter by source/dest IP, port, protocol
- Per-app traffic analysis
- Export to JSON/CSV
