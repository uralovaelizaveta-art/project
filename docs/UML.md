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
flowchart LR
    User([Пользователь])

    subgraph UI[Интерфейс сайта]
        Pages[HTML-страницы]
        Search[Поиск и подсказки]
        MovementPage[Страница движения]
        RealtimePage[Окно камеры]
        Skeleton[Скелет поверх видео]
        MovementList[Список распознанных движений]
    end

    subgraph ClientLogic[JavaScript в браузере]
        AppJS[app.js]
        ApiJS[api.js]
        MovementJS[movement.js]
        AlphabetJS[alphabet.js]
        RealtimeJS[realtime.js]
        BrowserStorage[(localStorage)]
        CameraAPI[MediaDevices API]
        CanvasAPI[Canvas]
    end

    subgraph DataLayer[Данные справочника]
        MovementsJSON[(data/movements.json)]
    end

    subgraph ServerLayer[Сервер распознавания]
        Uvicorn[Uvicorn]
        FastAPI[FastAPI server.py]
        WebSocket[WebSocket /ws]
        Session[RealtimeSession]
    end

    subgraph RecognitionLayer[Модуль компьютерного зрения]
        PoseModel[PoseModel]
        MediaPipe[MediaPipe Pose Landmarker]
        Geometry[PoseGeometry]
        Classifier[MovementClassifier]
        Timeline[MovementTimeline]
        Sequence[SequenceDetector]
        Rules[movement_rules.py]
        ModelFile[(pose_landmarker_lite.task)]
    end

    User --> Pages
    Pages --> Search
    Pages --> MovementPage
    Pages --> RealtimePage

    Search --> AppJS
    MovementPage --> MovementJS
    RealtimePage --> RealtimeJS

    AppJS --> ApiJS
    MovementJS --> ApiJS
    AlphabetJS --> ApiJS
    ApiJS --> MovementsJSON

    AppJS <--> BrowserStorage
    RealtimeJS --> CameraAPI
    CameraAPI --> RealtimeJS
    RealtimeJS --> CanvasAPI
    CanvasAPI --> Skeleton
    RealtimeJS --> MovementList

    RealtimeJS <-->|кадры JPEG и JSON-результаты| WebSocket
    Uvicorn --> FastAPI
    FastAPI --> WebSocket
    WebSocket --> Session

    Session --> PoseModel
    PoseModel --> MediaPipe
    MediaPipe --> ModelFile
    Session --> Geometry
    Session --> Classifier
    Session --> Timeline
    Session --> Sequence
    Classifier --> Rules
    Sequence --> Rules
    Timeline --> MovementList
```

Архитектура разделена на клиентскую и серверную части. В браузере работает интерфейс сайта, поиск по справочнику и окно камеры. Данные о движениях загружаются из `data/movements.json`. Для режима реального времени JavaScript получает изображение с камеры и отправляет кадры на FastAPI-сервер через WebSocket. Сервер передает кадры в модуль распознавания, где MediaPipe определяет ключевые точки тела, геометрический модуль рассчитывает признаки позы, а классификатор сравнивает их с правилами движений. После этого результат возвращается в браузер и отображается рядом с камерой.

## UML-диаграмма классов распознавания

```mermaid
classDiagram
    class Point2D {
        public float x
        public float y
        public float visibility
    }

    class PoseModel {
        private PoseLandmarker landmarker
        public detect(frame_bgr, timestamp_ms)
        public detect_rgb(frame_rgb, timestamp_ms)
        public close()
    }

    class PoseGeometry {
        public dict KEYPOINTS
        public list CONNECTIONS
        public dict ANGLES
        public extract_points(landmarks, width, height) dict
        public compute_angles(points) dict
        public compute_distances(points) dict
        public compute_foot_state(points) dict
        public draw_skeleton(frame, points)
    }

    class ClassificationResult {
        public str movement_id
        public str movement_name
        public float confidence
    }

    class MovementClassifier {
        private list rules
        private dict settings
        public classify(angles, distances, foot_state) ClassificationResult
        private _score_movement(angles, distances, foot_state, rule) float
        private _score_block(angles, distances, foot_state, rule, block) float
    }

    class RecordedMovement {
        public str movement_id
        public str movement_name
        public float confidence
        public float time_sec
    }

    class SequenceDetection {
        public str sequence_id
        public str sequence_name
        public float time_sec
        public list steps
    }

    class TimelineSettings {
        public float min_hold_sec
        public float cooldown_sec
        public int max_history
    }

    class MovementTimeline {
        public list events
        public list sequences_detected
        public update(movement_id, movement_name, confidence) bool
        public add_sequence(detection)
        public get_events_for_api() list
        public get_sequences_for_api() list
        public export_json(path)
    }

    class SequenceDetector {
        private list sequence_rules
        public check(timeline) SequenceDetection
        private _match_steps(events, step_ids, max_gap, max_total)
    }

    class RealtimeSession {
        public MovementTimeline timeline
        public SequenceDetector sequence_detector
        public process_frame(frame_rgb) dict
        private _is_ready_for_detection(points, frame_w, frame_h) bool
    }

    class RealTimePoseApp {
        public PoseModel model
        public PoseGeometry geometry
        public MovementClassifier classifier
        public MovementTimeline timeline
        public SequenceDetector sequence_detector
        public run()
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
    participant UI as Интерфейс сайта
    participant Camera as Камера
    participant WS as Сервер FastAPI
    participant Session as Сессия распознавания
    participant Pose as MediaPipe
    participant Geometry as Анализ позы
    participant Classifier as Правила движений
    participant Timeline as История движений

    User->>UI: Нажимает "Включить камеру"
    UI->>Camera: Запрашивает доступ к камере
    Camera-->>UI: Передает видеопоток
    UI->>WS: Открывает постоянное соединение
    WS->>Session: Создает отдельную сессию для пользователя

    loop Пока камера включена
        UI->>UI: Подготавливает кадр для отправки
        UI->>WS: Отправляет изображение с камеры
        WS->>Session: Передает кадр на обработку
        Session->>Pose: Определяет положение тела на кадре
        Pose-->>Session: Возвращает координаты ключевых точек
        Session->>Geometry: Рассчитывает признаки позы
        Geometry-->>Session: Возвращает углы, расстояния и видимость точек
        Session->>Classifier: Сравнивает позу с правилами движений
        Classifier-->>Session: Возвращает название движения и уверенность
        Session->>Timeline: Добавляет устойчивый результат в историю
        Timeline-->>Session: Возвращает обновленный список движений
        Session-->>WS: Формирует ответ с результатом, точками тела и историей
        WS-->>UI: Отправляет результат распознавания
        UI->>UI: Обновляет название движения, список и скелет
    end

    User->>UI: Нажимает "Выключить камеру"
    UI->>Camera: Останавливает видеопоток
    UI->>WS: Закрывает соединение с сервером
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
