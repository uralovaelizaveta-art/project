"""
ПРАВИЛА КЛАССИФИКАЦИИ ДВИЖЕНИЙ
==============================
Заполняйте только этот файл.

ДВА ТИПА ПРАВИЛ (можно комбинировать в одном движении):
  "angles"     — углы суставов в градусах
  "distances"  — расстояния между точками ног (для позиций)

Доступные имена углов (вершина сустава):
  left_elbow    — левый локоть   (плечо — локоть — запястье)
  right_elbow   — правый локоть
  left_knee     — левое колено   (бедро — колено — лодыжка)
  right_knee    — правое колено
  left_shoulder — левое плечо    (локоть — плечо — бедро)
  right_shoulder— правое плечо
  left_hip      — левое бедро
  right_hip     — правое бедро
  left_ankle    — левая лодыжка  (колено — лодыжка — носок)
  right_ankle   — правая лодыжка

Формат угла: (минимум, максимум) в градусах.
Пример: "left_knee": (100, 150)

Доступные расстояния (для позиций ног):
  ankles_norm          — лодыжки (норм. к ширине бёдер)
  heels_norm           — пятки
  toes_norm            — носки
  ankle_x_gap_norm     — расстояние по горизонтали между лодыжками
  ankle_depth_norm     — насколько одна лодыжка впереди другой (IV поз.)
  heel_depth_norm      — глубина между пятками
  left_heel_right_toe_norm  — левая пятка — правый носок (V поз.)
  right_heel_left_toe_norm  — правая пятка — левый носок

  *_norm — доля от ширины бёдер (удобнее калибровать).
  Смотрите значения в консоли при запуске программы.

Формат расстояния: (минимум, максимум) — те же единицы, что в консоли.

ПОЗИЦИИ НОГ — используйте "distances" + "visibility" + пол (авто).

Видимость точек ("visibility"):
  "hidden"  — точка почти не видна (visibility 0..0.45)
  "visible" — точка хорошо видна (0.45..1.0)
  "high"    — очень хорошо видна (0.6..1.0)
  или свой диапазон: (0.0, 0.4)

Имена точек: left_heel, right_heel, left_ankle, right_ankle,
             left_toe, right_toe

III и V позиция — одна пятка скрыта за стопой (variants + visibility).

Ноги на полу (автоматически для всех pos*):
  POSITION_FLOOR_REQUIREMENTS — носки не подняты, лодыжки на одном уровне.
  Свои пороги: "foot_on_floor": {"ankle_y_diff_norm": (0.0, 0.12)}

Варианты "variants" — левая/правая нога или скрытая пятка.
"""

# Пресеты видимости
VISIBILITY_PRESETS = {
    "hidden":  (0.0, 0.45),
    "low":     (0.0, 0.55),
    "visible": (0.45, 1.0),
    "high":    (0.6, 1.0),
}

# Общие требования «ноги на полу» для всех позиций (id начинается с pos)
POSITION_FLOOR_REQUIREMENTS = {
    "ankle_y_diff_norm":          (0.0, 0.15),  # лодыжки на одном уровне
    "toe_y_diff_norm":            (0.0, 0.20),  # носки на одном уровне
    "left_toe_above_ankle_norm":  (0.0, 0.10),  # носок не поднят
    "right_toe_above_ankle_norm": (0.0, 0.10),
    "max_toe_lift_norm":          (0.0, 0.10),
}

# Настройки классификатора
CLASSIFIER_SETTINGS = {
  # Название, если ни одно движение не подошло
  "unknown_name": "Не определено",
  # Минимальная уверенность (0..1). Ниже — считаем «Не определено»
  "min_confidence": 0.5,
}

