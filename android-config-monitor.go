package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

type DeviceConfig struct {
	Timestamp    string            `json:"timestamp"`
	Properties   map[string]string `json:"properties"`
	Settings     map[string]string `json:"settings"`
	BuildInfo    map[string]string `json:"build_info"`
}

func runAdb(args ...string) string {
	cmd := exec.Command("adb", args...)
	output, err := cmd.Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(output))
}

func getProperties() map[string]string {
	output := runAdb("shell", "getprop")
	props := make(map[string]string)
	scanner := bufio.NewScanner(strings.NewReader(output))
	for scanner.Scan() {
		line := scanner.Text()
		parts := strings.SplitN(line, "]: [", 2)
		if len(parts) == 2 {
			key := strings.TrimPrefix(parts[0], "[")
			value := strings.TrimSuffix(parts[1], "]")
			props[key] = value
		}
	}
	return props
}

func getSettings() map[string]string {
	settings := make(map[string]string)
	// Sample critical settings
	criticalSettings := []string{
		"adb_enabled",
		"screen_brightness",
		"screen_off_timeout",
		"wifi_on",
		"bluetooth_on",
		"airplane_mode_on",
	}
	for _, setting := range criticalSettings {
		value := runAdb("shell", "settings", "get", "global", setting)
		settings[setting] = value
	}
	return settings
}

func getBuildInfo() map[string]string {
	buildInfo := make(map[string]string)
	buildProps := []string{
		"ro.build.version.release",
		"ro.build.version.sdk",
		"ro.product.model",
		"ro.product.manufacturer",
		"ro.build.fingerprint",
		"ro.build.version.security_patch",
	}
	for _, prop := range buildProps {
		value := runAdb("shell", "getprop", prop)
		buildInfo[prop] = value
	}
	return buildInfo
}

func main() {
	outputJSON := flag.Bool("json", false, "Output as JSON")
	flag.Parse()

	config := DeviceConfig{
		Timestamp:  time.Now().Format(time.RFC3339),
		Properties: getProperties(),
		Settings:   getSettings(),
		BuildInfo:  getBuildInfo(),
	}

	if *outputJSON {
		data, _ := json.MarshalIndent(config, "", "  ")
		fmt.Println(string(data))
	} else {
		fmt.Printf("Device Config Snapshot - %s\n", config.Timestamp)
		fmt.Printf("Android: %s (API %s)\n", config.BuildInfo["ro.build.version.release"], config.BuildInfo["ro.build.version.sdk"])
		fmt.Printf("Device: %s (%s)\n", config.BuildInfo["ro.product.model"], config.BuildInfo["ro.product.manufacturer"])
		fmt.Printf("Settings - ADB: %s, WiFi: %s, BT: %s, Airplane: %s\n",
			config.Settings["adb_enabled"],
			config.Settings["wifi_on"],
			config.Settings["bluetooth_on"],
			config.Settings["airplane_mode_on"],
		)
	}
}
