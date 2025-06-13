# ROS 2 Camera ➜ RTSP Quick‑Start Guide

This short checklist helps anyone on the team bring a HikRobot camera online in ROS 2 and expose it as an RTSP stream that the frontend (FE) can open.

---

## 1. Bring the camera online (ROS 2 topic)

```bash
# 1‑A. SSH into the edge device
essh <user>@<edge_device_ip>

# 1‑B. Load the camera workspace
cd ~/workspaces/nv_hikrobot_ros_driver
source install/setup.bash

# 1‑C. Launch the driver (replace <SERIAL>)
ros2 launch nv_hikrobot_ros_driver hikrobot_camera_ros2.launch.py \
    serial_num:=<SERIAL>
```

> **Result:** the camera publishes JPEG frames on `/hikrobot/<SERIAL>/compressed`.

Verify with:

```bash
ros2 topic hz /hikrobot/<SERIAL>/compressed   # expect ~10 fps
```

---

## 2. Convert the topic to RTSP

**Repository (ROS ➜ RTSP converter):** [https://github.com/maladzenkau/image2rtsp](https://github.com/maladzenkau/image2rtsp)

```bash
# 2‑A. Switch to the conversion workspace
cd ~/workspaces/app_one
source install/setup.bash

# 2‑B. Start the RTSP node (default port 8556)
ros2 launch image2rtsp image2rtsp.launch.py
```

The default **mount‑point** is `back`, so the stream is:

```
rtsp://<edge_device_ip>:8556/back
```

### 2.1  Smoke‑test locally

```bash
ffprobe -v error -rtsp_transport tcp -count_frames -select_streams v:0 \
        rtsp://127.0.0.1:8556/back
```

Frame info confirms packets are flowing.

---

## 3. Adjusting parameters

- **Topic** or **port**: edit `config/parameters.yaml` inside `workspaces/app_one/image2rtsp`.
  - `topic`: `/hikrobot/<SERIAL>/compressed`
  - `port`: `8556` (change if 8554/8555 are preferred)
- Re‑run **step 2‑B** after any config change.

---

## 4. Common issues & fixes

| Issue               | Symptom                          | Fix                                                              |
| ------------------- | -------------------------------- | ---------------------------------------------------------------- |
| Port already in use | `lsof -i :8556` shows `mediamtx` | Edit `parameters.yaml` → choose free port (e.g. 8557).           |
| Missing video       | `ros2 topic hz` shows 0 fps      | Camera driver not running or wrong serial → repeat **step 1‑C**. |
| VLC times out       | Firewall blocks TCP 8556         | `sudo ufw allow 8556/tcp` on edge device.                        |

---

### TL;DR for experts

```bash
ssh edge && cd ~/ws/nv && source install/setup.bash \
  && ros2 launch nv_hikrobot_ros_driver hikrobot_camera_ros2.launch.py serial_num:=<SERIAL> &
cd ~/ws/app_one && source install/setup.bash \
  && ros2 launch image2rtsp image2rtsp.launch.py &
```

Share **rtsp\://\<edge\_ip>:8556/back** with the FE.

