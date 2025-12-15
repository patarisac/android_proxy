# android_proxy

Scripts to force an Android app to route all its traffic through Burp Suite by applying per-app or global proxy rules using iptables.

## Files

* android_proxy.sh     : enable proxy for a specific app or globally
* android_unproxy.sh   : remove the proxy and restore normal routing

## Requirements

* Android device or AVD must be rooted
* Android device must be on the same network as the host (laptop/PC running Burp Suite)

## Tested
- Android Emulator (AVD) up to Android 15
- Physical Android device up to Android 14

This approach should work on all (rooted) Android versions that support iptables.


## Setup

```bash
chmod +x android_proxy.sh android_unproxy.sh
```

## Usage

### Enable proxy (specific app):

```bash
./android_proxy.sh -u <package_id> -p <burp_port>
```

### Disable proxy (specific app):

```bash
./android_unproxy.sh -u <package_id> -p <burp_port>
```

### Enable proxy (all Android traffic):

```bash
./android_proxy.sh -p <burp_port>
```

### Disable proxy (all Android traffic):

```bash
./android_unproxy.sh -p <burp_port>
```

### Example

```bash
./android_proxy.sh -u com.example.app -p 8083 # route all com.example.app traffic to host's 8083 port
./android_unproxy.sh -u com.example.app -p 8083 # undo

./android_proxy.sh -p 8083 # route all Android apps' traffic to host's 8083 port
./android_unproxy.sh -p 8083 # undo
```

## Notes

* This script modifies iptables rules on the device. Network connectivity may break if rules are not reverted properly.
* All modifications are temporary and will be automatically cleared after the Android device reboots.
* Always run android_unproxy.sh after testing to restore the original network state without rebooting.
