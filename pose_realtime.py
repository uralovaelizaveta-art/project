import math
import time
from dataclasses import dataclass

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


@dataclass
class Point2D:
    x: float
    y: float
    visibility: float = 1.0


class PoseModel:
    """Обёртка над MediaPipe Pose Landmarker."""

    def __init__(self, model_path: str, min_confidence: float = 0.5):
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=min_confidence,
            min_pose_presence_confidence=min_confidence,
            min_tracking_confidence=min_confidence,
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def detect(self, frame_bgr, timestamp_ms: int):
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        return self.landmarker.detect_for_video(mp_image, timestamp_ms)

    def close(self):
        self.landmarker.close()


class PoseGeometry:
    """Работа с координатами, линиями и углами."""

    KEYPOINTS = {
        "nose": 0,
        "left_shoulder": 11,
        "right_shoulder": 12,
        "left_elbow": 13,
        "right_elbow": 14,
        "left_wrist": 15,
        "right_wrist": 16,
        "left_hip": 23,
        "right_hip": 24,
        "left_knee": 25,
        "right_knee": 26,
        "left_ankle": 27,
        "right_ankle": 28,
        "left_foot_index": 31,
        "left_heel": 29,
        "right_heel": 30,
        "right_foot_index": 32

    }

    # Соединения для отрисовки скелета
    CONNECTIONS = [
        ("left_shoulder", "right_shoulder"),
        ("left_shoulder", "left_elbow"),
        ("left_elbow", "left_wrist"),
        ("right_shoulder", "right_elbow"),
        ("right_elbow", "right_wrist"),
        ("left_shoulder", "left_hip"),
        ("right_shoulder", "right_hip"),
        ("left_hip", "right_hip"),
        ("left_hip", "left_knee"),
        ("left_knee", "left_ankle"),
        ("right_hip", "right_knee"),
        ("right_knee", "right_ankle"),
        ("left_ankle", "left_foot_index"),
        ("left_ankle", "left_heel"),
        ("left_heel", "left_foot_index"),
        ("right_ankle", "right_foot_index"),
        ("right_ankle", "right_heel"),
        ("right_heel", "right_foot_index")

    ]

    # Углы: (точка A, вершина B, точка C) -> угол между прямыми BA и BC
    ANGLES = {
        "left_elbow": ("left_shoulder", "left_elbow", "left_wrist"),
        "right_elbow": ("right_shoulder", "right_elbow", "right_wrist"),
        "left_knee": ("left_hip", "left_knee", "left_ankle"),
        "right_knee": ("right_hip", "right_knee", "right_ankle"),
        "left_shoulder": ("left_elbow", "left_shoulder", "left_hip"),
        "right_shoulder": ("right_elbow", "right_shoulder", "right_hip"),
        "left_hip": ("left_shoulder", "left_hip", "left_knee"),
        "right_hip": ("right_shoulder", "right_hip", "right_knee"),
    }

    @staticmethod
    def extract_points(landmarks, frame_w: int, frame_h: int) -> dict[str, Point2D]:
        points = {}
        for name, idx in PoseGeometry.KEYPOINTS.items():
            lm = landmarks[idx]
            points[name] = Point2D(
                x=lm.x * frame_w,
                y=lm.y * frame_h,
                visibility=lm.visibility,
            )
        return points

    @staticmethod
    def angle_at_vertex(a: Point2D, b: Point2D, c: Point2D) -> float:
        """Угол в вершине b между прямыми ba и bc (в градусах)."""
        v1 = (a.x - b.x, a.y - b.y)
        v2 = (c.x - b.x, c.y - b.y)

        len1 = math.hypot(v1[0], v1[1])
        len2 = math.hypot(v2[0], v2[1])
        if len1 == 0 or len2 == 0:
            return float("nan")

        cos_angle = (v1[0] * v2[0] + v1[1] * v2[1]) / (len1 * len2)
        cos_angle = max(-1.0, min(1.0, cos_angle))
        return math.degrees(math.acos(cos_angle))

    @classmethod
    def compute_angles(cls, points: dict[str, Point2D]) -> dict[str, float]:
        angles = {}
        for name, (a_name, b_name, c_name) in cls.ANGLES.items():
            angles[name] = cls.angle_at_vertex(points[a_name], points[b_name], points[c_name])
        return angles

    @classmethod
    def draw_skeleton(cls, frame, points: dict[str, Point2D]):
        for a_name, b_name in cls.CONNECTIONS:
            a = points[a_name]
            b = points[b_name]
            if a.visibility < 0.5 or b.visibility < 0.5:
                continue
            cv2.line(
                frame,
                (int(a.x), int(a.y)),
                (int(b.x), int(b.y)),
                (254, 125, 125),
                2,
            )

        for name, p in points.items():
            if p.visibility < 0.5:
                continue
            cv2.circle(frame, (int(p.x), int(p.y)), 3, (255, 255, 255), -1)
            cv2.putText(
                frame,
                name,
                (int(p.x) + 5, int(p.y) - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (255, 255, 0),
                1,
                cv2.LINE_AA,
            )


class DataPrinter:
    """Печать данных с интервалом."""

    def __init__(self, interval_sec: float = 1.0):
        self.interval_sec = interval_sec
        self.last_print_time = 0.0

    def should_print(self) -> bool:
        now = time.time()
        if now - self.last_print_time >= self.interval_sec:
            self.last_print_time = now
            return True
        return False

    @staticmethod
    def print_data(points: dict[str, Point2D], angles: dict[str, float]):
        print("=" * 70)
        print("КООРДИНАТЫ ТОЧЕК (px):")
        for name, p in points.items():
            print(
                f"  {name:>15}: x={p.x:7.1f}, y={p.y:7.1f}, "
                f"visibility={p.visibility:.2f}"
            )

        print("\nУГЛЫ МЕЖДУ ПРЯМЫМИ (градусы):")
        for name, angle in angles.items():
            if math.isnan(angle):
                print(f"  {name:>15}: n/a")
            else:
                print(f"  {name:>15}: {angle:6.1f}°")


class RealTimePoseApp:
    def __init__(self, model_path: str, camera_id: int = 0, print_interval: float = 0.5):
        self.model = PoseModel(model_path)
        self.geometry = PoseGeometry()
        self.printer = DataPrinter(interval_sec=print_interval)
        self.cap = cv2.VideoCapture(camera_id)

        if not self.cap.isOpened():
            raise RuntimeError("Не удалось открыть камеру.")

    def run(self):
        print("Запуск. Нажмите 'Esc' для выхода.")
        start_time = time.time()

        while True:
            ok, frame = self.cap.read()
            if not ok:
                print("Ошибка чтения кадра.")
                break

            frame = cv2.flip(frame, 1)
            timestamp_ms = int((time.time() - start_time) * 1000)

            result = self.model.detect(frame, timestamp_ms)
            h, w = frame.shape[:2]

            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]
                points = self.geometry.extract_points(landmarks, w, h)
                angles = self.geometry.compute_angles(points)

                self.geometry.draw_skeleton(frame, points)

                if self.printer.should_print():
                    self.printer.print_data(points, angles)

            cv2.imshow("Pose Landmarker. Real Time", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

        self.cap.release()
        self.model.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    MODEL_PATH = "pose_landmarker_heavy.task"
    app = RealTimePoseApp(model_path=MODEL_PATH, camera_id=0, print_interval=0.5)
    app.run()


