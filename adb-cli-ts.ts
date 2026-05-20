#!/usr/bin/env node
/**
 * adb-cli-ts.ts -- TypeScript CLI for interactive ADB command exploration
 * Provides command hints, history, and auto-completion
 * 
 * Usage: npx ts-node adb-cli-ts.ts [device serial]
 */

import { execSync } from 'child_process';
import * as readline from 'readline';

const adb = (cmd: string): string => {
  try {
    return execSync(`adb shell ${cmd}`, { encoding: 'utf8' });
  } catch (e) {
    return `Error: ${(e as Error).message}`;
  }
};

const HINTS: Record<string, string> = {
  'getprop': 'Get system property | getprop ro.build.version.release',
  'pm list packages': 'List installed packages | pm list packages -3 (user only)',
  'dumpsys battery': 'Show battery status',
  'settings list secure': 'Show secure settings',
  'input tap': 'Tap screen | input tap 540 960',
  'input swipe': 'Swipe screen | input swipe x1 y1 x2 y2',
  'screencap': 'Capture screenshot | screencap -p /sdcard/ss.png',
  'logcat': 'View log stream | logcat -v threadtime',
};

async function repl() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const history: string[] = [];

  const prompt = () => {
    rl.question('adb> ', (input) => {
      if (!input.trim()) return prompt();
      
      if (input === 'exit') {
        rl.close();
        return;
      }

      if (input === 'help') {
        console.log('\n📚 Common commands:\n');
        Object.entries(HINTS).forEach(([cmd, desc]) => {
          console.log(`  ${cmd.padEnd(25)} ${desc}`);
        });
        console.log();
        return prompt();
      }

      const result = adb(input);
      console.log(result);
      history.push(input);
      prompt();
    });
  };

  console.log('🔧 ADB Interactive CLI (type "help" for hints)\n');
  prompt();
}

repl().catch(console.error);
