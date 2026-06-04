import cv2
import mediapipe as mp

# Загрузка модели Pose Landmarker из файла .task
try:
    pose_landmarker = mp.tasks.vision.PoseLandmarker.create_from_options(
        options=mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.BaseOptions(model_asset_path='pose_landmarker_full.task'),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            output_segmentation_masks=False,  # Маски не нужны для координат
        )
    )
except Exception as e:
    print("Ошибка при загрузке модели. Проверьте наличие файла 'pose_landmarker_full.task'.")
    raise SystemExit from e

# Открытие веб-камеры (0 — индекс камеры по умолчанию)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Не удалось открыть камеру.")
    raise SystemExit

print("Запуск обработки видео... Нажмите ESC для выхода.")

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        continue

    # Преобразование кадра BGR -> RGB и создание объекта VideoFrame
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    video_frame = mp.Image(image_format=mp.ImageFormat.RGB, data=rgb_frame)

    try:
        # Обработка кадра моделью
        result = pose_landmarker.process(video_frame)
    except Exception as e:
        print(f"Ошибка обработки кадра: {e}")
        break

    landmarks = result.pose_world_landmarks

    if landmarks:
        # Выводим координаты каждой ключевой точки в консоль
        for idx, lm in enumerate(landmarks.landmark):
            x, y, z = lm.x, lm.y, lm.z
            print(f"Точка {idx}: X={x:.4f}, Y={y:.4f}, Z={z:.4f}")

        # Отрисовка ключевых точек на изображении (для визуализации)
        h, w, _ = frame.shape
        for lm in landmarks.landmark:
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (cx, cy), radius=5, color=(0, 155, 255), thickness=-1)

    # Показываем обработанный кадр
    cv2.imshow('MediaPipe Pose', frame)

    # Выход по нажатию клавиши ESC
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
