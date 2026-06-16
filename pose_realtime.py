import sys
sys.dont_write_bytecode = True

import math
import threading
import time
from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from movement_rules import (
    CLASSIFIER_SETTINGS,
    MOVEMENT_RULES,
    POSITION_FLOOR_REQUIREMENTS,
    SEQUENCE_RULES,
    TIMELINE_SETTINGS,
    VISIBILITY_PRESETS,
)
from movement_timeline import MovementTimeline, SequenceDetector, TimelineSettings


@dataclass
class Point2D: #Класс для хранения координат и видимости ключевых точек позы.
    x: float
    y: float
    visibility: float = 1.0


class PoseModel: 
    #Обёртка над MediaPipe Pose Landmarker.

    def __init__(self, model_path: str, min_confidence: float = 0.5): #Инициализация модели MediaPipe Pose Landmarker с заданным путем к модели и минимальной уверенностью для обнаружения позы.
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=min_confidence,
            min_pose_presence_confidence=min_confidence,
            min_tracking_confidence=min_confidence,
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def detect(self, frame_bgr, timestamp_ms: int): #Преобразование кадра из BGR в RGB, создание объекта mp.Image и передача его в модель для получения позы. Результат — объект с данными о позе, который можно использовать для извлечения ключевых точек.
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return self.detect_rgb(frame_rgb, timestamp_ms)

    def detect_rgb(self, frame_rgb, timestamp_ms: int):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        return self.landmarker.detect_for_video(mp_image, timestamp_ms)

    def close(self): #Закрытие модели и освобождение ресурсов.
        self.landmarker.close()


