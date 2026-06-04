import cv2
import mediapipe as mp
import numpy as np

# --- ИМПОРТЫ MEDIAPIPE TASKS (из вашего второго фрагмента) ---
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions
from mediapipe.tasks import python as mp_tasks 
from mediapipe.tasks.python import vision as mp_vision

# --- ИНИЦИАЛИЗАЦИЯ DETECTOR (из вашего второго фрагмента) ---
# Этот блок выполняется один раз при запуске программы
base_options = BaseOptions(model_asset_path='pose_landmarker_full.task')
options = PoseLandmarkerOptions(
    base_options=base_options,
    output_segmentation_masks=True)
detector = PoseLandmarker.create_from_options(options)

# --- ИНИЦИАЛИЗАЦИЯ ОТКРЫТОГО ОКНА (OpenCV) ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Ошибка: Не удалось открыть камеру.")
    exit()

print("Нажмите 'q' для выхода из программы.")

while True:
    # --- ЗАХВАТ КАДРОВ (из вашего первого фрагмента) ---
    ret, frame = cap.read()
    if not ret:
        print("Не удалось получить кадр.")
        break

    # Создаем копию кадра для вывода, чтобы не рисовать поверх оригинала
    output_frame = frame.copy()
    
    # --- ПОДГОТОВКА ДЛЯ MEDIAPIPE (Конвертация) ---
    # 1. Переворачиваем кадр для естественного вида
    frame_rgb = cv2.flip(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), 1)
    
    # 2. Создаем объект ImageFrame (обертка для данных)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # 3. Создаем объект VisionImage для передачи в детектор
    
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    # --- ОБНАРУЖЕНИЕ ПОЗЫ (из вашего второго фрагмента) ---
    # Этот блок выполняется для каждого кадра
    detection_result = detector.detect(mp_image)

    # --- ВИЗУАЛИЗАЦИЯ РЕЗУЛЬТАТА ---
    if detection_result.pose_landmarks:
        # Рисуем ключевые точки (кружки)
        for landmark in detection_result:
            x = int(landmark.x * output_frame.shape[1])
            y = int(landmark.y * output_frame.shape[0])
            cv2.circle(output_frame, (x, y), radius=5, color=(0, 255, 0), thickness=-1)

    if detection_result.segmentation_mask is not None:
        # Преобразуем маску в бинарное изображение и находим контуры тела
        mask_bool = detection_result.segmentation_mask.numpy_view()
        
        # Масштабируем маску до размера исходного кадра
        mask_scaled = cv2.resize(mask_bool.astype(np.uint8), (output_frame.shape[1], output_frame.shape[0]))
        
        # Находим внешние контуры на маске
        contours, _ = cv2.findContours(mask_scaled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Выбираем самый большой контур (предположительно, тело человека)
            largest_contour = max(contours, key=cv2.contourArea)
            # Рисуем контур на кадре
            cv2.drawContours(output_frame, [largest_contour], -1, (255, 0, 0), 2)

    # Отображаем итоговый кадр с нарисованными точками и контурами
    cv2.imshow('Определение позы в реальном времени', output_frame)

    # Выход из цикла по нажатию 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- ЗАВЕРШЕНИЕ РАБОТЫ ---
detector.close()  # Закрываем детектор для освобождения ресурсов
cap.release()     # Освобождаем камеру
cv2.destroyAllWindows()
