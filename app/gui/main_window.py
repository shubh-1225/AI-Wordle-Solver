"""Main CustomTkinter window. Talks to GameSession / WordleSolver only."""

from __future__ import annotations

import queue
import random
import threading

import customtkinter as ctk

from app.gui.feedback_selector import FeedbackSelector
from app.gui.keyboard import OnScreenKeyboard
from app.gui.simulation_panel import SimulationModePanel, SolverModePanel
from app.gui.solver_panel import SolverPanel
from app.gui.statistics_panel import StatisticsPanel
from app.gui.styles import (
    ACCENT,
    ACCENT_HOVER,
    BUTTON_BG,
    BUTTON_HOVER,
    ERROR,
    INFO,
    SUCCESS,
    WINDOW_BG,
)
from app.gui.wordle_board import WordleBoard
from app.session import GameSession, SessionError
from app.solver.constraints import ConstraintError
from app.solver.simulator import WordleSimulator, simulate
from app.solver.solver import WordleSolver
from app.utils.word_utils import load_word_data

ctk.deactivate_automatic_dpi_awareness()


class MainWindow(ctk.CTk):
    def __init__(self, session: GameSession) -> None:
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
        super().__init__()
        self.session = session
        self._rec_generation = 0
        self._busy = False
        self._ui_queue: queue.Queue = queue.Queue()
        self._solver_sim = WordleSimulator(
            session.solver.answers,
            session.solver.allowed_guesses,
            cache=session.solver.pattern_cache if session.solver.pattern_cache is not None else False,
        )

        self.title("AI Wordle Solver")
        self.geometry("1280x720")
        self.minsize(1080, 700)
        self.configure(fg_color=WINDOW_BG)

        self._build()
        self.bind("<Key>", self._on_physical_key)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.after(50, self._pump_ui)
        self.refresh()
        self.queue_recommendation()

    def _build(self) -> None:
        toolbar = ctk.CTkFrame(self, fg_color="transparent", height=40)
        toolbar.pack(fill="x", padx=16, pady=(10, 0))
        ctk.CTkLabel(
            toolbar,
            text="AI WORDLE SOLVER",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
        ).pack(side="left")
        for text, command, accent in (
            ("New game", self.new_game, True),
            ("Reset row", self.reset_row, False),
            ("Solver", lambda: self.modes.set("Solver"), False),
            ("Simulation", lambda: self.modes.set("Simulation"), False),
        ):
            ctk.CTkButton(
                toolbar,
                text=text,
                width=104,
                height=32,
                corner_radius=8,
                command=command,
                fg_color=ACCENT if accent else BUTTON_BG,
                hover_color=ACCENT_HOVER if accent else BUTTON_HOVER,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            ).pack(side="right", padx=3)

        self.status = ctk.CTkLabel(
            self,
            text="Type a 5-letter guess, then Enter.",
            text_color=INFO,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            anchor="w",
        )
        self.status.pack(fill="x", padx=16, pady=(2, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(6, 12))
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body, fg_color="transparent")
        left.grid(row=0, column=0, sticky="n", padx=(0, 14))
        self.board = WordleBoard(left, on_tile_click=self.on_tile_click)
        self.board.pack(pady=(0, 8))
        self.feedback_bar = FeedbackSelector(left, on_submit=self.submit_feedback)
        self.feedback_bar.pack(fill="x", pady=(0, 8))
        self.keyboard = OnScreenKeyboard(
            left,
            on_letter=self.type_letter,
            on_enter=self.on_enter,
            on_backspace=self.backspace,
        )
        self.keyboard.pack()

        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        self.modes = ctk.CTkTabview(right, fg_color=WINDOW_BG, segmented_button_selected_color=ACCENT)
        self.modes.pack(fill="both", expand=True)
        assist = self.modes.add("Assist")
        solver_tab = self.modes.add("Solver")
        sim_tab = self.modes.add("Simulation")

        assist_body = ctk.CTkFrame(assist, fg_color="transparent")
        assist_body.pack(fill="both", expand=True)
        assist_body.grid_columnconfigure(0, weight=1)
        assist_body.grid_rowconfigure(0, weight=0)
        assist_body.grid_rowconfigure(1, weight=0)
        assist_body.grid_rowconfigure(2, weight=1)

        self.solver_panel = SolverPanel(assist_body)
        self.solver_panel.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.stats_panel = StatisticsPanel(assist_body)
        self.stats_panel.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        candidates = self.solver_panel.attach_candidates(assist_body)
        candidates.grid(row=2, column=0, sticky="nsew")

        self.solver_mode = SolverModePanel(solver_tab, on_run=self.start_solver_mode)
        self.solver_mode.pack(fill="x", pady=8)
        self.sim_mode = SimulationModePanel(sim_tab, on_run=self.start_simulation)
        self.sim_mode.pack(fill="x", pady=8)


    def _dispatch(self, callback) -> None:
        self._ui_queue.put(callback)

    def _pump_ui(self) -> None:
        self._drain_ui_queue()
        if self.winfo_exists():
            self.after(50, self._pump_ui)

    def _drain_ui_queue(self) -> None:
        while True:
            try:
                callback = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            callback()

    def _entry_focused(self) -> bool:
        focus = self.focus_get()
        return isinstance(focus, ctk.CTkEntry)

    def _on_physical_key(self, event: object) -> None:
        if self._entry_focused() or self._busy:
            return
        keysym = getattr(event, "keysym", "")
        char = getattr(event, "char", "")
        if keysym in {"Return", "KP_Enter"}:
            self.on_enter()
        elif keysym in {"BackSpace"}:
            self.backspace()
        elif char and char.isalpha():
            self.type_letter(char)

    def type_letter(self, letter: str) -> None:
        if self._busy:
            return
        self.session.type_letter(letter)
        self.refresh()

    def backspace(self) -> None:
        if self._busy:
            return
        self.session.backspace()
        self.refresh()

    def on_enter(self) -> None:
        if self._busy:
            return
        if self.session.state.awaiting_feedback:
            self.submit_feedback()
            return
        error = self.session.submit_guess()
        self._show_error(error)
        self.refresh()

    def on_tile_click(self, row: int, col: int) -> None:
        if self._busy:
            return
        self.session.cycle_tile(row, col)
        self.refresh()

    def submit_feedback(self) -> None:
        if self._busy:
            return
        error = self.session.submit_feedback()
        self._show_error(error)
        self.refresh()
        if error is None and not self.session.state.failed:
            self.queue_recommendation()

    def new_game(self) -> None:
        self._rec_generation += 1
        self.session.new_game()
        self.refresh()
        self.queue_recommendation()

    def reset_row(self) -> None:
        if self._busy:
            return
        self.session.reset_current_row()
        self.refresh()

    def refresh(self) -> None:
        self._drain_ui_queue()
        self.board.render(self.session.state)
        self.keyboard.render(self.session.state.keyboard)
        remaining = len(self.session.candidates())
        self.stats_panel.render_game(self.session.state, remaining)
        caption = f"Possible answers remaining: {remaining}"
        self.solver_panel.candidate_count.configure(text=caption)
        if hasattr(self.solver_panel, "remaining_value"):
            self.solver_panel.remaining_value.configure(text=str(remaining))
        message = self.session.state.status_message
        if message:
            self._set_status(message)
        elif self.session.state.awaiting_feedback:
            self._set_status("Click tiles to cycle gray → yellow → green, then submit feedback.")
            self.feedback_bar.set_hint("Click tiles: gray → yellow → green")
        else:
            self._set_status("Type a 5-letter guess, then Enter.")
            self.feedback_bar.set_hint("Enter a 5-letter guess, then click tiles: gray → yellow → green")

    def _set_status(self, message: str) -> None:
        lowered = message.lower()
        if any(token in lowered for token in ("not in", "not enough", "already", "no possible", "exhausted", "failed", "check the feedback")):
            color = ERROR
        elif "solved" in lowered:
            color = SUCCESS
        else:
            color = INFO
        self.status.configure(text=message, text_color=color)

    def _show_error(self, error: SessionError | None) -> None:
        if error is None:
            return
        self.session.state.status_message = error.message
        self._set_status(error.message)

    def queue_recommendation(self) -> None:
        self._rec_generation += 1
        generation = self._rec_generation
        remaining = len(self.session.candidates())
        self.solver_panel.set_loading(remaining)
        thread = threading.Thread(
            target=self._compute_recommendation,
            args=(generation,),
            daemon=True,
        )
        thread.start()

    def _compute_recommendation(self, generation: int) -> None:
        try:
            recommendation = self.session.recommendation()
            candidates = self.session.candidates()
        except ConstraintError:
            recommendation = None
            candidates = ()
        self._dispatch(lambda: self._apply_recommendation(generation, recommendation, candidates))

    def _apply_recommendation(self, generation: int, recommendation: object, candidates: tuple[str, ...]) -> None:
        if not self.winfo_exists() or generation != self._rec_generation:
            return
        self.solver_panel.render_recommendation(recommendation, candidates)  # type: ignore[arg-type]
        self.refresh()

    def start_solver_mode(self, strategy: str, opener: str | None, answer: str) -> None:
        if self._busy:
            return
        hidden = answer if answer else random.choice(self.session.solver.answers)
        self._busy = True
        self.solver_mode.set_status("Solving…")
        thread = threading.Thread(
            target=self._run_solver_mode,
            args=(strategy, opener, hidden),
            daemon=True,
        )
        thread.start()

    def _run_solver_mode(self, strategy: str, opener: str | None, hidden: str) -> None:
        try:
            result = simulate(
                hidden,
                strategy,
                starting_word=opener,
                solver=self._solver_sim.solver,
            )
            error = None
        except (ConstraintError, ValueError) as exc:
            result = None
            error = str(exc)
        self._dispatch(lambda: self._play_solver_result(result, error))

    def _play_solver_result(self, result: object, error: str | None) -> None:
        if not self.winfo_exists():
            return
        self._busy = False
        if error or result is None:
            self.solver_mode.set_status(error or "Solver failed.")
            return
        self.session.new_game()
        self._rec_generation += 1
        self._animate_turns(result.turns, 0, result)  # type: ignore[attr-defined]

    def _animate_turns(self, turns: tuple, index: int, result: object) -> None:
        if not self.winfo_exists():
            return
        if index >= len(turns):
            self.stats_panel.render_simulation(result)  # type: ignore[arg-type]
            self.solver_mode.set_status(
                f"Done. Answer {result.answer.upper()} in {result.guesses} guesses."  # type: ignore[attr-defined]
            )
            self.queue_recommendation()
            self.refresh()
            return
        turn = turns[index]
        self.session.play_recorded_turn(turn.guess, turn.feedback, turn.entropy)
        self.refresh()
        self.after(450, lambda: self._animate_turns(turns, index + 1, result))

    def start_simulation(self, strategy: str, opener: str, games: int) -> None:
        if self._busy:
            return
        total = min(games, len(self.session.solver.answers))
        self._busy = True
        self.sim_mode.set_progress(0, total)
        thread = threading.Thread(
            target=self._run_simulation,
            args=(strategy, opener, total),
            daemon=True,
        )
        thread.start()

    def _run_simulation(self, strategy: str, opener: str, total: int) -> None:
        answers = self.session.solver.answers[:total]
        try:
            summary = self._solver_sim.benchmark(
                answers,
                strategy=strategy,
                starting_word=opener,
                progress=lambda done, all_games, _result: self._dispatch(
                    lambda d=done, t=all_games: self.sim_mode.set_progress(d, t)
                ),
            )
            error = None
        except (ConstraintError, ValueError) as exc:
            summary = None
            error = str(exc)
        self._dispatch(lambda: self._finish_simulation(summary, error))

    def _finish_simulation(self, summary: object, error: str | None) -> None:
        if not self.winfo_exists():
            return
        self._busy = False
        if error or summary is None:
            self.sim_mode.status.configure(text=error or "Simulation failed.")
            return
        self.stats_panel.render_benchmark(summary)  # type: ignore[arg-type]
        self.modes.set("Assist")
        self.sim_mode.status.configure(
            text=f"Finished {summary.games} games. Win rate {summary.win_rate:.1%}."  # type: ignore[attr-defined]
        )


def run_app() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)
    data = load_word_data()
    solver = WordleSolver(data.answers, data.allowed_guesses, cache=True)
    session = GameSession(solver)
    window = MainWindow(session)
    window.mainloop()
