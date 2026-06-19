"""
Volleyball serve trajectory simulation.

Edit the constants and force functions below to refine the physical model.
"""

from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# Physical constants — adjust these to match your model
# ---------------------------------------------------------------------------

GRAVITY = 9.81  # m/s²
AIR_DENSITY = 1.225  # kg/m³
BALL_MASS = 0.270  # kg  (official volleyball ~260–280 g)
BALL_RADIUS = 0.105  # m
BALL_AREA = np.pi * BALL_RADIUS**2
DRAG_COEFFICIENT = 0.47  # sphere; volleyball may be ~0.5
MAGNUS_COEFFICIENT = 0.25  # lift coefficient for spin (tune as needed)

# Court geometry (side-view, x = horizontal distance from serve line)
NET_DISTANCE = 9.0  # m from baseline to net
NET_HEIGHT_MEN = 2.43  # m
NET_HEIGHT_WOMEN = 2.24  # m
COURT_DEPTH = 9.0  # m opponent half-court depth
COURT_WIDTH = 9.0  # m (not used in 2-D side view)

# Integration
DT = 0.005  # s time step
MAX_TIME = 5.0  # s safety cap


# ---------------------------------------------------------------------------
# Force helpers — modify these to implement your equations
# ---------------------------------------------------------------------------

def gravity_force() -> np.ndarray:
    """Weight acts downward."""
    return np.array([0.0, -BALL_MASS * GRAVITY])


def drag_force(velocity: np.ndarray) -> np.ndarray:
    """
    Quadratic air drag: F_d = -½ ρ C_d A |v| v

    Opposes the direction of motion.
    """
    speed = np.linalg.norm(velocity)
    if speed < 1e-9:
        return np.zeros(2)
    return -0.5 * AIR_DENSITY * DRAG_COEFFICIENT * BALL_AREA * speed * velocity


def magnus_force(velocity: np.ndarray, spin_rpm: float) -> np.ndarray:
    """
    Magnus (lift) force from ball spin.

    Spin is about the axis perpendicular to the side-view plane (z-axis).
    Positive spin_rpm → topspin (jump serve): ball drops faster.
    Negative spin_rpm → backspin (float serve): ball hangs longer.

    Uses: F_m = ½ ρ C_L A (r ω / |v|) (ω̂ × v)
    Simplified 2-D cross product: ω̂ × v = (-ω v_y, ω v_x) with ω in rad/s.
    """
    speed = np.linalg.norm(velocity)
    if speed < 1e-9 or abs(spin_rpm) < 1e-9:
        return np.zeros(2)

    omega = spin_rpm * 2.0 * np.pi / 60.0  # rad/s
    spin_ratio = (BALL_RADIUS * abs(omega)) / speed
    cross = np.array([-omega * velocity[1], omega * velocity[0]])
    return 0.5 * AIR_DENSITY * MAGNUS_COEFFICIENT * BALL_AREA * spin_ratio * cross


def total_acceleration(
    velocity: np.ndarray, spin_rpm: float, include_drag: bool, include_magnus: bool
) -> np.ndarray:
    """Sum of forces divided by mass → acceleration vector."""
    force = gravity_force()
    if include_drag:
        force += drag_force(velocity)
    if include_magnus:
        force += magnus_force(velocity, spin_rpm)
    return force / BALL_MASS


# ---------------------------------------------------------------------------
# Trajectory integration (4th-order Runge–Kutta)
# ---------------------------------------------------------------------------

def _rk4_step(
    position: np.ndarray,
    velocity: np.ndarray,
    spin_rpm: float,
    include_drag: bool,
    include_magnus: bool,
    dt: float,
) -> tuple[np.ndarray, np.ndarray]:
    def accel(v: np.ndarray) -> np.ndarray:
        return total_acceleration(v, spin_rpm, include_drag, include_magnus)

    k1_v = accel(velocity)
    k1_x = velocity

    k2_v = accel(velocity + 0.5 * dt * k1_v)
    k2_x = velocity + 0.5 * dt * k1_v

    k3_v = accel(velocity + 0.5 * dt * k2_v)
    k3_x = velocity + 0.5 * dt * k2_v

    k4_v = accel(velocity + dt * k3_v)
    k4_x = velocity + dt * k3_v

    new_velocity = velocity + (dt / 6.0) * (k1_v + 2 * k2_v + 2 * k3_v + k4_v)
    new_position = position + (dt / 6.0) * (k1_x + 2 * k2_x + 2 * k3_x + k4_x)
    return new_position, new_velocity


def simulate_trajectory(
    speed: float,
    angle_deg: float,
    spin_rpm: float = 0.0,
    height: float = 2.5,
    net_height: float = NET_HEIGHT_MEN,
    include_drag: bool = True,
    include_magnus: bool = True,
) -> dict:
    """
    Simulate a volleyball serve trajectory.

    Parameters
    ----------
    speed : float
        Initial speed in m/s.
    angle_deg : float
        Launch angle above horizontal in degrees.
    spin_rpm : float
        Spin rate in revolutions per minute.
        Positive = topspin, negative = backspin (float serve).
    height : float
        Release height in metres (contact point).
    net_height : float
        Net height in metres (2.43 men, 2.24 women).
    include_drag : bool
        Include air-resistance term.
    include_magnus : bool
        Include Magnus (spin) force.

    Returns
    -------
    dict with keys:
        x, y       — lists of position samples (metres)
        stats      — computed summary statistics
    """
    angle_rad = np.radians(angle_deg)
    velocity = np.array([speed * np.cos(angle_rad), speed * np.sin(angle_rad)])
    position = np.array([0.0, height])

    xs: list[float] = [float(position[0])]
    ys: list[float] = [float(position[1])]
    max_height = height
    t = 0.0

    while t < MAX_TIME:
        position, velocity = _rk4_step(
            position, velocity, spin_rpm, include_drag, include_magnus, DT
        )
        t += DT

        xs.append(float(position[0]))
        ys.append(float(position[1]))
        max_height = max(max_height, float(position[1]))

        # Stop when ball hits the ground
        if position[1] <= 0.0:
            xs[-1] = float(position[0])
            ys[-1] = 0.0
            break

    # --- Statistics ---
    net_index = _height_at_distance(xs, ys, NET_DISTANCE)
    net_clearance = net_index - net_height if net_index is not None else None

    landing_x = xs[-1]
    in_bounds = NET_DISTANCE <= landing_x <= NET_DISTANCE + COURT_DEPTH

    stats = {
        "range_m": round(landing_x, 2),
        "max_height_m": round(max_height, 2),
        "flight_time_s": round(t, 2),
        "net_height_at_net_m": round(net_index, 2) if net_index is not None else None,
        "net_clearance_m": round(net_clearance, 2) if net_clearance is not None else None,
        "clears_net": net_clearance > 0 if net_clearance is not None else False,
        "lands_in_bounds": in_bounds,
        "initial_speed_ms": speed,
        "launch_angle_deg": angle_deg,
        "spin_rpm": spin_rpm,
    }

    return {"x": xs, "y": ys, "stats": stats}


def _height_at_distance(xs: list[float], ys: list[float], target_x: float) -> float | None:
    """Linearly interpolate ball height when x crosses target_x."""
    for i in range(1, len(xs)):
        if xs[i - 1] <= target_x <= xs[i]:
            frac = (target_x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + frac * (ys[i] - ys[i - 1])
    return None
