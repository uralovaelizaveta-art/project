# UML-диаграммы проекта

Проект представляет собой веб-справочник движений классического танца с
поиском по названию и распознаванием движений по изображению с камеры.

Документ описывает текущее состояние реализации:

- веб-интерфейс работает в браузере;
- справочник хранится в `data/movements.json`;
- пользовательские данные хранятся в `localStorage`;
- FastAPI-сервер обрабатывает кадры по WebSocket;
- MediaPipe определяет ключевые точки тела;
- правила из `movement_rules.py` классифицируют движения.

Диаграммы записаны в формате Mermaid. Их можно просмотреть в редакторе с
поддержкой Mermaid, на GitHub или вставить в
[Mermaid Live Editor](https://mermaid.live/) для экспорта в PNG или SVG.

## Диаграмма вариантов использования

```mermaid
flowchart LR
    Guest([Посетитель])
    User([Пользователь])
    Camera([Камера устройства])

    subgraph System[Справочник движений классического танца]
        Browse((Просматривать справочник))
        Search((Искать движение по названию))
        Filter((Фильтровать алфавитный указатель))
        View((Открывать страницу движения))
        Feedback((Отправлять обратную связь))
        Realtime((Запускать распознавание в реальном времени))
        Skeleton((Просматривать ключевые точки тела))
        History((Просматривать историю распознанных движений))
        OpenDetected((Открывать распознанное движение))
        Favorite((Добавлять движение в избранное))
        Auth((Регистрироваться и входить))
    end

    Guest --> Browse
    Guest --> Search
    Guest --> Filter
    Guest --> View
    Guest --> Feedback
    Guest --> Realtime
    Guest --> Auth

    User --> Browse
    User --> Search
    User --> View
    User --> Favorite
    User --> Realtime

    Camera --> Realtime
    Realtime --> Skeleton
    Realtime --> History
    History --> OpenDetected
    OpenDetected --> View
```

## Компонентная архитектура

```mermaid
flowchart TB
    subgraph Browser[Браузер пользователя]
        Pages[HTML-страницы]
        AppJS[app.js: поиск и общая логика]
        ApiJS[api.js: доступ к справочнику]
        RealtimeJS[realtime.js: камера, WebSocket, overlay]
        OtherJS[alphabet.js, movement.js, auth.js, ui.js]
        LocalStorage[(localStorage)]
        Camera[MediaDevices API]
        Canvas[Canvas: скелет поверх видео]
    end

    subgraph Backend[Python / FastAPI]
        Server[server.py]
        Session[RealtimeSession]
        Pose[PoseModel / MediaPipe]
        Geometry[PoseGeometry]
        Classifier[MovementClassifier]
        Timeline[MovementTimeline]
        Sequence[SequenceDetector]
        Rules[movement_rules.py]
    end

    subgraph Files[Файлы проекта]
        Movements[(data/movements.json)]
        Model[(pose_landmarker_lite.task)]
        SessionLog[(data/movement_session.json)]
    end

    Pages --> AppJS
    Pages --> OtherJS
    ApiJS --> Movements
    AppJS --> ApiJS
    OtherJS --> ApiJS
    OtherJS <--> LocalStorage

    Camera --> RealtimeJS
    RealtimeJS --> Canvas
    RealtimeJS <-->|WebSocket: JPEG / JSON| Server

    Server --> Session
    Session --> Pose
    Pose --> Model
    Session --> Geometry
    Session --> Classifier
    Session --> Timeline
    Session --> Sequence
    Classifier --> Rules
    Sequence --> Rules
    Timeline -. экспорт .-> SessionLog
```

## UML-диаграмма классов распознавания

```mermaid
classDiagram
    class Point2D {
        +float x
        +float y
        +float visibility
    }

    class PoseModel {
        -PoseLandmarker landmarker
        +detect(frame_bgr, timestamp_ms)
        +detect_rgb(frame_rgb, timestamp_ms)
        +close()
    }

    class PoseGeometry {
        +dict KEYPOINTS
        +list CONNECTIONS
        +dict ANGLES
        +extract_points(landmarks, width, height) dict
        +compute_angles(points) dict
        +compute_distances(points) dict
        +compute_foot_state(points) dict
        +draw_skeleton(frame, points)
    }

    class ClassificationResult {
        +str movement_id
        +str movement_name
        +float confidence
    }

    class MovementClassifier {
        -list rules
        -dict settings
        +classify(angles, distances, foot_state) ClassificationResult
        -_score_movement(angles, distances, foot_state, rule) float
        -_score_block(angles, distances, foot_state, rule, block) float
    }

    class RecordedMovement {
        +str movement_id
        +str movement_name
        +float confidence
        +float time_sec
    }

    class SequenceDetection {
        +str sequence_id
        +str sequence_name
        +float time_sec
        +list steps
    }

    class TimelineSettings {
        +float min_hold_sec
        +float cooldown_sec
        +int max_history
    }

    class MovementTimeline {
        +list events
        +list sequences_detected
        +update(movement_id, movement_name, confidence) bool
        +add_sequence(detection)
        +get_events_for_api() list
        +get_sequences_for_api() list
        +export_json(path)
    }

    class SequenceDetector {
        -list sequence_rules
        +check(timeline) SequenceDetection
        -_match_steps(events, step_ids, max_gap, max_total)
    }

    class RealtimeSession {
        +MovementTimeline timeline
        +SequenceDetector sequence_detector
        +process_frame(frame_rgb) dict
    }

    class RealTimePoseApp {
        +PoseModel model
        +PoseGeometry geometry
        +MovementClassifier classifier
        +MovementTimeline timeline
        +SequenceDetector sequence_detector
        +run()
    }

    PoseGeometry ..> Point2D : создает и использует
    MovementClassifier ..> ClassificationResult : создает
    MovementTimeline "1" o-- "*" RecordedMovement
    MovementTimeline "1" o-- "*" SequenceDetection
    MovementTimeline --> TimelineSettings
    SequenceDetection "1" o-- "*" RecordedMovement
    SequenceDetector --> MovementTimeline
    SequenceDetector ..> SequenceDetection : создает
    RealtimeSession --> PoseModel
    RealtimeSession --> PoseGeometry
    RealtimeSession --> MovementClassifier
    RealtimeSession *-- MovementTimeline
    RealtimeSession *-- SequenceDetector
    RealTimePoseApp *-- PoseModel
    RealTimePoseApp *-- PoseGeometry
    RealTimePoseApp *-- MovementClassifier
    RealTimePoseApp *-- MovementTimeline
    RealTimePoseApp *-- SequenceDetector
```

## Модель данных веб-приложения

Классы ниже являются логическими сущностями. На текущем этапе они хранятся
как JSON-объекты в файле или в `localStorage`.

```mermaid
classDiagram
    class Movement {
        +str id
        +str nameRu
        +str nameFr
        +str category
        +str type
        +str description
        +str imageUrl
        +str videoUrl
        +list tags
    }

    class User {
        +str id
        +str login
        +str password
        +str email
        +str name
        +datetime createdAt
    }

    class Favorite {
        +str userId
        +str movementId
    }

    class RecentMovement {
        +str movementId
        +datetime viewedAt
    }

    class SearchHistoryItem {
        +str query
        +datetime createdAt
    }

    class Feedback {
        +int id
        +str subject
        +str message
        +str contact
        +str userId
        +datetime createdAt
    }

    User "1" --> "*" Favorite
    Favorite "*" --> "1" Movement
    User "0..1" --> "*" SearchHistoryItem
    User "0..1" --> "*" Feedback
    RecentMovement "*" --> "1" Movement
```

## Диаграмма последовательности realtime-распознавания

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant UI as realtime.js
    participant Camera as Камера
    participant WS as FastAPI WebSocket
    participant Session as RealtimeSession
    participant Pose as MediaPipe PoseModel
    participant Geometry as PoseGeometry
    participant Classifier as MovementClassifier
    participant Timeline as MovementTimeline

    User->>UI: Нажимает "Включить камеру"
    UI->>Camera: getUserMedia()
    Camera-->>UI: Видеопоток
    UI->>WS: Открывает /ws
    WS->>Session: Создает сессию

    loop Пока камера включена
        UI->>UI: Масштабирует кадр и кодирует JPEG
        UI->>WS: Отправляет бинарный кадр
        WS->>Session: process_frame(frame)
        Session->>Pose: detect_rgb(frame, timestamp)
        Pose-->>Session: ключевые точки позы
        Session->>Geometry: углы, расстояния, видимость
        Geometry-->>Session: признаки движения
        Session->>Classifier: classify(features)
        Classifier-->>Session: движение и уверенность
        Session->>Timeline: update(movement)
        Timeline-->>Session: история движений
        Session-->>WS: результат + pose_points + история
        WS-->>UI: JSON-ответ
        UI->>UI: Рисует скелет и обновляет список
    end

    User->>UI: Нажимает "Выключить камеру"
    UI->>Camera: Останавливает tracks
    UI->>WS: Закрывает соединение
```

## Диаграмма активности распознавания кадра

```mermaid
flowchart TD
    Start([Получен кадр]) --> Decode[Декодировать JPEG]
    Decode --> Detect[MediaPipe определяет позу]
    Detect --> PoseFound{Поза найдена?}

    PoseFound -- Нет --> Unknown[Вернуть "Не определено"]
    PoseFound -- Да --> Points[Извлечь ключевые точки]
    Points --> Features[Вычислить углы, расстояния и видимость]
    Features --> Compare[Сравнить признаки с правилами]
    Compare --> Score{Оценка выше порога?}
    Score -- Нет --> Unknown
    Score -- Да --> Movement[Сформировать результат движения]
    Movement --> Timeline[Обновить историю]
    Timeline --> Sequence{Найдена последовательность?}
    Sequence -- Да --> SaveSequence[Добавить последовательность]
    Sequence -- Нет --> Response
    SaveSequence --> Response[Сформировать JSON-ответ]
    Unknown --> Response
    Response --> End([Отправить результат браузеру])
```

## Диаграмма развертывания

```mermaid
flowchart LR
    subgraph ClientDevice[Устройство пользователя]
        Browser[Веб-браузер]
        Webcam[Камера]
        Storage[(localStorage)]
    end

    subgraph Host[Компьютер с проектом]
        Static[Статический HTTP-сервер]
        FastAPI[FastAPI / Uvicorn]
        MediaPipe[MediaPipe + TFLite model]
        JSON[(JSON-файлы)]
    end

    Webcam --> Browser
    Browser <--> Storage
    Browser <-->|HTTP: HTML, CSS, JS, JSON| Static
    Browser <-->|WebSocket: JPEG и результаты| FastAPI
    FastAPI --> MediaPipe
    Static --> JSON
    FastAPI -. экспорт истории .-> JSON
```

## Ответственность основных модулей

| Модуль | Ответственность |
|---|---|
| `server.py` | FastAPI-приложение, WebSocket, декодирование кадров |
| `pose_realtime.py` | MediaPipe, геометрия позы, классификация и realtime-сессия |
| `movement_rules.py` | Правила отдельных движений и последовательностей |
| `movement_timeline.py` | История распознанных движений и поиск последовательностей |
| `scripts/realtime.js` | Камера, отправка кадров, вывод результата и скелета |
| `scripts/app.js` | Общая логика интерфейса и поиск по названию |
| `scripts/api.js` | Загрузка справочника и операции с локальными данными |
| `scripts/alphabet.js` | Фильтрация и вывод алфавитного указателя |
| `scripts/movement.js` | Вывод страницы выбранного движения |
| `data/movements.json` | Справочник движений |

## Важное архитектурное замечание

В текущей учебной версии регистрация, избранное, история и обратная связь
хранятся в `localStorage`. Это не серверная база данных: данные доступны
только в конкретном браузере и могут быть удалены пользователем.

Для полноценной многопользовательской версии логично добавить серверную БД,
хеширование паролей и HTTP API для пользователей, избранного и обратной связи.