class PoseGeometry:
    #Работа с координатами, линиями и углами.

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
        "left_ankle":("left_knee", "left_ankle", "left_foot_index"),
        "right_ankle":("right_knee", "right_ankle", "right_foot_index")
    }

    @staticmethod
    def extract_points(landmarks, frame_w: int, frame_h: int) -> dict[str, Point2D]: #Преобразование нормализованных координат ключевых точек из MediaPipe в пиксельные координаты на кадре, а также сохранение информации о видимости каждой точки. Результат — словарь с именами точек и их координатами и видимостью.
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
    def angle_at_vertex(a: Point2D, b: Point2D, c: Point2D) -> float: # метод для вычисления угла в вершине b между прямыми ba и bc, который используется для оценки позы и классификации движений. Угол возвращается в градусах. Если одна из точек совпадает (длина вектора 0), возвращается NaN.
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
    def compute_angles(cls, points: dict[str, Point2D]) -> dict[str, float]: #Вычисление углов между прямыми, образованными ключевыми точками, для оценки позы и классификации движений.
        angles = {}
        for name, (a_name, b_name, c_name) in cls.ANGLES.items():
            angles[name] = cls.angle_at_vertex(points[a_name], points[b_name], points[c_name])
        return angles

    # Расстояния между парами точек (для позиций ног)
    DISTANCE_PAIRS = {
        "ankles": ("left_ankle", "right_ankle"),
        "heels": ("left_heel", "right_heel"),
        "toes": ("left_foot_index", "right_foot_index"),
        "left_heel_right_toe": ("left_heel", "right_foot_index"),
        "right_heel_left_toe": ("right_heel", "left_foot_index"),
    }

    @staticmethod
    def _point_distance(a: Point2D, b: Point2D) -> float: #евклидово расстояние между двумя точками в пикселях
        return math.hypot(a.x - b.x, a.y - b.y)

    @classmethod
    def compute_distances(cls, points: dict[str, Point2D]) -> dict[str, float]: #Расстояния между точками ног в пикселях и нормализованные относительно ширины бёдер (hip_width) — удобнее для правил.
        hip_w = cls._point_distance(points["left_hip"], points["right_hip"])
        if hip_w < 1:
            hip_w = 1.0

        distances: dict[str, float] = {"hip_width": hip_w}

        for name, (p1, p2) in cls.DISTANCE_PAIRS.items():
            d = cls._point_distance(points[p1], points[p2])
            distances[name] = d
            distances[f"{name}_norm"] = d / hip_w

        la, ra = points["left_ankle"], points["right_ankle"]
        lh, rh = points["left_heel"], points["right_heel"]

        distances["ankle_depth"] = abs(la.y - ra.y)
        distances["ankle_depth_norm"] = distances["ankle_depth"] / hip_w
        distances["ankle_x_gap"] = abs(la.x - ra.x)
        distances["ankle_x_gap_norm"] = distances["ankle_x_gap"] / hip_w
        distances["heel_depth"] = abs(lh.y - rh.y)
        distances["heel_depth_norm"] = distances["heel_depth"] / hip_w

        return distances

    @classmethod
    def compute_foot_state(cls, points: dict[str, Point2D]) -> dict[str, float]: #метод для оценки состояния ног, включая видимость ключевых точек и признаки «ноги на полу», которые используются в правилах классификации позиций.
        #Видимость точек ног и признаки «ноги на полу». toe_above_ankle_norm > 0 — носок выше лодыжки (поднят с пола).
        hip_w = cls._point_distance(points["left_hip"], points["right_hip"])
        if hip_w < 1:
            hip_w = 1.0

        la = points["left_ankle"]
        ra = points["right_ankle"]
        lh = points["left_heel"]
        rh = points["right_heel"]
        lt = points["left_foot_index"]
        rt = points["right_foot_index"]

        left_toe_lift = max(0.0, (la.y - lt.y) / hip_w)
        right_toe_lift = max(0.0, (ra.y - rt.y) / hip_w)

        return {
            "left_heel_visibility": lh.visibility,
            "right_heel_visibility": rh.visibility,
            "left_ankle_visibility": la.visibility,
            "right_ankle_visibility": ra.visibility,
            "left_toe_visibility": lt.visibility,
            "right_toe_visibility": rt.visibility,
            "ankle_y_diff_norm": abs(la.y - ra.y) / hip_w,
            "toe_y_diff_norm": abs(lt.y - rt.y) / hip_w,
            "heel_y_diff_norm": abs(lh.y - rh.y) / hip_w,
            "left_toe_above_ankle_norm": left_toe_lift,
            "right_toe_above_ankle_norm": right_toe_lift,
            "max_toe_lift_norm": max(left_toe_lift, right_toe_lift),
        }

    @classmethod
    def draw_skeleton(cls, frame, points: dict[str, Point2D]): #Отрисовка скелета и ключевых точек на кадре для визуализации.
        for a_name, b_name in cls.CONNECTIONS:
            a = points[a_name]
            b = points[b_name]
            if a.visibility < 0.45 or b.visibility < 0.45:
                continue
            cv2.line(
                frame,
                (int(a.x), int(a.y)),
                (int(b.x), int(b.y)),
                (254, 255, 125),
                2,
            )

        for name, p in points.items():
            if p.visibility < 0.1:
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


@dataclass
class ClassificationResult: #Результат классификации движения, содержащий идентификатор, название и уверенность.
    movement_id: str
    movement_name: str
    confidence: float


