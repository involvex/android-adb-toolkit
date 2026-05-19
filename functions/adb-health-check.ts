/**
 * adb-health-check.ts
 * HTTP backend function to check ADB device health
 * Deploy with: base44 deploy functions/adb-health-check.ts
 * Call with: POST /api/functions/adbHealthCheck
 */

export async function adbHealthCheck() {
  const { execSync } = await import("child_process");
  
  try {
    // Check if adb is running
    const devices = execSync("adb devices", { encoding: "utf8" });
    const connected = devices.split("\n").filter(l => l.includes("device") && !l.includes("offline"));
    
    if (connected.length === 0) {
      return {
        status: "error",
        message: "No Android devices connected",
        code: "NO_DEVICES"
      };
    }

    // Get device info
    const device = connected[0].split("\t")[0];
    const model = execSync(`adb -s ${device} shell getprop ro.product.model`, { encoding: "utf8" }).trim();
    const android = execSync(`adb -s ${device} shell getprop ro.build.version.release`, { encoding: "utf8" }).trim();
    const battery = execSync(`adb -s ${device} shell dumpsys battery | grep level`, { encoding: "utf8" }).match(/\d+/)?.[0];

    return {
      status: "ok",
      device,
      model,
      android_version: android,
      battery_percent: parseInt(battery) || null,
      timestamp: new Date().toISOString()
    };
  } catch (err) {
    return {
      status: "error",
      message: err.message,
      code: "ADB_ERROR"
    };
  }
}
