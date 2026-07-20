"""Deterministic value types shared by Somnia's editor and runtime."""

from __future__ import annotations

import math


class Vec3:
    """A small immutable-by-convention three-dimensional vector."""

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    @classmethod
    def zero(cls) -> "Vec3":
        return cls(0.0, 0.0, 0.0)

    @classmethod
    def one(cls) -> "Vec3":
        return cls(1.0, 1.0, 1.0)

    @classmethod
    def from_value(cls, value: object) -> "Vec3":
        if isinstance(value, cls):
            return value.copy()
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return cls(value[0], value[1], value[2])
        if isinstance(value, dict):
            return cls(value.get("x", 0.0), value.get("y", 0.0), value.get("z", 0.0))
        raise TypeError("Vec3 requires another Vec3, a three-item sequence, or a mapping")

    def copy(self) -> "Vec3":
        return Vec3(self.x, self.y, self.z)

    def to_list(self) -> list[float]:
        return [self.x, self.y, self.z]

    def dot(self, other: "Vec3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Vec3") -> "Vec3":
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def length_squared(self) -> float:
        return self.dot(self)

    def length(self) -> float:
        return math.sqrt(self.length_squared())

    def normalized(self) -> "Vec3":
        magnitude = self.length()
        if magnitude == 0.0:
            return Vec3.zero()
        return self / magnitude

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vec3":
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> "Vec3":
        return self * scalar

    def __truediv__(self, scalar: float) -> "Vec3":
        if scalar == 0.0:
            raise ZeroDivisionError("cannot divide Vec3 by zero")
        return Vec3(self.x / scalar, self.y / scalar, self.z / scalar)

    def __neg__(self) -> "Vec3":
        return Vec3(-self.x, -self.y, -self.z)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Vec3)
            and self.x == other.x
            and self.y == other.y
            and self.z == other.z
        )

    def __repr__(self) -> str:
        return f"Vec3({self.x!r}, {self.y!r}, {self.z!r})"


class Quaternion:
    """Quaternion rotation stored as x, y, z, w."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        w: float = 1.0,
    ) -> None:
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.w = float(w)

    @classmethod
    def identity(cls) -> "Quaternion":
        return cls(0.0, 0.0, 0.0, 1.0)

    @classmethod
    def from_value(cls, value: object) -> "Quaternion":
        if isinstance(value, cls):
            return value.copy()
        if isinstance(value, (list, tuple)) and len(value) == 4:
            return cls(value[0], value[1], value[2], value[3])
        if isinstance(value, dict):
            return cls(
                value.get("x", 0.0),
                value.get("y", 0.0),
                value.get("z", 0.0),
                value.get("w", 1.0),
            )
        raise TypeError("Quaternion requires another Quaternion, a four-item sequence, or a mapping")

    def copy(self) -> "Quaternion":
        return Quaternion(self.x, self.y, self.z, self.w)

    def to_list(self) -> list[float]:
        return [self.x, self.y, self.z, self.w]

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y + self.z * self.z + self.w * self.w

    def normalized(self) -> "Quaternion":
        magnitude = math.sqrt(self.length_squared())
        if magnitude == 0.0:
            return Quaternion.identity()
        return Quaternion(
            self.x / magnitude,
            self.y / magnitude,
            self.z / magnitude,
            self.w / magnitude,
        )

    def __mul__(self, other: "Quaternion") -> "Quaternion":
        return Quaternion(
            self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
            self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
            self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w,
            self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z,
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Quaternion)
            and self.x == other.x
            and self.y == other.y
            and self.z == other.z
            and self.w == other.w
        )

    def __repr__(self) -> str:
        return f"Quaternion({self.x!r}, {self.y!r}, {self.z!r}, {self.w!r})"


class Transform:
    """Position, rotation, and scale in parent-local space."""

    def __init__(
        self,
        position: Vec3 | None = None,
        rotation: Quaternion | None = None,
        scale: Vec3 | None = None,
    ) -> None:
        self.position = position.copy() if position is not None else Vec3.zero()
        self.rotation = rotation.copy() if rotation is not None else Quaternion.identity()
        self.scale = scale.copy() if scale is not None else Vec3.one()

    @classmethod
    def identity(cls) -> "Transform":
        return cls()

    @classmethod
    def from_value(cls, value: object) -> "Transform":
        if isinstance(value, cls):
            return value.copy()
        if isinstance(value, dict):
            return cls(
                Vec3.from_value(value.get("position", [0.0, 0.0, 0.0])),
                Quaternion.from_value(value.get("rotation", [0.0, 0.0, 0.0, 1.0])),
                Vec3.from_value(value.get("scale", [1.0, 1.0, 1.0])),
            )
        raise TypeError("Transform requires another Transform or a mapping")

    def copy(self) -> "Transform":
        return Transform(self.position, self.rotation, self.scale)

    def to_dict(self) -> dict[str, list[float]]:
        return {
            "position": self.position.to_list(),
            "rotation": self.rotation.to_list(),
            "scale": self.scale.to_list(),
        }

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Transform)
            and self.position == other.position
            and self.rotation == other.rotation
            and self.scale == other.scale
        )

    def __repr__(self) -> str:
        return (
            "Transform(position="
            f"{self.position!r}, rotation={self.rotation!r}, scale={self.scale!r})"
        )
