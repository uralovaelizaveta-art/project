# import cv2
# import mediapipe as mp

# # 1. Импортируем нужные модули из tasks
# from mediapipe.tasks.python.vision import vision_image
# from mediapipe.framework.formats import image_frame

# # Инициализация VideoCapture
# cap = cv2.VideoCapture(0)

# if not cap.isOpened():
#     print("Ошибка: Не удалось открыть камеру.")
# else:
#     while True:
#         success, frame_bgr = cap.read()
#         if not success:
#             continue

#         # Отражаем кадр для естественного вида
#         frame_bgr = cv2.flip(frame_bpr, 1) 

#         # 2. Создаем объект ImageFrame
#         # .BGR - это формат OpenCV. Обратите внимание, здесь используется BGR, а не RGB.
#         img_frame = image_frame.ImageFrame(
#             data=frame_bgr,
#             format=image_frame.Format.BGR
#         )

#         # 3. Создаем объект VisionImage с поддержкой zero_copy
#         # Параметр zero_copy=True передает данные без дублирования.
#         image = vision_image.VisionImage.from_imageframe(img_frame, zero_copy=True)
        
#         # --- Здесь можно передавать 'image' в модель ---
#         # results = hand_detector.detect(image)

#         cv2.imshow('MediaPipe Tasks', frame_bgr)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     cap.release()
#     cv2.destroyAllWindows()
    
# import cv2

# # 0 - это индекс камеры. Если у вас несколько камер, попробуйте 1, 2 и т.д.
# cap = cv2.VideoCapture(0)

# # Проверяем, удалось ли открыть камеру
# if not cap.isOpened():
#     print("Ошибка: Камера не найдена.")
#     exit()

# while True:
#     # ret - булево значение (успех/неудача)
#     # frame - сам кадр в виде numpy-массива (формат BGR)
#     ret, frame = cap.read()

#     if not ret:
#         print("Ошибка: Не удалось считать кадр.")
#         break

#     # Здесь будет происходить обработка кадра

#     # Отображаем кадр в окне
#     cv2.imshow('Прямой эфир', frame)

#     # Выход из цикла по нажатию клавиши 'q'
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# # Освобождаем ресурсы
# cap.release()
# cv2.destroyAllWindows()

import cv2

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Получаем высоту и ширину кадра
    height, width = frame.shape[:2]

    # Определяем размер и координаты для нашего "квадрата" в центре
    # min(height, width) гарантирует, что квадрат впишется в кадр
    side = min(height, width) // 2
    x = width // 2 - side // 2
    y = height // 2 - side // 2

    # Вырезаем область интереса (ROI)
    roi = frame[y:y+side, x:x+side]

    # Для наглядности обведем эту область на исходном кадре
    cv2.rectangle(frame, (x, y), (x+side, y+side), (0, 255, 0), 2) 

    cv2.imshow('Прямой эфир с ROI', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# import cv2
# import mediapipe as mp

# # --- ИМПОРТЫ ДЛЯ MEDIAPIPE TASKS ---
# from mediapipe.tasks.python.vision.vision import VisionImage
# from mediapipe.framework.formats import image_frame

# # Инициализация камеры
# cap = cv2.VideoCapture(0)
# if not cap.isOpened():
#     print("Не удалось открыть камеру.")
#     exit()

# print("Нажмите 'q' для выхода.")

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         print("Не удалось получить кадр.")
#         break

#     height, width = frame.shape[:2]
    
#     # --- НАРЕЗКА КАДРА (ЭТАП 2) ---
#     # Вырезаем нижнюю половину кадра для примера
#     roi = frame[height//2:height, 0:width]

#     # --- ПОДГОТОВКА ДЛЯ MEDIAPIPE (ЭТАП 3) ---
#     # 1. Конвертируем ROI из BGR в RGB
#     image_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)

#     # 2. Создаем ImageFrame из RGB-данных
#     img_frame = image_frame.ImageFrame(data=image_rgb, format=image_frame.Format.RGB)

#     # 3. Создаем объект VisionImage с zero_copy для эффективности
#     mp_image = VisionImage.from_imageframe(img_frame, zero_copy=True)
    
#     # --- ПРИМЕР ИСПОЛЬЗОВАНИЯ ---
#     # На этом этапе 'mp_image' готов к передаче в модель.
#     # Например: results = my_model.detect(mp_image)
    
#     # Для наглядности покажем исходный кадр и вырезанный ROI
#     cv2.imshow('Исходный кадр', frame)
#     cv2.imshow('Область для MediaPipe (ROI)', roi)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()