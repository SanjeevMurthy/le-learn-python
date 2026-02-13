"""
anomaly_detection.py

Simple anomaly detection for log streams and metrics.

Prerequisites:
- Standard library only
"""

import math
import logging
from typing import List, Dict, Any, Tuple
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def detect_rate_anomalies(
    values: List[float],
    window: int = 10,
    std_threshold: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Detect anomalies using a sliding window z-score approach.

    Interview Question:
        Q: How do you detect anomalies in monitoring data?
        A: 1. Statistical: z-score (>2-3 std devs from mean)
           2. Moving average: deviation from rolling average
           3. Seasonal decomposition: account for daily/weekly patterns
           4. ML-based: isolation forest, autoencoders
           5. Prometheus approach: predict_linear(), delta()
           Start simple (z-score), add complexity as needed.
           Avoid: static thresholds on dynamic workloads.
    """
    anomalies = []
    for i in range(window, len(values)):
        window_values = values[i - window:i]
        mean = sum(window_values) / len(window_values)
        variance = sum((x - mean) ** 2 for x in window_values) / len(window_values)
        std = math.sqrt(variance) if variance > 0 else 0.0001

        z_score = (values[i] - mean) / std

        if abs(z_score) > std_threshold:
            anomalies.append({
                'index': i,
                'value': values[i],
                'mean': round(mean, 2),
                'z_score': round(z_score, 2),
                'direction': 'spike' if z_score > 0 else 'drop',
            })

    return anomalies


def detect_log_pattern_anomalies(
    logs: List[Dict[str, Any]],
    level_field: str = 'level',
    baseline_error_rate: float = 0.05
) -> Dict[str, Any]:
    """Detect unusual log level distributions."""
    level_counts = Counter(log.get(level_field, 'INFO').upper() for log in logs)
    total = sum(level_counts.values()) or 1

    error_rate = (level_counts.get('ERROR', 0) + level_counts.get('CRITICAL', 0)) / total

    anomalies = []
    if error_rate > baseline_error_rate * 3:
        anomalies.append({
            'type': 'high_error_rate',
            'current': round(error_rate * 100, 2),
            'baseline': round(baseline_error_rate * 100, 2),
        })

    return {
        'total_logs': total,
        'level_distribution': dict(level_counts),
        'error_rate_pct': round(error_rate * 100, 2),
        'anomalies': anomalies,
    }


if __name__ == "__main__":
    print("Anomaly Detection — Usage Examples")
    print("""
    # Detect spikes in request rate
    values = [100, 102, 98, 101, 99, 150, 200, 500, 105, 101]
    anomalies = detect_rate_anomalies(values, window=5, std_threshold=2.0)
    for a in anomalies:
        print(f"  Index {a['index']}: value={a['value']} ({a['direction']}, z={a['z_score']})")
    """)
