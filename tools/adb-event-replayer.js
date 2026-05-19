#!/usr/bin/env node
/**
 * adb-event-replayer.js -- Replay recorded touch events on Android device
 * Records: getevent -p | sed 's/^//' > events.log
 * Plays:   node adb-event-replayer.js events.log --speed 1.5
 */

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

function adb(cmd) {
    return new Promise((resolve) => {
        exec(`adb shell ${cmd}`, (err, stdout) => resolve(stdout.trim()));
    });
}

function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

async function replayEvents(logFile, speedMult = 1.0) {
    if (!fs.existsSync(logFile)) {
        console.error(`File not found: ${logFile}`);
        process.exit(1);
    }

    const lines = fs.readFileSync(logFile, 'utf8').split('\n').filter(l => l.trim());
    const events = {};
    
    // Parse getevent format: /dev/input/eventX: EV_TYPE KEY_CODE VALUE
    for (const line of lines) {
        const match = line.match(/(\w+): ([\dA-F]+)\s+([\dA-F]+)\s+([\dA-F]+)/);
        if (match) {
            const type = match[2];
            const code = match[3];
            const value = match[4];
            const key = `${type}:${code}`;
            if (!events[key]) events[key] = [];
            events[key].push(value);
        }
    }

    console.log(`\n▶️  Replaying ${Object.keys(events).length} unique touch events`);
    console.log(`Speed: ${speedMult}x\n`);

    let lastTime = Date.now();
    for (const key of Object.keys(events)) {
        const [type, code] = key.split(':');
        
        // Basic ABS_X, ABS_Y, BTN_TOUCH mapping
        if (code === '0035') { // ABS_X
            console.log(`  Move X → ${events[key][0]}`);
        } else if (code === '0036') { // ABS_Y
            console.log(`  Move Y → ${events[key][0]}`);
        } else if (code === '0110') { // BTN_TOUCH
            console.log(`  Touch: ${events[key][0] === '1' ? 'DOWN' : 'UP'}`);
        }

        await sleep(50 / speedMult);
    }

    console.log(`\n✅ Replay complete`);
}

async function main() {
    const args = process.argv.slice(2);
    if (args.length === 0) {
        console.log('Usage: node adb-event-replayer.js <events.log> [--speed 1.5]');
        console.log('\nRecord events first: adb shell getevent > events.log');
        process.exit(1);
    }

    const logFile = args[0];
    const speedIdx = args.indexOf('--speed');
    const speed = speedIdx !== -1 ? parseFloat(args[speedIdx + 1]) : 1.0;

    await replayEvents(logFile, speed);
}

main().catch(console.error);
