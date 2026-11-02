#!/usr/bin/env python3
"""
Chaos Monkey for RetailOps Platform.

Randomly terminates pods in the application namespace to validate:
  - Kubernetes self-healing (ReplicaSet restarts pods)
  - PodDisruptionBudget enforcement (maxUnavailable respected)
  - HorizontalPodAutoscaler reaction to load
  - Observability stack alerting on crash loops

Usage:
    python chaos-monkey.py --namespace retailops --interval 30 --duration 300
"""

from __future__ import annotations

import argparse
import random
import subprocess
import sys
import time
from datetime import datetime, timedelta


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def get_pods(namespace: str) -> list[str]:
    """Return a list of pod names in the given namespace."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", namespace, "-o", "jsonpath={.items[*].metadata.name}"],
            capture_output=True,
            text=True,
            check=True,
        )
        pods = result.stdout.strip().split()
        return [p for p in pods if not p.startswith("kube-") and not p.startswith("prometheus")]
    except subprocess.CalledProcessError as exc:
        log(f"Failed to list pods: {exc.stderr.strip()}")
        return []


def kill_pod(namespace: str, pod: str) -> None:
    """Delete a pod to simulate a node crash / chaos event."""
    try:
        subprocess.run(
            ["kubectl", "delete", "pod", pod, "-n", namespace],
            capture_output=True,
            text=True,
            check=True,
        )
        log(f"CHAOS: Terminated pod {pod} in namespace {namespace}")
    except subprocess.CalledProcessError as exc:
        log(f"Failed to kill pod {pod}: {exc.stderr.strip()}")


def main() -> int:
    parser = argparse.ArgumentParser(description="RetailOps Chaos Monkey")
    parser.add_argument("--namespace", default="retailops", help="Target namespace")
    parser.add_argument("--interval", type=int, default=30, help="Seconds between chaos events")
    parser.add_argument("--duration", type=int, default=300, help="Total duration in seconds")
    parser.add_argument("--max-pods-per-cycle", type=int, default=1, help="Max pods to kill per cycle")
    args = parser.parse_args()

    end_time = datetime.now() + timedelta(seconds=args.duration)
    cycle = 0

    log(f"Starting Chaos Monkey: namespace={args.namespace}, interval={args.interval}s, duration={args.duration}s")

    while datetime.now() < end_time:
        cycle += 1
        pods = get_pods(args.namespace)

        if not pods:
            log(f"Cycle {cycle}: No target pods found in namespace {args.namespace}")
            time.sleep(args.interval)
            continue

        targets = random.sample(pods, min(args.max_pods_per_cycle, len(pods)))
        log(f"Cycle {cycle}: Target pods: {targets}")

        for pod in targets:
            kill_pod(args.namespace, pod)

        time.sleep(args.interval)

    log("Chaos Monkey completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
