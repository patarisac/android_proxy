# android_proxy

A unified, cross-platform Python utility designed to dynamically inject or remove custom network routing profiles inside a rooted Android environment. It explicitly forces per-application or device-wide traffic to cleanly map back to local interception proxies (e.g., Burp Suite listeners) across Linux, macOS, and Windows.

## Requirements

- **Root Access:** Target physical hardware or Android Virtual Devices (AVD) must possess established root boundaries (`su`).
- **System Boundaries:** Host operating environments must expose `adb` universally through native shell configuration paths.

---

## Usage Guide

Give the script executive running permissions (Linux/macOS platforms only):
```bash
chmod +x android_proxy.py
```

### 1. Intercept a Specific Target Application
To isolate, register, and lock an interface loop down to a single chosen bundle ID, pair your command execution with the specific package target flag:
```bash
./android_proxy.py -s -u com.example.targetapp -p 8082
```
*(On Windows systems, invoke using explicit terminal handles: `python android_proxy.py -s -u com.example.targetapp -p 8082`)*

### 2. Route Device Traffic Globally
To enforce interception parameters device-wide across all systemic framework endpoints (safely blacklisting the base infrastructure communication loop at `27042` to eliminate proxy cascade locks), omit the package parameter completely:
```bash
./android_proxy.py -s -p 8082
```

### 3. Survey Currently Active Proxy Configurations
To look into the host engine runtime data and active loop variables without mutating running parameters:
```bash
./android_proxy.py -l
```
**Example Runtime Map:**
```text
=== Active Proxy Rules ===
No.  Target Scope / Package                   Burp Proxy Port
1    com.example.targetapp                    8082           
2    Global (All Apps)                        8084           
```

### 4. Interactive Configuration Teardown
To securely teardown active listeners and structural loops without leaving device endpoints in dead states, invoke the targeted removal manager:
```bash
./android_proxy.py -r
```
Simply choose the rule index integer from the provided list to simultaneously strip away the target device iptables rules and detach the structural host reverse ADB maps.

---

## Technical Notes

- **Volatile Execution:** Custom device-side `iptables` hooks live strictly in volatile memory. If your testing canvas crashes or needs an immediate reset, executing an emulator cold reboot clears all changes.
- **Session Clean Up:** Always run the `-r` unproxy selection when tearing down proxy hooks. Leaving hooks in place without an active intercept listener can drop your test device's network traffic entirely.