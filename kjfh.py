import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class PoseModel:
    """Обертка над MediaPipe Pose Landmarker."""
    def __init__(self, model_path: str, min_pose_confidence: float = 0.5):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=min_pose_confidence,
            min_pose_presence_confidence=min_pose_confidence,
            min_tracking_confidence=min_pose_confidence,
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def detect(self, frame_bgr, timestamp_ms: int):
        """Возвращает результат детекции для одного кадра."""
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        return result

    def close(self):
        self.landmarker.close()


class PosePointExtractor:
    """Извлекает и форматирует координаты интересующих ключевых точек."""
    # Индексы соответствуют BlazePose (MediaPipe Pose Landmarker)
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
    }

    @staticmethod
    def extract(landmarks, frame_w: int, frame_h: int):
        """
        Возвращает словарь:
        {
          "left_shoulder": {"x_norm":..., "y_norm":..., "x_px":..., "y_px":..., "visibility":...},
          ...
        }
        """
        points = {}
        for name, idx in PosePointExtractor.KEYPOINTS.items():
            lm = landmarks[idx]
            x_norm, y_norm = lm.x, lm.y
            x_px = int(x_norm * frame_w)
            y_px = int(y_norm * frame_h)

            points[name] = {
                "x_norm": round(x_norm, 4),
                "y_norm": round(y_norm, 4),
                "z": round(lm.z, 4),
                "x_px": x_px,
                "y_px": y_px,
                "visibility": round(lm.visibility, 4),
            }
        return points


class RealTimePoseApp:
    def __init__(self, model_path: str, camera_id: int = 0):
        self.model = PoseModel(model_path=model_path)
        self.extractor = PosePointExtractor()
        self.cap = cv2.VideoCapture(camera_id)

        if not self.cap.isOpened():
            raise RuntimeError("Не удалось открыть камеру.")

    def run(self):
        print("Нажмите 'q' для выхода.")
        while True:
            ok, frame = self.cap.read()
            if not ok:
                print("Ошибка чтения кадра.")
                break

            # Timestamp для режима VIDEO (должен монотонно расти)
            timestamp_ms = int(cv2.getTickCount() / cv2.getTickFrequency() * 1000)

            result = self.model.detect(frame, timestamp_ms)
            h, w = frame.shape[:2]

            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]  # первая найденная поза
                points = self.extractor.extract(landmarks, w, h)

                # Печать координат в консоль
                print("-" * 60)
                for name, p in points.items():
                    print(
                        f"{name:>15}: "
                        f"norm=({p['x_norm']:.4f}, {p['y_norm']:.4f}, z={p['z']:.4f}) "
                        f"px=({p['x_px']}, {p['y_px']}) vis={p['visibility']:.2f}"
                    )

                # Визуализация точек на кадре
                for name, p in points.items():
                    cv2.circle(frame, (p["x_px"], p["y_px"]), 5, (0, 255, 0), -1)
                    cv2.putText(
                        frame,
                        name,
                        (p["x_px"] + 6, p["y_px"] - 6),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.4,
                        (0, 255, 255),
                        1,
                        cv2.LINE_AA,
                    )

            cv2.imshow("Real-time Pose Landmarker", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        self.cap.release()
        self.model.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    MODEL_PATH = "pose_landmarker_full.task"

    app = RealTimePoseApp(model_path=MODEL_PATH, camera_id=0)
    app.run()