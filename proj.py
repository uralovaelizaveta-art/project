# import mediapipe as mp
# from mediapipe.tasks import python
# from mediapipe.tasks.python import vision

# model_path = '/absolute/path/to/pose_landmarker.task'

import numpy as np
from mediapipe.tasks.python.vision import drawing_utils
from mediapipe.tasks.python.vision import drawing_styles
from mediapipe.tasks.python import vision


def draw_landmarks_on_image(rgb_image, detection_result):
  pose_landmarks_list = detection_result.pose_landmarks
  annotated_image = np.copy(rgb_image)

  pose_landmark_style = drawing_styles.get_default_pose_landmarks_style()
  pose_connection_style = drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2)

  for pose_landmarks in pose_landmarks_list:
    drawing_utils.draw_landmarks(
        image=annotated_image,
        landmark_list=pose_landmarks,
        connections=vision.PoseLandmarksConnections.POSE_LANDMARKS,
        landmark_drawing_spec=pose_landmark_style,
        connection_drawing_spec=pose_connection_style)

  return annotated_image
import cv2
from google.colab.patches import cv2_imshow

img = cv2.imread("image.jpg")
cv2_imshow(img)

# STEP 1: Import the necessary modules.
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# STEP 2: Create an PoseLandmarker object.
base_options = python.BaseOptions(model_asset_path='pose_landmarker.task')
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    output_segmentation_masks=True)
detector = vision.PoseLandmarker.create_from_options(options)

# STEP 3: Load the input image.
image = mp.Image.create_from_file("image.jpg")

# STEP 4: Detect pose landmarks from the input image.
detection_result = detector.detect(image)

# STEP 5: Process the detection result. In this case, visualize it.
annotated_image = draw_landmarks_on_image(image.numpy_view(), detection_result)
cv2_imshow(cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
# # Инициализация модулей MediaPipe
# mp_hands = mp.solutions.hands
# hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5)
# mp_draw = mp.solutions.drawing_utils

# # Открытие веб-камеры (0 — индекс камеры по умолчанию)
# cap = cv2.VideoCapture(0)

# while cap.isOpened():
#    success, image = cap.read()
#    if not success:
#        print("Ignoring empty camera frame.")
#        continue

#    # Переворачиваем кадр по горизонтали для естественного отображения и конвертируем в RGB
#    image = cv2.flip(image, 1)
#    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

#    # Обработка кадра моделью MediaPipe
#    results = hands.process(image_rgb)

#    # Отрисовка ключевых точек и связей руки на изображении
#    if results.multi_hand_landmarks:
#        for hand_landmarks in results.multi_hand_landmarks:
#            mp_draw.draw_landmarks(
#                image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
#                mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
#                mp_draw.DrawingSpec(color=(255, 0, 0), thickness=2))

#    cv2.imshow('MediaPipe Hands', image)

#    # Выход из цикла по нажатию клавиши 'q'
#    if cv2.waitKey(5) & 0xFF == ord('q'):
#        break

# hands.close()
# cap.release()
# cv2.destroyAllWindows()