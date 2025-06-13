#!/usr/bin/env python3
"""Multi-camera RTSP launch file for *image2rtsp*

• Reads a YAML file (**camera_config.yaml**) that lists camera serials
  → ROS topic → RTSP port / mount-point.
• Spawns **one `image2rtsp` node per camera**.

YAML schema example:
```yaml
base_port: 8556            # optional, default 8556
cameras:
  - serial: DA3614748      # required
    topic: /hikrobot/DA3614748/compressed   # optional, auto-filled if absent
    mount_point: cam1      # optional, default cam<index>
    port: 8556             # optional, auto-increments when absent
  - serial: DA4930148
    # … repeat for as many cameras as needed
```

Usage:
```bash
ros2 launch image2rtsp multi_camera_rtsp_launch.py \
    camera_config:=/absolute/path/to/camera_config.yaml
```
If *camera_config* is omitted, the launch file falls back to
`<package_share>/config/camera_config.yaml`.
"""

import os
from typing import List
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _load_yaml(path: str) -> dict:
    """Safely load the YAML camera-config file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"camera_config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _spawn_nodes(context, *_) -> List[Node]:
    cfg_path = LaunchConfiguration("camera_config").perform(context)
    cfg = _load_yaml(cfg_path)

    base_port = cfg.get("base_port", 8556)
    cams = cfg.get("cameras", [])

    entities: List[Node] = []
    for idx, cam in enumerate(cams):
        serial = cam["serial"]
        topic = cam.get("topic", f"/hikrobot/{serial}/compressed")
        port = cam.get("port", base_port + idx)
        mount = cam.get("mount_point", f"cam{idx + 1}")

        # Spawn one image2rtsp node per camera
        entities.append(
            Node(
                package="image2rtsp",
                executable="image2rtsp",  # matches console_script entry point
                name=f"image2rtsp_{serial}",
                parameters=[{
                    "topic": topic,
                    "port": str(port),  # convert to string to match node's declared type
                    "mount_point": mount,
                    "use_compressed": True,
                }],
                output="screen",
            )
        )
        # Log the resulting RTSP URL
        entities.append(
            LogInfo(msg=f"[multi_cam_rtsp] {serial} ➜ rtsp://<edge_ip>:{port}/{mount}")
        )

    return entities


def generate_launch_description() -> LaunchDescription:
    """Entry point for the ROS 2 launch system."""
    default_cfg = os.path.join(
        get_package_share_directory("image2rtsp"),
        "config",
        "camera_config.yaml",
    )

    cfg_arg = DeclareLaunchArgument(
        "camera_config",
        default_value=default_cfg,
        description="Path to YAML file listing camera serials and RTSP settings.",
    )

    return LaunchDescription([
        cfg_arg,
        OpaqueFunction(function=_spawn_nodes),
    ])