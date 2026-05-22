//! ADB Device Enumerator — list all connected devices with full properties
//! Written in Rust for speed and memory safety

use std::process::{Command, Stdio};
use std::io::BufRead;
use std::collections::HashMap;
use regex::Regex;

#[derive(Debug, Clone)]
pub struct AdbDevice {
    pub id: String,
    pub status: String,
    pub product: String,
    pub model: String,
    pub device: String,
    pub android_version: String,
    pub sdk_level: String,
    pub architecture: String,
    pub rooted: bool,
}

pub struct AdbEnumerator;

impl AdbEnumerator {
    pub fn list_devices() -> Result<Vec<AdbDevice>, String> {
        let output = Command::new("adb")
            .arg("devices")
            .arg("-l")
            .stdout(Stdio::piped())
            .output()
            .map_err(|e| format!("Failed to execute adb: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        let mut devices = Vec::new();

        for line in stdout.lines().skip(1) {
            if line.trim().is_empty() {
                continue;
            }

            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() < 2 {
                continue;
            }

            let device_id = parts[0].to_string();
            let status = parts[1].to_string();

            if status == "offline" || status == "unauthorized" {
                devices.push(AdbDevice {
                    id: device_id,
                    status,
                    product: String::new(),
                    model: String::new(),
                    device: String::new(),
                    android_version: String::new(),
                    sdk_level: String::new(),
                    architecture: String::new(),
                    rooted: false,
                });
                continue;
            }

            let mut props = HashMap::new();
            for part in parts.iter().skip(2) {
                if let Some((k, v)) = part.split_once(':') {
                    props.insert(k.to_string(), v.to_string());
                }
            }

            let device = AdbDevice {
                id: device_id.clone(),
                status: status.clone(),
                product: props.get("product").cloned().unwrap_or_default(),
                model: props.get("model").cloned().unwrap_or_default(),
                device: props.get("device").cloned().unwrap_or_default(),
                android_version: Self::get_property(&device_id, "ro.build.version.release")
                    .unwrap_or_default(),
                sdk_level: Self::get_property(&device_id, "ro.build.version.sdk")
                    .unwrap_or_default(),
                architecture: Self::get_property(&device_id, "ro.product.cpu.abi")
                    .unwrap_or_default(),
                rooted: Self::is_rooted(&device_id),
            };

            devices.push(device);
        }

        Ok(devices)
    }

    fn get_property(device_id: &str, prop: &str) -> Result<String, String> {
        let output = Command::new("adb")
            .arg("-s")
            .arg(device_id)
            .arg("shell")
            .arg(format!("getprop {}", prop))
            .stdout(Stdio::piped())
            .output()
            .map_err(|e| format!("ADB error: {}", e))?;

        Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
    }

    fn is_rooted(device_id: &str) -> bool {
        let output = Command::new("adb")
            .arg("-s")
            .arg(device_id)
            .arg("shell")
            .arg("which su")
            .stdout(Stdio::piped())
            .output();

        matches!(output, Ok(out) if !out.stdout.is_empty())
    }

    pub fn print_devices(devices: &[AdbDevice]) {
        println!("\n{:=^80}", " Connected ADB Devices ");
        println!(
            "{:<20} {:<12} {:<16} {:<14} {:<8} {:<8}",
            "ID", "Status", "Model", "Android", "Arch", "Root"
        );
        println!("{:-<80}", "");

        for device in devices {
            let rooted = if device.rooted { "✓" } else { "✗" };
            println!(
                "{:<20} {:<12} {:<16} {:<14} {:<8} {:<8}",
                &device.id[..device.id.len().min(19)],
                device.status,
                &device.model[..device.model.len().min(15)],
                device.android_version,
                &device.architecture[..device.architecture.len().min(7)],
                rooted
            );
        }
        println!("{:=<80}\n", "");
    }
}

fn main() {
    match AdbEnumerator::list_devices() {
        Ok(devices) => {
            if devices.is_empty() {
                println!("❌ No devices connected");
            } else {
                println!("✅ Found {} device(s)", devices.len());
                AdbEnumerator::print_devices(&devices);

                // Print detailed info if only one device
                if devices.len() == 1 {
                    let dev = &devices[0];
                    println!("📋 Detailed Info for {}:", dev.id);
                    println!("  Product: {}", dev.product);
                    println!("  Model: {}", dev.model);
                    println!("  Device: {}", dev.device);
                    println!("  Android: {} (SDK {})", dev.android_version, dev.sdk_level);
                    println!("  Architecture: {}", dev.architecture);
                    println!("  Root: {}", if dev.rooted { "Yes" } else { "No" });
                }
            }
        }
        Err(e) => {
            eprintln!("❌ Error: {}", e);
            std::process::exit(1);
        }
    }
}
