"""
Память движений по времени и распознавание последовательностей.

Использование на сайте: после сессии читайте data/movement_session.json
или вызывайте timeline.export_json() / timeline.get_events_for_api().
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class RecordedMovement:
    movement_id: str
    movement_name: str
    confidence: float
    time_sec: float


@dataclass
class SequenceDetection:
    sequence_id: str
    sequence_name: str
    time_sec: float
    steps: list[RecordedMovement]


@dataclass
class TimelineSettings:
    min_hold_sec: float = 0.15
    cooldown_sec: float = 0.8
    max_history: int = 50


class MovementTimeline:
    """
    Запоминает распознанные движения с меткой времени.
    Одно и то же движение добавляется только после удержания min_hold_sec.
    """

    def __init__(
        self,
        settings: TimelineSettings | None = None,
        session_log_path: str | Path = "data/movement_session.json",
    ):
        self.settings = settings or TimelineSettings()
        self.session_log_path = Path(session_log_path)
        self.session_start = time.time()

        self.events: list[RecordedMovement] = []
        self.sequences_detected: list[SequenceDetection] = []

        self._candidate_id: str | None = None
        self._candidate_name: str = ""
        self._candidate_confidence: float = 0.0
        self._candidate_since: float | None = None

    def _now(self) -> float:
        return time.time() - self.session_start

    def update(self, movement_id: str, movement_name: str, confidence: float) -> bool:
        """
        Вызывать каждый кадр. Возвращает True, если в историю добавлено новое движение.
        """
        now = self._now()
        unknown_ids = {"unknown", ""}

        if movement_id in unknown_ids:
            self._reset_candidate()
            return False

        if movement_id != self._candidate_id:
            self._candidate_id = movement_id
            self._candidate_name = movement_name
            self._candidate_confidence = confidence
            self._candidate_since = now
            return False

        if self._candidate_since is None:
            return False

        if now - self._candidate_since < self.settings.min_hold_sec:
            return False

        if self.events:
            last = self.events[-1]
            if last.movement_id == movement_id and now - last.time_sec < self.settings.cooldown_sec:
                return False

        event = RecordedMovement(
            movement_id=movement_id,
            movement_name=movement_name,
            confidence=confidence,
            time_sec=round(now, 2),
        )
        self.events.append(event)
        if len(self.events) > self.settings.max_history:
            self.events = self.events[-self.settings.max_history :]

        self._reset_candidate()
        return True

    def _reset_candidate(self):
        self._candidate_id = None
        self._candidate_name = ""
        self._candidate_confidence = 0.0
        self._candidate_since = None

    def add_sequence(self, detection: SequenceDetection):
        self.sequences_detected.append(detection)

    def get_recent(self, count: int = 8) -> list[RecordedMovement]:
        return self.events[-count:]

    def get_events_for_api(self) -> list[dict]:
        return [asdict(e) for e in self.events]

    def get_sequences_for_api(self) -> list[dict]:
        return [
            {
                "sequence_id": s.sequence_id,
                "sequence_name": s.sequence_name,
                "time_sec": s.time_sec,
                "steps": [asdict(step) for step in s.steps],
            }
            for s in self.sequences_detected
        ]

    def export_json(self, path: str | Path | None = None) -> Path:
        path = Path(path or self.session_log_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "session_start_unix": self.session_start,
            "duration_sec": round(self._now(), 2),
            "events": self.get_events_for_api(),
            "sequences_detected": self.get_sequences_for_api(),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def format_history_lines(self, count: int = 6) -> list[str]:
        lines = []
        for e in self.get_recent(count):
            lines.append(f"{e.time_sec:5.1f}s  {e.movement_name} ({e.confidence:.0%})")
        for s in self.sequences_detected[-3:]:
            lines.append(f"{s.time_sec:5.1f}s  >> {s.sequence_name}")
        return lines


class SequenceDetector:
    """
    Ищет составные движения (цепочки) в истории.
    Правила задаются в movement_rules.py → SEQUENCE_RULES.
    """

    def __init__(self, sequence_rules: list[dict]):
        self.sequence_rules = sequence_rules
        self._completed_keys: set[str] = set()

    @staticmethod
    def _match_steps(
        events: list[RecordedMovement],
        step_ids: list[str],
        max_step_gap_sec: float,
        max_total_sec: float,
    ) -> list[RecordedMovement] | None:
        if not step_ids:
            return None

        start_idx = 0
        matched: list[RecordedMovement] = []

        for step_id in step_ids:
            found = None
            for i in range(start_idx, len(events)):
                if events[i].movement_id != step_id:
                    continue
                if matched and events[i].time_sec - matched[-1].time_sec > max_step_gap_sec:
                    continue
                found = events[i]
                start_idx = i + 1
                break
            if found is None:
                return None
            matched.append(found)

        if matched[-1].time_sec - matched[0].time_sec > max_total_sec:
            return None
        return matched

    def check(self, timeline: MovementTimeline) -> SequenceDetection | None:
        events = timeline.events
        if not events:
            return None

        for rule in self.sequence_rules:
            seq_id = rule["id"]
            steps = rule["steps"]
            max_gap = rule.get("max_step_gap_sec", 3.0)
            max_total = rule.get("max_total_sec", 10.0)

            matched = self._match_steps(events, steps, max_gap, max_total)
            if matched is None:
                continue

            key = f"{seq_id}:{matched[0].time_sec}:{matched[-1].time_sec}"
            if key in self._completed_keys:
                continue

            self._completed_keys.add(key)
            return SequenceDetection(
                sequence_id=seq_id,
                sequence_name=rule.get("name", seq_id),
                time_sec=matched[-1].time_sec,
                steps=matched,
            )

        return None
