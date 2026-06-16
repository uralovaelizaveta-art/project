"""
ПРАВИЛА КЛАССИФИКАЦИИ ДВИЖЕНИЙ

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

CLASSIFIER_SETTINGS = {
  "unknown_name": "Не определено",
  "min_confidence": 0.5,
}

MOVEMENT_RULES = [
  {
    "id": "basic2",
    "name": "Plie",
    "angles": {
      "left_knee":  (100, 165),  
      "right_knee": (100, 165),
    },
    "min_score": 0.6,
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
    "min_score": 0.6,
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
    "min_score": 0.6,
  },
  {
    "id": "basic4",
    "name": "Sur le coup de pied",
    "variants": [
        {
            "label": "левая нога у щиколотки",
            "angles": {
                "left_knee":  (100, 135),    
                "right_knee": (165, 180),  
                "left_hip": (130, 165),
                "right_hip": (170, 180)
            },
        },
        {
            "label": "правая нога у щиколотки",
            "angles": {
                "right_knee": (100, 135),   
                "left_knee":  (165, 180),
                "left_hip": (170, 180),
                "right_hip": (130, 165)
            },
        },
    ],
    "min_score": 0.6,
  },
  {
    "id": "basic5",
    "name": "Retire",
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
    "min_score": 0.6,
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
    ],
    "min_score": 0.6,
  },

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
    "angles": {
        "left_knee":  (170, 180),
        "right_knee": (170, 180)
    },
    "min_score": 0.6,
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
    "angles": {
        "left_knee":  (170, 180),
        "right_knee": (170, 180)
    },
    "min_score": 0.6,
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
        "angles": {
        "left_knee":  (170, 180),
        "right_knee": (170, 180)
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
        "angles": {
        "left_knee":  (170, 180),
        "right_knee": (170, 180)
    },
      },
    ],
    "min_score": 0.6,
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
    "angles": {
        "left_knee":  (170, 180), 
        "right_knee": (170, 180)
    },
    "min_score": 0.6,
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
        "angles": {
            "left_knee":  (170, 180), 
            "right_knee": (170, 180)
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
        "angles": {
            "left_knee":  (170, 180), 
            "right_knee": (170, 180)
        },
      },
    ],
    "min_score": 0.6,
  },
]

SEQUENCE_RULES = [
    {
        "id": "jump1",
        "name": "saute",
        "steps": ["basic2", "pos2", "basic2"],
        "max_step_gap_sec": 1.0,
        "max_total_sec": 4.0,
    },
]

TIMELINE_SETTINGS = {
    "min_hold_sec": 0.15,
    "cooldown_sec": 0.8,
    "max_history": 50,
    "session_log_path": "data/movement_session.json",
}