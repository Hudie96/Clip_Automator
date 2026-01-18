# WebSocket Live Stats - Usage Examples

## How to Use from the Clipper

### 1. Import the shared stats and emit function

```python
from src.web.live_stats import shared_stats
from src.web.dashboard import emit_stats_update
```

### 2. Update viewer counts

```python
# When you detect viewer count change
shared_stats.update_viewers("xQc", 45000)
emit_stats_update()  # Broadcast to all connected clients
```

### 3. Update chat velocity

```python
# When calculating messages per minute
shared_stats.update_velocity("xQc", 125.5)
emit_stats_update()
```

### 4. Log trigger events

```python
# When a clip is triggered
shared_stats.add_trigger(
    streamer="xQc",
    trigger_type="viewer_spike",
    details={
        "before": 40000,
        "after": 55000,
        "spike_percent": 37.5
    }
)
emit_stats_update()
```

### 5. Update recording status

```python
# When starting recording
shared_stats.update_recording_status("xQc", True)
emit_stats_update()

# When stopping recording
shared_stats.update_recording_status("xQc", False)
emit_stats_update()
```

### 6. Full monitoring loop example

```python
from src.web.live_stats import shared_stats
from src.web.dashboard import emit_stats_update

def monitor_stream(streamer_name):
    while True:
        # Get current stats from Twitch API
        viewers = get_viewer_count(streamer_name)
        chat_rate = calculate_chat_velocity(streamer_name)

        # Update shared stats
        shared_stats.update_viewers(streamer_name, viewers)
        shared_stats.update_velocity(streamer_name, chat_rate)

        # Check for trigger conditions
        if should_trigger_clip(viewers, chat_rate):
            shared_stats.add_trigger(
                streamer=streamer_name,
                trigger_type="combo",
                details={
                    "viewers": viewers,
                    "chat_rate": chat_rate
                }
            )
            start_recording(streamer_name)
            shared_stats.update_recording_status(streamer_name, True)

        # Broadcast updates to dashboard
        emit_stats_update()

        time.sleep(5)  # Update every 5 seconds
```

## Client-Side JavaScript Example

```javascript
// Connect to WebSocket
const socket = io();

// Request initial stats
socket.emit('request_stats');

// Listen for stats updates
socket.on('stats_update', function(data) {
    console.log('Viewer counts:', data.viewer_counts);
    console.log('Chat velocities:', data.chat_velocities);
    console.log('Recent triggers:', data.recent_triggers);
    console.log('Recording status:', data.recording_status);

    // Update UI elements
    updateViewerCounts(data.viewer_counts);
    updateChatRates(data.chat_velocities);
    updateTriggerLog(data.recent_triggers);
    updateRecordingIndicators(data.recording_status);
});
```

## API Endpoint

You can also fetch stats via HTTP:

```bash
curl http://localhost:5000/api/stats
```

Returns:
```json
{
    "viewer_counts": {
        "xQc": 45000,
        "Shroud": 32000
    },
    "chat_velocities": {
        "xQc": 125.5,
        "Shroud": 87.2
    },
    "recent_triggers": [
        {
            "streamer": "xQc",
            "type": "viewer_spike",
            "timestamp": "2026-01-17T10:30:45.123456",
            "details": {"spike_percent": 37.5}
        }
    ],
    "recording_status": {
        "xQc": true,
        "Shroud": false
    },
    "last_updated": "2026-01-17T10:31:00.000000"
}
```

## Thread Safety

All operations are thread-safe thanks to the internal locking mechanism in SharedStats. You can safely call these methods from multiple threads:

```python
# Safe to call from different threads
thread1: shared_stats.update_viewers("xQc", 45000)
thread2: shared_stats.update_velocity("Shroud", 90.0)
thread3: shared_stats.add_trigger("xQc", "spike", {})
```

## Installation

Before running, install the new dependency:

```bash
pip install flask-socketio>=5.0.0
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```