# Список движений. Дополняйте и редактируйте по мере калибровки.
MOVEMENT_RULES = [
  # ------------------------------------------------------------------
  # ПРИМЕР (можно удалить после заполнения своих значений):
  # ------------------------------------------------------------------
  {
    "id": "basic2",
    "name": "Plie",
    "angles": {
      "left_knee":  (100, 165),   # ЗАПОЛНИТЕ под свои измерения
      "right_knee": (100, 165),
    },
    # Необязательно: свой порог для этого движения (0..1)
    # "min_score": 0.6,
  },
  {
    "id": "basic1",
    "name": "Battement tendu",
    "variants": [
        {
            "label": "левая нога",
            "angles": {
                "left_hip":  (150, 165), 
                "right_hip": (170, 180),  
                "left_knee": (170, 180),
                "right_knee": (170, 180)
            },
        },
        {
            "label": "правая нога",
            "angles": {
                "right_hip": (150, 165), 
                "left_hip":  (170, 180), 
                "left_knee": (170, 180),
                "right_knee": (170, 180)
            },
        },
    ],
  },
  {
    "id": "basic3",
    "name": "Battement tendu jete",
    "variants": [
        {
            "label": "левая нога",
            "angles": {
                "left_hip":  (125, 150), 
                "right_hip": (170, 180), 
                "left_knee": (170, 180),
                "right_knee": (170, 180) 
            },
        },
        {
            "label": "правая нога",
            "angles": {
                "right_hip": (125, 150), 
                "left_hip":  (170, 180),
                "left_knee": (170, 180),
                "right_knee": (170, 180)  
            },
        },
    ],
  },
  {
    "id": "basic4",
    "name": "Sur le coup de pied",
    "variants": [
        {
            "label": "левая нога у щиколотки",
            "angles": {
                "left_knee":  (100, 135),    # рабочая — согнута
                "right_knee": (165, 180),   # опорная — прямая
                "left_hip": (150, 165),
                "right_hip": (170, 180)
            },
        },
        {
            "label": "правая нога у щиколотки",
            "angles": {
                "right_knee": (100, 135),   # рабочая — согнута
                "left_knee":  (165, 180),
                "left_hip": (170, 180),
                "right_hip": (150, 165)
            },
        },
    ],
  },
  {
    "id": "basic5",
    "name": "Passe",
        "variants": [
        {
            "label": "левая нога",
            "angles": {
                "left_knee":  (40, 80), 
                "right_knee": (170, 180),  
                "left_hip": (110, 150),
                "right_hip": (170, 180)
            },
        },
        {
            "label": "правая нога",
            "angles": {
                "right_knee": (40, 80), 
                "left_knee":  (170, 180),  
                "left_hip": (170, 180),
                "right_hip": (110, 165)
            },
        },
    ],
  },
  {
    "id": "basic6",
    "name": "Grand battement tendu jete",
    "variants":[
        {
            "label": "левая нога",
            "angles": {
                "left_hip":  (60, 120), 
                "right_hip": (170, 180),  
            },
        },
        {
            "label": "правая нога",
            "angles": {
                "right_hip": (60, 120), 
                "left_hip":  (170, 180),  
            },
        },
    ]
  },
  # ------------------------------------------------------------------
  # КАК ДОБАВИТЬ НОВОЕ ДВИЖЕНИЕ — скопируйте блок ниже в конец списка:
  # ------------------------------------------------------------------
  # {
  #   "id": "my_movement",
  #   "name": "Название движения",
  #   "angles": {
  #     "left_knee":  (мин, макс),
  #     "right_knee": (мин, макс),
  #     # добавьте любые углы из списка в начале файла
  #   },
  # },


  # ------------------------------------------------------------------
  # ПОЗИЦИИ — по расстоянию между точками ног (ЗАПОЛНИТЕ под себя)
  # ------------------------------------------------------------------
  {
    "id": "pos1",
    "name": "I position",
    "visibility": {
      "left_heel":  "visible",
      "right_heel": "visible",
    },
    "distances": {
      "ankles_norm": (0.15, 0.55),
      "heels_norm":  (0.10, 0.45),
    },
  },
  {
    "id": "pos2",
    "name": "II position",
    "visibility": {
      "left_heel":  "visible",
      "right_heel": "visible",
    },
    "distances": {
      "ankles_norm":      (0.90, 2.50),
      "ankle_x_gap_norm": (0.90, 2.50),
      "toes_norm":        (0.90, 2.80),
    },
  },
  {
    "id": "pos3",
    "name": "III position",
    "variants": [
      {
        "label": "пятка левой ноги скрыта (приставлена)",
        "visibility": {
          "left_heel":  "hidden",
          "right_heel": "visible",
        },
        "distances": {
          "ankles_norm": (0.05, 0.45),
          "heels_norm":  (0.05, 0.50),
        },
      },
      {
        "label": "пятка правой ноги скрыта (приставлена)",
        "visibility": {
          "right_heel": "hidden",
          "left_heel":  "visible",
        },
        "distances": {
          "ankles_norm": (0.05, 0.45),
          "heels_norm":  (0.05, 0.50),
        },
      },
    ],
  },
  {
    "id": "pos4",
    "name": "IV position",
    "visibility": {
      "left_heel":  "visible",
      "right_heel": "visible",
    },
    "distances": {
      "ankles_norm":      (0.30, 0.90),
      "ankle_depth_norm": (0.15, 0.80),
    },
  },
  {
    "id": "pos5",
    "name": "V position",
    "variants": [
      {
        "label": "левая пятка за правой стопой",
        "visibility": {
          "left_heel":  "hidden",
          "right_heel": "visible",
        },
        "distances": {
          "ankles_norm": (0.02, 0.35),
          "heels_norm":  (0.02, 0.35),
          "left_heel_right_toe_norm": (0.05, 0.55),
        },
      },
      {
        "label": "правая пятка за левой стопой",
        "visibility": {
          "right_heel": "hidden",
          "left_heel":  "visible",
        },
        "distances": {
          "ankles_norm": (0.02, 0.35),
          "heels_norm":  (0.02, 0.35),
          "right_heel_left_toe_norm": (0.05, 0.55),
        },
      },
    ],
  },
]

# ------------------------------------------------------------------
# ПОСЛЕДОВАТЕЛЬНОСТИ (составные движения по времени)
# ------------------------------------------------------------------
# steps — id движений по порядку (из MOVEMENT_RULES).
# Соте: плие → II позиция (в прыжке) → плие
#
# Как добавить новую последовательность:
# {
#   "id": "jump2",
#   "name": "Па эшапе",
#   "steps": ["basic2", "pos5", "pos2", "pos5", "basic2"],
#   "max_step_gap_sec": 2.5,   # макс. пауза между шагами (сек)
#   "max_total_sec": 10.0,     # макс. длина всей цепочки (сек)
# },

SEQUENCE_RULES = [
    {
        "id": "jump1",
        "name": "saute",
        "steps": ["basic2", "pos2", "basic2"],
        "max_step_gap_sec": 1.0,
        "max_total_sec": 4.0,
    },
]

# Настройки записи истории движений
TIMELINE_SETTINGS = {
    "min_hold_sec": 0.15,
    "cooldown_sec": 0.8,
    "max_history": 50,
    "session_log_path": "data/movement_session.json",
}