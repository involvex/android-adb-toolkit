import express, { Express, Request, Response } from "express";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
const app: Express = express();
const PORT = 3000;

app.use(express.json());

interface AdbResponse {
  success: boolean;
  output?: string;
  error?: string;
}

// Execute ADB command
async function adb(cmd: string): Promise<string> {
  try {
    const { stdout } = await execAsync(`adb shell ${cmd}`);
    return stdout.trim();
  } catch (err: any) {
    throw new Error(err.stderr || err.message);
  }
}

// Endpoints
app.get("/api/device", async (req: Request, res: Response): Promise<void> => {
  try {
    const model = await adb("getprop ro.product.model");
    const android = await adb("getprop ro.build.version.release");
    const battery = await adb("dumpsys battery | grep level");
    res.json({
      success: true,
      device: { model, android, battery },
    });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.post("/api/shell", async (req: Request, res: Response): Promise<void> => {
  const { command } = req.body;
  if (!command) {
    res.status(400).json({ success: false, error: "No command provided" });
    return;
  }
  try {
    const output = await adb(command);
    res.json({ success: true, output });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.post("/api/tap", async (req: Request, res: Response): Promise<void> => {
  const { x, y } = req.body;
  if (!x || !y) {
    res.status(400).json({ success: false, error: "x and y required" });
    return;
  }
  try {
    await adb(`input tap ${x} ${y}`);
    res.json({ success: true });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.post("/api/screenshot", async (req: Request, res: Response): Promise<void> => {
  try {
    await execAsync("adb exec-out screencap -p > screenshot.png");
    res.download("screenshot.png");
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`🖥️  ADB Server running on http://localhost:${PORT}`);
  console.log(`POST /api/shell with {"command":"..."}  to execute commands`);
});
