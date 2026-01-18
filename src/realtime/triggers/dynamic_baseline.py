"""
Dynamic baseline tracker for chat velocity anomaly detection.

Maintains a rolling 5-minute window of velocity measurements per channel,
calculating mean and standard deviation to detect spikes dynamically.

The threshold is calculated as: baseline + (2 × stddev)
A spike is detected when current velocity exceeds this threshold.

Baselines are persisted to data/baselines.json on shutdown and loaded on startup.
"""

import json
import statistics
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class DynamicBaseline:
    """
    Tracks rolling chat velocity per channel with dynamic baseline calculation.

    Uses a 5-minute sliding window to maintain historical velocity samples,
    computing mean and standard deviation for anomaly detection.

    Attributes:
        channel_id: Unique identifier for the channel being monitored.
        window_duration_seconds: Size of the rolling window (default: 300s = 5 min).
        baseline_file: Path to persist baselines across sessions.
    """

    # Default 5-minute window
    DEFAULT_WINDOW_SECONDS = 300

    def __init__(
        self,
        channel_id: str,
        window_duration_seconds: int = DEFAULT_WINDOW_SECONDS,
        baseline_file: Optional[Path] = None,
    ):
        """
        Initialize a DynamicBaseline tracker for a channel.

        Args:
            channel_id: Identifier for the channel (e.g., "12345").
            window_duration_seconds: Rolling window size in seconds (default: 300).
            baseline_file: Path to persist baselines (default: data/baselines.json).
        """
        self.channel_id = channel_id
        self.window_duration_seconds = window_duration_seconds

        if baseline_file is None:
            baseline_file = Path(__file__).parent.parent.parent.parent / "data" / "baselines.json"
        self.baseline_file = Path(baseline_file)

        # Rolling window: stores (timestamp, velocity) tuples
        self.samples: deque = deque()

        # Load persisted baseline if available
        self._load_baseline()

    def add_sample(self, velocity: float) -> None:
        """
        Add a velocity reading to the rolling window.

        Removes old samples outside the window and stores the new measurement.

        Args:
            velocity: Current velocity measurement (e.g., messages per second).
        """
        now = datetime.now()
        self.samples.append((now, velocity))

        # Remove samples older than the window
        cutoff_time = now - timedelta(seconds=self.window_duration_seconds)
        while self.samples and self.samples[0][0] < cutoff_time:
            self.samples.popleft()

    def get_threshold(self) -> float:
        """
        Calculate the spike detection threshold.

        Threshold = mean(velocity) + (2 × stddev(velocity))

        Returns 0 if fewer than 2 samples (insufficient data).

        Returns:
            Threshold value as a float. Returns 0 if insufficient samples.
        """
        if len(self.samples) < 2:
            return 0.0

        velocities = [v for _, v in self.samples]
        mean_velocity = statistics.mean(velocities)
        stdev_velocity = statistics.stdev(velocities)

        # Threshold: baseline + 2 standard deviations
        threshold = mean_velocity + (2 * stdev_velocity)
        return threshold

    def is_spike(self, velocity: float) -> bool:
        """
        Detect if current velocity represents a spike.

        A spike is detected when velocity exceeds the calculated threshold.

        Args:
            velocity: Current velocity to check.

        Returns:
            True if velocity > threshold, False otherwise.
        """
        threshold = self.get_threshold()
        return velocity > threshold

    def get_stats(self) -> Dict[str, float]:
        """
        Get current statistics for monitoring and debugging.

        Returns:
            Dictionary with keys: count, mean, stdev, threshold, latest_velocity.
        """
        if len(self.samples) == 0:
            return {
                "count": 0,
                "mean": 0.0,
                "stdev": 0.0,
                "threshold": 0.0,
                "latest_velocity": 0.0,
            }

        velocities = [v for _, v in self.samples]
        mean_vel = statistics.mean(velocities)
        stdev_vel = statistics.stdev(velocities) if len(velocities) > 1 else 0.0

        return {
            "count": len(self.samples),
            "mean": round(mean_vel, 2),
            "stdev": round(stdev_vel, 2),
            "threshold": round(self.get_threshold(), 2),
            "latest_velocity": round(velocities[-1], 2) if velocities else 0.0,
        }

    def save_baseline(self) -> None:
        """
        Persist the current baseline to data/baselines.json.

        Only saves if there are samples. Creates file if it doesn't exist.
        Maintains baselines for all channels in a single JSON file.
        """
        if len(self.samples) == 0:
            return

        # Load existing baselines
        baselines = {}
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, "r") as f:
                    baselines = json.load(f)
            except (json.JSONDecodeError, IOError):
                baselines = {}

        # Extract velocities and store summary
        velocities = [v for _, v in self.samples]
        mean_vel = statistics.mean(velocities)
        stdev_vel = statistics.stdev(velocities) if len(velocities) > 1 else 0.0

        baselines[self.channel_id] = {
            "mean": round(mean_vel, 4),
            "stdev": round(stdev_vel, 4),
            "sample_count": len(self.samples),
            "saved_at": datetime.now().isoformat(),
        }

        # Write back
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.baseline_file, "w") as f:
            json.dump(baselines, f, indent=2)

    def _load_baseline(self) -> None:
        """
        Load saved baseline from data/baselines.json if available.

        This is called during __init__. If a baseline exists for this channel,
        it's used to seed the initial statistics (though no samples are restored).
        """
        if not self.baseline_file.exists():
            return

        try:
            with open(self.baseline_file, "r") as f:
                baselines = json.load(f)

            if self.channel_id in baselines:
                baseline_info = baselines[self.channel_id]
                # Note: We don't restore samples, only acknowledge the saved state
                print(
                    f"[baseline] Loaded saved baseline for channel {self.channel_id}: "
                    f"mean={baseline_info.get('mean', 0)}, "
                    f"stdev={baseline_info.get('stdev', 0)}"
                )
        except (json.JSONDecodeError, IOError) as e:
            print(f"[baseline] Warning: Could not load baseline file: {e}")
