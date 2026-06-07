#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys

DIP = "127.0.0.1"


def run_adb_cmd(cmd_list):
    try:
        result = subprocess.run(
            cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        print(
            "Error: 'adb' command not found. Ensure Android SDK platform-tools are in your PATH."
        )
        sys.exit(1)


def check_adb_connection():
    stdout, _, _ = run_adb_cmd(["adb", "devices"])
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    
    devices = lines[1:] if len(lines) > 1 else []
    
    if not devices:
        print("Error: No Android devices or emulators found. Please connect your device and try again.")
        sys.exit(1)
        
    unauthorized = any("unauthorized" in d for d in devices)
    offline = any("offline" in d for d in devices)
    
    if unauthorized:
        print("Error: Device is unauthorized. Please look at your phone screen and allow USB debugging.")
        sys.exit(1)
    elif offline:
        print("Error: Connected device is offline. Try restarting your phone's USB debugging or the ADB server.")
        sys.exit(1)


def get_adb_shell_prefix():
    stdout, _, _ = run_adb_cmd(["adb", "shell", "whoami"])
    if "root" in stdout:
        return []

    stdout, _, _ = run_adb_cmd(["adb", "shell", "which", "su"])
    if "/system/bin/su" in stdout:
        return ["su", "-c"]
    else:
        return ["su", "root", "sh", "-c"]


def execute_iptables_cmd(iptables_args):
    prefix = get_adb_shell_prefix()
    iptables_str = f"iptables {iptables_args}"

    if prefix:
        if prefix[0] == "su" and len(prefix) == 2:
            full_cmd = ["adb", "shell", prefix[0], prefix[1], iptables_str]
        else:
            full_cmd = [
                "adb",
                "shell",
                prefix[0],
                prefix[1],
                prefix[2],
                prefix[3],
                iptables_str,
            ]
    else:
        full_cmd = ["adb", "shell", iptables_str]

    stdout, stderr, code = run_adb_cmd(full_cmd)
    return stdout, stderr, code


def get_uid_from_pkg(pkg_name):
    stdout, _, _ = run_adb_cmd(["adb", "shell", "pm", "list", "packages", "-U"])
    for line in stdout.splitlines():
        if pkg_name in line:
            match = re.search(r"uid:(\d+)", line)
            if match:
                return match.group(1)
    print(f"Error: Cannot find UID for package '{pkg_name}'")
    sys.exit(1)


def get_pkg_from_uid(uid):
    stdout, _, _ = run_adb_cmd(["adb", "shell", "pm", "list", "packages", "-U"])
    for line in stdout.splitlines():
        if f"uid:{uid}" in line:
            match = re.search(r"package:([^\s]+)", line)
            if match:
                return match.group(1)
    return f"UID: {uid}"


def enable_proxy(pkg, port):
    target_uid = get_uid_from_pkg(pkg) if pkg else None

    if target_uid:
        print(f"Targeting UID: {target_uid} for app: {pkg}")
        iptables_args = f"-t nat -A OUTPUT -p tcp -m owner --uid-owner {target_uid} -j DNAT --to-destination {DIP}:{port}"
    else:
        print("Targeting global Android traffic (excluding port 27042)...")
        iptables_args = f"-t nat -A OUTPUT -p tcp ! --dport 27042 -j DNAT --to-destination {DIP}:{port}"

    _, _, rev_code = run_adb_cmd(
        ["adb", "reverse", f"tcp:{port}", f"tcp:{port}"]
    )
    if rev_code != 0:
        print(f"Warning: Failed to set adb reverse for port {port}")

    stdout, stderr, code = execute_iptables_cmd(iptables_args)
    if code == 0:
        print(f"Proxy active → {DIP}:{port}")
    else:
        print(f"Error applying proxy rules: {stderr.strip()}")


def parse_active_proxies():
    stdout, _, code = execute_iptables_cmd("-t nat -S OUTPUT")
    if code != 0:
        print("Failed to fetch active iptables rules.")
        return []

    rules = []
    for line in stdout.splitlines():
        if "DNAT --to-destination" in line:
            port_match = re.search(r"--to-destination \d+\.\d+\.\d+\.\d+:(\d+)", line)
            if not port_match:
                continue
            port = port_match.group(1)

            uid_match = re.search(r"--uid-owner (\d+)", line)
            
            if uid_match:
                uid = uid_match.group(1)
                delete_args = f"-t nat -D OUTPUT -p tcp -m owner --uid-owner {uid} -j DNAT --to-destination {DIP}:{port}"
                display_target = get_pkg_from_uid(uid)
            else:
                delete_args = f"-t nat -D OUTPUT -p tcp ! --dport 27042 -j DNAT --to-destination {DIP}:{port}"
                display_target = "Global (All Apps)"

            rules.append({"target": display_target, "port": port, "raw_delete": delete_args})
    return rules


def list_proxies():
    rules = parse_active_proxies()
    if not rules:
        print("No active proxy rules found.")
        return False

    print("\n=== Active Proxy Rules ===")
    print(f"{'No.':<5} {'Target (Package / Scope)':<40} {'Burp Proxy Port':<15}")
    print("-" * 65)
    for idx, rule in enumerate(rules, start=1):
        print(f"{idx:<5} {rule['target']:<40} {rule['port']:<15}")
    print()
    return rules


def disable_proxy_interactive():
    rules = list_proxies()
    if not rules:
        return

    try:
        choice = input(
            "Enter the number of the proxy rule you want to REMOVE (or 'q' to quit): "
        ).strip()
        if choice.lower() == "q" or not choice:
            return

        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(rules):
            target_rule = rules[choice_idx]

            _, stderr, code = execute_iptables_cmd(target_rule["raw_delete"])
            if code == 0:
                run_adb_cmd(
                    ["adb", "reverse", "--remove", f"tcp:{target_rule['port']}"]
                )
                print(
                    f"Successfully removed proxy rule for Port {target_rule['port']}!"
                )
            else:
                print(f"Failed to remove iptables rule: {stderr.strip()}")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input. Please enter a number.")


def main():
    parser = argparse.ArgumentParser(
        description="Android Proxy Tool - Route app traffic to Burp Suite using iptables"
    )
    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "-s",
        "--start",
        action="store_true",
        help="Start proxy routing (requires -p/--port)",
    )
    group.add_argument(
        "-l", "--list", action="store_true", help="List active proxy rules"
    )
    group.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Interactively list and remove a proxy rule",
    )

    parser.add_argument(
        "-u",
        "--package",
        dest="pkg",
        help="Target specific Android package name (OMIT for global proxy)",
    )
    parser.add_argument(
        "-p",
        "--port",
        default="8082",
        help="Local Burp Suite proxy port (default: 8082)",
    )

    args = parser.parse_args()

    if args.start or args.list or args.remove:
        check_adb_connection()

    if args.start:
        enable_proxy(args.pkg, args.port)
    elif args.list:
        list_proxies()
    elif args.remove:
        disable_proxy_interactive()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