class MovementClassifier: # Класс для классификации движений на основе углов и расстояний, используя правила из movement_rules.py.

    def __init__(self, rules: list[dict] | None = None, settings: dict | None = None): #Инициализация классификатора с правилами и настройками. Если не переданы, используются значения по умолчанию из movement_rules.py.
        self.rules = rules if rules is not None else MOVEMENT_RULES
        self.settings = settings if settings is not None else CLASSIFIER_SETTINGS

    @staticmethod
    def _score_angle(value: float, low: float, high: float) -> float: #оценка соответствия одного угла заданному диапазону в правилах движения.
        #1.0 — угол в диапазоне, меньше — чем дальше от диапазона.
        if math.isnan(value):
            return 0.0
        if low <= value <= high:
            return 1.0
        dist = low - value if value < low else value - high
        return max(0.0, 1.0 - dist / 40.0)

    def _score_range(self, value: float, low: float, high: float) -> float: #оценка соответствия одного значения (угла, расстояния или видимости) заданному диапазону в правилах
        return self._score_angle(value, low, high)

    def _score_angle_set(self, angles: dict[str, float], angle_rules: dict) -> float: #оценка соответствия текущих данных правилам по углам суставов
        if not angle_rules:
            return 0.0
        scores = [
            self._score_range(angles.get(name, float("nan")), low, high)
            for name, (low, high) in angle_rules.items()
        ]
        return sum(scores) / len(scores)

    def _score_distance_set(self, distances: dict[str, float], distance_rules: dict) -> float: #оценка соответствия текущих данных правилам расстояний между точками ног
        if not distance_rules:
            return 0.0
        scores = [
            self._score_range(distances.get(name, float("nan")), low, high)
            for name, (low, high) in distance_rules.items()
        ]
        return sum(scores) / len(scores)

    @staticmethod
    def _resolve_visibility_range(rule_value) -> tuple[float, float]:#определяет, какие пороги видимости применять для оценки соответствия правилам видимости точек ног
        if isinstance(rule_value, str):
            return VISIBILITY_PRESETS[rule_value]
        return rule_value

    def _score_visibility_set( #оценка соответствия текущих данных правилам видимости точек ног
        self, foot_state: dict[str, float], visibility_rules: dict
    ) -> float:
        if not visibility_rules:
            return 0.0

        scores = []
        for point, rule_value in visibility_rules.items():
            key = f"{point}_visibility" if not point.endswith("_visibility") else point
            low, high = self._resolve_visibility_range(rule_value)
            scores.append(self._score_range(foot_state.get(key, 0.0), low, high))
        return sum(scores) / len(scores)

    def _score_foot_on_floor( #оценка соответствия текущих данных правилам «нога на полу»
        self, foot_state: dict[str, float], floor_rules: dict
    ) -> float:
        if not floor_rules:
            return 0.0
        scores = [
            self._score_range(foot_state.get(name, float("nan")), low, high)
            for name, (low, high) in floor_rules.items()
        ]
        return sum(scores) / len(scores)

    def _floor_rules_for(self, rule: dict, block: dict) -> dict: #определяет, какие правила для оценки «ноги на полу» применять к данному блоку правил движения
        merged = {}
        rule_id = str(rule.get("id", ""))
        if rule.get("requires_floor") or rule_id.startswith("pos"):
            merged.update(POSITION_FLOOR_REQUIREMENTS)
        merged.update(block.get("foot_on_floor", {}))
        return merged

    @staticmethod
    def _block_has_rules(block: dict) -> bool: #проверяет, есть ли в блоке правила для оценки (углы, расстояния, видимость или ноги на полу)
        return any(
            block.get(key)
            for key in ("angles", "distances", "visibility", "foot_on_floor")
        )

    def _score_block( #оценка соответствия текущих данных одному блоку правил движения
        self,
        angles: dict[str, float],
        distances: dict[str, float],
        foot_state: dict[str, float],
        rule: dict,
        block: dict,
    ) -> float:
        parts = []
        if block.get("angles"):
            parts.append(self._score_angle_set(angles, block["angles"]))
        if block.get("distances"):
            parts.append(self._score_distance_set(distances, block["distances"]))
        if block.get("visibility"):
            parts.append(self._score_visibility_set(foot_state, block["visibility"]))

        floor_rules = self._floor_rules_for(rule, block)
        if floor_rules:
            parts.append(self._score_foot_on_floor(foot_state, floor_rules))

        return sum(parts) / len(parts) if parts else 0.0

    def _score_movement( #оценка соответствия текущих данных правилам движения
        self,
        angles: dict[str, float],
        distances: dict[str, float],
        foot_state: dict[str, float],
        rule: dict,
    ) -> float:
        if self._block_has_rules(rule):
            return self._score_block(angles, distances, foot_state, rule, rule)

        variants = rule.get("variants", [])
        if variants:
            variant_scores = [
                self._score_block(angles, distances, foot_state, rule, variant)
                for variant in variants
                if self._block_has_rules(variant)
            ]
            return max(variant_scores) if variant_scores else 0.0

        return 0.0

    def classify( #классификация движения
        self,
        angles: dict[str, float],
        distances: dict[str, float] | None = None,
        foot_state: dict[str, float] | None = None,
    ) -> ClassificationResult:
        distances = distances or {}
        foot_state = foot_state or {}
        unknown_name = self.settings.get("unknown_name", "Не определено")
        min_confidence = self.settings.get("min_confidence", 0.5)

        best_id = "unknown"
        best_name = unknown_name
        best_score = 0.0

        for rule in self.rules:
            score = self._score_movement(angles, distances, foot_state, rule)
            rule_min = rule.get("min_score", min_confidence)
            if score >= rule_min and score > best_score:
                best_score = score
                best_id = rule.get("id", "unknown")
                best_name = rule.get("name", unknown_name)

        if best_score < min_confidence:
            return ClassificationResult("unknown", unknown_name, round(best_score, 2))

        return ClassificationResult(best_id, best_name, round(best_score, 2))


