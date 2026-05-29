"""Движок лесенки: состояние игры и обработка ответов."""
from dataclasses import dataclass, field, asdict

from config import QUESTIONS_PER_GAME, PRIZE_LADDER
from game.questions import build_game_questions
from game.ladder import guaranteed_level, prize_for_level

TOTAL_LEVELS = len(PRIZE_LADDER)


@dataclass
class GameState:
    questions: list = field(default_factory=list)  # вопросы на игру (по порядку)
    index: int = 0                                  # текущий вопрос, 0-based
    hidden: list = field(default_factory=list)      # буквы, скрытые 50:50 на текущем вопросе
    lifelines: dict = field(default_factory=lambda: {"fifty": False, "audience": False, "friend": False})
    finished: bool = False
    won: bool = False                               # дошёл ли до конца лесенки

    # --- сериализация для хранилища FSM ---
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        return cls(**data)

    # --- доступ к текущему вопросу ---
    @property
    def current(self) -> dict:
        return self.questions[self.index]

    @property
    def level(self) -> int:
        """Уровень текущего вопроса, 1-based."""
        return self.index + 1

    def available_letters(self) -> list[str]:
        return [l for l in ("A", "B", "C", "D") if l not in self.hidden]


def new_game() -> GameState:
    return GameState(questions=build_game_questions())


@dataclass
class AnswerResult:
    correct: bool
    chosen: str
    correct_letter: str
    finished: bool
    won: bool
    level_reached: int      # сколько вопросов пройдено верно (1-based)
    guaranteed_prize: str   # несгораемый приз при проигрыше
    final_prize: str        # итоговый приз (для finished)


def answer(state: GameState, letter: str) -> AnswerResult:
    """Обработать ответ игрока. Мутирует state (переходит к след. вопросу /
    завершает игру)."""
    q = state.current
    correct_letter = q["correct"]
    is_correct = letter == correct_letter
    level = state.level  # 1-based номер текущего вопроса

    if not is_correct:
        state.finished = True
        guaranteed = guaranteed_level(level - 1)  # последний ПРОЙДЕННЫЙ вопрос
        return AnswerResult(
            correct=False,
            chosen=letter,
            correct_letter=correct_letter,
            finished=True,
            won=False,
            level_reached=level - 1,
            guaranteed_prize=prize_for_level(guaranteed),
            final_prize=prize_for_level(guaranteed),
        )

    # Верный ответ.
    if level >= QUESTIONS_PER_GAME or level >= TOTAL_LEVELS:
        state.finished = True
        state.won = True
        return AnswerResult(
            correct=True,
            chosen=letter,
            correct_letter=correct_letter,
            finished=True,
            won=True,
            level_reached=level,
            guaranteed_prize=prize_for_level(level),
            final_prize=prize_for_level(level),
        )

    # Переходим к следующему вопросу.
    state.index += 1
    state.hidden = []
    return AnswerResult(
        correct=True,
        chosen=letter,
        correct_letter=correct_letter,
        finished=False,
        won=False,
        level_reached=level,
        guaranteed_prize=prize_for_level(guaranteed_level(level)),
        final_prize=prize_for_level(level),
    )
