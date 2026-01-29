"""Centralized test reporting utility."""

import json
import os
from datetime import datetime
from typing import Any


class ResultsReporter:
    """
    Structured test results reporter.

    Collects test steps, errors, and metadata, then outputs
    results as JSON for reporting dashboards.
    """

    def __init__(self, test_name: str, output_dir: str = "test_results"):
        """
        Initialize the reporter.

        Args:
            test_name: Name of the test being reported
            output_dir: Directory to save results JSON files
        """
        self.test_name = test_name
        self.output_dir = output_dir
        self.start_time = datetime.now()
        self.steps: list[dict] = []
        self.errors: list[dict] = []
        self.warnings: list[dict] = []
        self.metadata: dict[str, Any] = {}

        os.makedirs(output_dir, exist_ok=True)

    def add_step(
        self,
        name: str,
        status: str = "passed",
        data: dict | None = None
    ) -> None:
        """
        Record a test step.

        Args:
            name: Step description
            status: Step status ('passed', 'failed', 'skipped')
            data: Optional additional data for the step
        """
        step = {
            "name": name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        if data:
            step["data"] = data
        self.steps.append(step)

    def add_error(self, message: str, context: dict | None = None) -> None:
        """
        Record an error.

        Args:
            message: Error message
            context: Optional context information
        """
        error = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        if context:
            error["context"] = context
        self.errors.append(error)

    def add_warning(self, message: str) -> None:
        """Record a warning."""
        self.warnings.append({
            "message": message,
            "timestamp": datetime.now().isoformat(),
        })

    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value."""
        self.metadata[key] = value

    def get_status(self) -> str:
        """Determine overall test status based on steps and errors."""
        if self.errors:
            return "failed"
        if any(step["status"] == "failed" for step in self.steps):
            return "failed"
        return "passed"

    def generate_report(self) -> dict:
        """
        Generate the full test report.

        Returns:
            Complete test report as a dictionary
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        return {
            "test_name": self.test_name,
            "status": self.get_status(),
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": round(duration, 3),
            "steps": self.steps,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "summary": {
                "total_steps": len(self.steps),
                "passed_steps": sum(1 for s in self.steps if s["status"] == "passed"),
                "failed_steps": sum(1 for s in self.steps if s["status"] == "failed"),
                "error_count": len(self.errors),
                "warning_count": len(self.warnings),
            }
        }

    def save(self) -> str:
        """
        Save the report to a JSON file.

        Returns:
            Path to the saved report file
        """
        report = self.generate_report()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.test_name}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        return filepath