class DataPrinter: #Класс для печати данных с интервалом в консоль, чтобы не засорять её слишком частыми обновлениями.

    def __init__(self, interval_sec: float = 0.5): #интервал между печатью данных в консоль
        self.interval_sec = interval_sec
        self.last_print_time = 0.0

    def should_print(self) -> bool: #проверяет, прошло ли достаточно времени с последней печати
        now = time.time()
        if now - self.last_print_time >= self.interval_sec:
            self.last_print_time = now
            return True
        return False

    @staticmethod
    def print_data( #печать данных в консоль
        points: dict[str, Point2D],
        angles: dict[str, float],
        distances: dict[str, float],
        foot_state: dict[str, float],
        classification: ClassificationResult,
        timeline: MovementTimeline | None = None,
    ):
        print("=" * 70)
        print(f"СЕЙЧАС: {classification.movement_name} "
              f"(уверенность: {classification.confidence:.0%})")

        if timeline and timeline.events:
            print("\nИСТОРИЯ ДВИЖЕНИЙ:")
            for line in timeline.format_history_lines(8):
                print(f"  {line}")

        print("\nУГЛЫ МЕЖДУ ПРЯМЫМИ (градусы):")
        for name, angle in angles.items():
            if math.isnan(angle):
                print(f"  {name:>22}: n/a")
            else:
                print(f"  {name:>22}: {angle:6.1f}°")

        # print("\nВИДИМОСТЬ И НОГИ НА ПОЛУ (для позиций):")
        # for name, value in foot_state.items():
        #     if name.endswith("_visibility"):
        #         print(f"  {name:>28}: {value:5.2f}")
        #     elif name.endswith("_norm"):
        #         print(f"  {name:>28}: {value:6.3f}")

        # print("\nРАССТОЯНИЯ (норм. к бёдрам):")
        # for name in sorted(distances):
        #     if not name.endswith("_norm"):
        #         continue
        #     print(f"  {name:>28}: {distances[name]:6.3f}")


