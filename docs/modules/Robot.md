# Robot Module

> **Source**: `src/Mod/Robot/` · ~95 .cpp · ~43 .h · ~6 .py  
> **Dependencies**: FreeCADApp, Part, KDL

## 📋 Overview
Robot simulation and offline programming. Models 6-axis industrial robots with trajectory planning.

## Key Features
| Feature | Description |
|---|---|
| `Robot6Axis` | 6-DOF robot arm model |
| `RobotObject` | Robot instance in document |
| `TrajectoryObject` | Planned motion path |
| `Waypoint` | Position/orientation target |
| `Edge2TracParameter` | Convert edges to robot trajectories |
| `Simulation` | Playback robot motion |

Uses KDL (Kinematics and Dynamics Library) for forward/inverse kinematics.

⚠️ **Note**: The Robot module has been relatively unmaintained and may see limited development.

---
*Part of the [FreeCAD Documentation Hub](../README.md)*
