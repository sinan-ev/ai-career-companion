"""
Step recorder for the Module 2 pipeline.

WHY THIS EXISTS
---------------
The AI agent decides which steps to run (handle_missing, encoding, etc.)
As each step executes, Memory logs it in real time:
    - What step ran
    - Did it succeed, fail, or get skipped
    - A human-readable note about what happened
    - How long it took

At the end of the pipeline, memory.get_steps() fills the
pipeline_steps list inside Module2Response.

CONNECTION TO MODULE 1
----------------------
Module 1 has no memory system — it runs 9 fixed stages always.
Module 2 is dynamic — the AI picks different steps for different
datasets. Memory makes that dynamic execution traceable and debuggable.

USAGE (in pipeline_module2.py)
------------------------------
    memory = Memory()

    memory.start_step("handle_missing")
    df = clean_missing(df, schema)
    memory.end_step("handle_missing", details="imputed 23 values in Age")

    memory.skip_step("handle_outliers", reason="no outliers detected")

    # At the end:
    steps = memory.get_steps()   # List[PipelineStep] → into Module2Response
    summary = memory.get_summary()  # prints what ran
"""

import time
from typing import List, Optional
from module2.models.module2_response import PipelineStep


class PipelineMemory:
    """
    Real-time step recorder for the Module 2 pipeline.

    Tracks every step the agent runs — success, failure, or skip —
    with timing and detail notes.
    """

    def __init__(self):
        self._steps: List[PipelineStep] = []
        self._timers: dict = {}         # step_name → start timestamp
        self._current_step: Optional[str] = None

    # ─────────────────────────────────────────
    #  LOGGING METHODS
    # ─────────────────────────────────────────

    def start_step(self, step_name: str):
        """
        Call this BEFORE executing a step.
        Records the start time so we can calculate duration.

        Example:
            memory.start_step("handle_missing")
            df = clean_missing(df, schema)
        """
        self._current_step = step_name
        self._timers[step_name] = time.time()

    def end_step(self, step_name: str, details: Optional[str] = None):
        """
        Call this AFTER a step finishes successfully.
        Calculates duration and logs a success record.

        Example:
            memory.end_step("handle_missing", details="imputed 23 values in Age")
        """
        duration = self._get_duration(step_name)
        detail_msg = details or ""
        if duration:
            detail_msg = f"{detail_msg} ({duration}s)".strip()

        self._steps.append(PipelineStep(
            step=step_name,
            status="success",
            details=detail_msg or None
        ))
        self._current_step = None

    def fail_step(self, step_name: str, error: str):
        """
        Call this if a step raises an exception.
        Logs the error message so we know exactly what broke.

        Example:
            try:
                df = scale_data(df, schema)
                memory.end_step("scaling")
            except Exception as e:
                memory.fail_step("scaling", error=str(e))
        """
        duration = self._get_duration(step_name)
        detail_msg = f"ERROR: {error}"
        if duration:
            detail_msg += f" ({duration}s)"

        self._steps.append(PipelineStep(
            step=step_name,
            status="failed",
            details=detail_msg
        ))
        self._current_step = None

    def skip_step(self, step_name: str, reason: str):
        """
        Call this when a step is intentionally skipped.

        When does this happen?
        - Agent planned 'handle_outliers' but no outliers were found
        - Agent planned 'encoding' but no categorical columns exist
        - A step was in the plan but the data condition wasn't met

        Example:
            memory.skip_step("handle_outliers", reason="no outliers in any column")
        """
        self._steps.append(PipelineStep(
            step=step_name,
            status="skipped",
            details=f"Skipped: {reason}"
        ))

    def log_warning(self, message: str):
        """
        Record a non-critical warning that doesn't belong to a specific step.
        """
        self._steps.append(PipelineStep(
            step="pipeline_warning",
            status="warning",
            details=message
        ))

    # ─────────────────────────────────────────
    #  RETRIEVAL METHODS
    # ─────────────────────────────────────────

    def get_steps(self) -> List[PipelineStep]:
        """
        Returns all recorded steps as List[PipelineStep].
        This goes directly into Module2Response.pipeline_steps.
        """
        return self._steps.copy()

    def get_summary(self) -> str:
        """
        Returns a human-readable summary of what ran.
        Useful for logs and debugging.

        Example output:
            Pipeline summary (4 steps):
              ✓ handle_missing    → imputed 23 values in Age (0.12s)
              ✓ encoding          → encoded 2 columns (0.05s)
              - handle_outliers   → Skipped: no outliers detected
              ✗ scaling           → ERROR: scaler failed on empty column
        """
        if not self._steps:
            return "Pipeline summary: no steps recorded."

        lines = [f"Pipeline summary ({len(self._steps)} steps):"]
        for step in self._steps:
            if step.status == "success":
                icon = "[OK]"
            elif step.status == "failed":
                icon = "[X]"
            else:
                icon = "-"

            detail = f" → {step.details}" if step.details else ""
            lines.append(f"  {icon} {step.step:<25}{detail}")

        return "\n".join(lines)

    def has_failed_steps(self) -> bool:
        """Returns True if any step failed — useful for error checking."""
        return any(s.status == "failed" for s in self._steps)

    def get_failed_steps(self) -> List[PipelineStep]:
        """Returns only the failed steps."""
        return [s for s in self._steps if s.status == "failed"]

    def get_executed_step_names(self) -> List[str]:
        """
        Returns names of steps that actually ran (not skipped/failed).
        Used by rule_engine to avoid running a step twice.
        """
        return [s.step for s in self._steps if s.status == "success"]

    def step_was_run(self, step_name: str) -> bool:
        """Check if a specific step already ran successfully."""
        return step_name in self.get_executed_step_names()

    # ─────────────────────────────────────────
    #  INTERNAL HELPERS
    # ─────────────────────────────────────────

    def _get_duration(self, step_name: str) -> Optional[str]:
        """Calculate elapsed time for a step in seconds."""
        start = self._timers.get(step_name)
        if start:
            elapsed = time.time() - start
            return str(round(elapsed, 3))
        return None

    def __repr__(self):
        total = len(self._steps)
        success = sum(1 for s in self._steps if s.status == "success")
        failed = sum(1 for s in self._steps if s.status == "failed")
        skipped = sum(1 for s in self._steps if s.status == "skipped")
        return (
            f"Memory(total={total}, "
            f"success={success}, failed={failed}, skipped={skipped})"
        )

# Alias for backward compatibility
Memory = PipelineMemory
