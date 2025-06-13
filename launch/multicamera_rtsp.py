#!/usr/bin/env python3
"""ROS 2 launch file that spins up one *image2rtsp* node per camera
listed in *camera_config.yaml*.

Each image2rtsp node subscribes to the compressed JPEG topic coming from the
HikRobot driver and exposes it as an RTSP mount‐point that the FE can open.

Usage (from the app_one workspace):

```bash
ros2 launch image2rtsp multi_camera_rtsp_launch.py \
    camera_config:=/absolute/path/to/camera_config.yaml
```

If *camera_config* is omitted, the default is
`$HOME/workspaces/app_one/config/camera_config.yaml`.

Example `camera_config.yaml` structure:
```yaml
base_port: 8556  # optional; starting port if "port" missing on a camera
cameras:
  - serial: DA6102933
    mount_point: cam1  # optional; defaults to cam<index>
    port: 8556         # optional; auto‐increment when omitted
  - serial: DA6102934  # ↑ same pattern for up to 6 cameras
```

The resulting RTSP URLs will be:
```
rtsp://<edge_ip>:8556/cam1
rtsp://<edge_ip>:8557/cam2
...
```
"""

import os
import yaml
from typing import List

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def _load_config(cfg_path: str) -> dict:
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"camera_config file not found: {cfg_path}")
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)


def _create_nodes(context, *_) -> List[Node]:
    cfg_file = LaunchConfiguration("camera_config").perform(context)
    cfg = _load_config(cfg_file)

    base_port = cfg.get("base_port", 8556)
    cam_list = cfg.get("cameras", [])

    launch_entities: List[Node] = []
    for idx, cam in enumerate(cam_list):
        serial = cam["serial"]
        port = cam.get("port", base_port + idx)
        mount = cam.get("mount_point", f"cam{idx + 1}")
        topic = cam.get("topic", f"/hikrobot/{serial}/compressed")

        launch_entities.append(
            Node(
                package="image2rtsp",
                executable="image2rtsp_node",
                name=f"image2rtsp_{serial}",
                parameters=[{
                    "topic": topic,
                    "mount_point": mount,
                    "port": port,
                    "use_compressed": True,
                }],
                output="screen",
            )
        )

        # Log the generated URL for convenience
        launch_entities.append(
            LogInfo(msg=f"[multi_cam_rtsp] {serial} ➜ rtsp://<edge_ip>:{port}/{mount}")
        )

    return launch_entities


def generate_launch_description() -> LaunchDescription:
    config_arg = DeclareLaunchArgument(
        "camera_config",
        default_value=os.path.expanduser("~/workspaces/RTSP/config/camera_config.yaml"),
        description="Path to YAML file that lists camera serials and RTSP settings",
    )

    return LaunchDescription([
        config_arg,
        OpaqueFunction(function=_create_nodes),
    ])