class RealTimePoseApp: #Главный класс приложения, который объединяет все компоненты и запускает цикл обработки видео.
    def __init__(self, model_path: str, camera_id: int = 0, print_interval: float = 0.5):
        self.model = PoseModel(model_path)
        self.geometry = PoseGeometry()
        self.classifier = MovementClassifier()
        self.printer = DataPrinter(interval_sec=print_interval)
        self.timeline = MovementTimeline(
            settings=TimelineSettings(
                min_hold_sec=TIMELINE_SETTINGS.get("min_hold_sec", 0.15),
                cooldown_sec=TIMELINE_SETTINGS.get("cooldown_sec", 0.8),
                max_history=TIMELINE_SETTINGS.get("max_history", 50),
            ),
            session_log_path=TIMELINE_SETTINGS.get(
                "session_log_path", "data/movement_session.json"
            ),
        )
        self.sequence_detector = SequenceDetector(SEQUENCE_RULES)
        self.cap = cv2.VideoCapture(camera_id)

        if not self.cap.isOpened():
            raise RuntimeError("Не удалось открыть камеру.")

    def run(self): #главный цикл приложения
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
                distances = self.geometry.compute_distances(points)
                foot_state = self.geometry.compute_foot_state(points)

                self.geometry.draw_skeleton(frame, points)

                classification = self.classifier.classify(angles, distances, foot_state)
                self._draw_movement_label(frame, classification)

                added = self.timeline.update(
                    classification.movement_id,
                    classification.movement_name,
                    classification.confidence,
                )
                if added:
                    seq = self.sequence_detector.check(self.timeline)
                    if seq:
                        self.timeline.add_sequence(seq)
                        print(f"\n>>> ПОСЛЕДОВАТЕЛЬНОСТЬ: {seq.sequence_name} "
                              f"({seq.time_sec:.1f}s)")

                # self._draw_history(frame, self.timeline)

                if self.printer.should_print():
                    self.printer.print_data(
                        points, angles, distances, foot_state,
                        classification, self.timeline,
                    )

            cv2.imshow("Pose Landmarker. Real Time", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

        log_path = self.timeline.export_json()
        print(f"\nИстория сохранена: {log_path}")
        print(f"Записано движений: {len(self.timeline.events)}, "
              f"последовательностей: {len(self.timeline.sequences_detected)}")

        self.cap.release()
        self.model.close()
        cv2.destroyAllWindows()

    @staticmethod
    def _draw_movement_label(frame, classification: ClassificationResult): #вывод текущего движения на экран
        label = f"Now: {classification.movement_name} ({classification.confidence:.0%})"
        cv2.rectangle(frame, (10, 10), (10 + len(label) * 11, 45), (0, 0, 0), -1)
        cv2.putText(
            frame, label, (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA,
        )

    @staticmethod
    def _draw_history(frame, timeline: MovementTimeline): #вывод истории движений на экран
        lines = ["History:"] + timeline.format_history_lines(5)
        y = 55
        for line in lines:
            cv2.putText(
                frame, line, (10, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA,
            )
            y += 18


_pose_model = None
_classifier = None
_pose_model_lock = threading.Lock()
_last_realtime_timestamp_ms = -1

def init_model(model_path: str): #Инициализация модели и классификатора. Гарантирует, что модель будет загружена только один раз, даже если несколько сессий обрабатывают кадры одновременно.
    global _pose_model, _classifier
    if _pose_model is None:
        _pose_model = PoseModel(model_path, min_confidence=0.5)
        _classifier = MovementClassifier()


class RealtimeSession:#Обработка кадров для одного WebSocket-подключения.

    def __init__(self, model_path: str | None = None):
        if _pose_model is None:
            init_model(model_path or "pose_landmarker_heavy.task")

        self.timeline = MovementTimeline(
            settings=TimelineSettings(
                min_hold_sec=TIMELINE_SETTINGS.get("min_hold_sec", 0.15),
                cooldown_sec=TIMELINE_SETTINGS.get("cooldown_sec", 0.8),
                max_history=TIMELINE_SETTINGS.get("max_history", 50),
            ),
        )
        self.sequence_detector = SequenceDetector(SEQUENCE_RULES)

    def process_frame(self, frame_rgb: np.ndarray) -> dict: #Обработка одного кадра: получение позы, извлечение ключевых точек, вычисление углов и расстояний, классификация движения, обновление таймлайна и возвращение данных для API.
        global _last_realtime_timestamp_ms

        with _pose_model_lock:
            timestamp_ms = max(
                time.monotonic_ns() // 1_000_000,
                _last_realtime_timestamp_ms + 1,
            )
            result = _pose_model.detect_rgb(frame_rgb, timestamp_ms)
            _last_realtime_timestamp_ms = timestamp_ms

        h, w = frame_rgb.shape[:2]
        movement_id = "unknown"
        movement_name = CLASSIFIER_SETTINGS.get("unknown_name", "Не определено")
        confidence = 0.0
        pose_points = {}
        ready_for_detection = False

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            points = PoseGeometry.extract_points(landmarks, w, h)
            pose_points = {
                name: {
                    "x": round(point.x / w, 4),
                    "y": round(point.y / h, 4),
                    "visibility": round(point.visibility, 3),
                }
                for name, point in points.items()
            }
            ready_for_detection = self._is_ready_for_detection(points, w, h)
            if not ready_for_detection:
                movement_name = "Отойдите назад"
            else:
                angles = PoseGeometry.compute_angles(points)
                distances = PoseGeometry.compute_distances(points)
                foot_state = PoseGeometry.compute_foot_state(points)

                classification = _classifier.classify(angles, distances, foot_state)
                movement_id = classification.movement_id
                movement_name = classification.movement_name
                confidence = classification.confidence

                added = self.timeline.update(
                    movement_id,
                    movement_name,
                    confidence,
                )
                if added:
                    seq = self.sequence_detector.check(self.timeline)
                    if seq:
                        self.timeline.add_sequence(seq)

        return {
            "movement": movement_name,
            "movement_id": movement_id,
            "confidence": confidence,
            "ready_for_detection": ready_for_detection,
            "pose_points": pose_points,
            "movements": self.timeline.get_events_for_api(),
            "sequences": self.timeline.get_sequences_for_api(),
        }

    @staticmethod
    def _is_ready_for_detection(points: dict[str, Point2D], frame_w: int, frame_h: int) -> bool: #Проверка, достаточно ли видно ключевых точек и не слишком ли близко человек к камере, чтобы начинать классификацию позы. Это помогает избежать ложных срабатываний, когда человек слишком близко или слишком далеко от камеры.
        required_points = (
            "left_shoulder",
            "right_shoulder",
            "left_hip",
            "right_hip",
            "left_knee",
            "right_knee",
            "left_ankle",
            "right_ankle",
        )
        visible = [points[name] for name in required_points if points[name].visibility >= 0.35]
        if len(visible) < len(required_points):
            return False

        xs = [point.x / frame_w for point in visible]
        ys = [point.y / frame_h for point in visible]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        body_width = max_x - min_x
        body_height = max_y - min_y

        touches_edge = min_x < 0.03 or max_x > 0.97 or min_y < 0.03 or max_y > 0.97
        too_close = body_width > 0.85 or body_height > 0.9
        return not touches_edge and not too_close

    @classmethod
    def draw_skeleton(cls, frame, points: dict[str, Point2D]): #Отрисовка скелета и ключевых точек на кадре для визуализации.
        for a_name, b_name in cls.CONNECTIONS:
            a = points[a_name]
            b = points[b_name]
            if a.visibility < 0.45 or b.visibility < 0.45:
                continue
            cv2.line(
                frame,
                (int(a.x), int(a.y)),
                (int(b.x), int(b.y)),
                (254, 255, 125),
                2,
            )

        for name, p in points.items():
            if p.visibility < 0.1:
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

def process_frame(frame_np) -> dict: #Обратная совместимость для одиночных вызовов.
    session = RealtimeSession()
    return session.process_frame(frame_np)


if __name__ == "__main__":
    MODEL_PATH = "pose_landmarker_heavy.task"
    app = RealTimePoseApp(model_path=MODEL_PATH, camera_id=0, print_interval=0.5)
    app.run()


