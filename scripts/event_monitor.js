#!/usr/bin/env node
/**
 * event_monitor.js -- Monitor getevent output in real-time
 * Usage: ./event_monitor.js [--filter EV_KEY]
 */
const { exec } = require('child_process');
const readline = require('readline');

const eventMap = {
  'EV_KEY': 'Key press/release',
  'EV_ABS': 'Absolute motion (touchscreen)',
  'EV_REL': 'Relative motion (mouse)',
  'EV_SYN': 'Sync marker',
};

const args = process.argv.slice(2);
const filter = args.includes('--filter') ? args[args.indexOf('--filter') + 1] : null;

console.log('📱 Android Event Monitor\n');
const proc = exec('adb shell getevent', { maxBuffer: 10 * 1024 * 1024 });

proc.stdout.on('data', (data) => {
  data.toString().split('\n').forEach(line => {
    if (!line) return;
    const match = line.match(/(\w+)\s+([\w_]+)\s+([\w_]+)\s+([\da-f]+)/i);
    if (match && (!filter || line.includes(filter))) {
      const [, device, type, code, value] = match;
      console.log(`  ${type.padEnd(8)} ${code.padEnd(20)} value=${value}`);
    }
  });
});

process.on('SIGINT', () => {
  proc.kill();
  console.log('\nStopped.');
  process.exit(0);
});
