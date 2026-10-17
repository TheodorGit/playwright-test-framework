"""
Suite profiles: how a suite presents itself in the report.

The framework knows that a run has sections, readable titles and an order.
It does not know what they are. A suite registers one profile naming its
own, which keeps every product word on the suite's side of the line.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

OTHER = "OTHER"
Facts = Callable[[dict], list]


@dataclass
class SuiteProfile:
    """One suite's presentation: its title, its sections, its facts."""

    key: str
    path_prefix: str
    title: str
    # ((section, ((func, title), ...)), ...): one plan, so a test is named once.
    plan: list = field(default_factory=list)
    fact_order: list = field(default_factory=list)
    passed_subhead: str = "Every check below ran against the system under test."

    def __post_init__(self):
        self._section_of = {func: section
                            for section, entries in self.plan for func, _ in entries}
        self._title_of = {func: title
                          for _, entries in self.plan for func, title in entries}
        self._order = [func for _, entries in self.plan for func, _ in entries]

    def section_for(self, func: str) -> str:
        return self._section_of.get(func, OTHER)

    def title_for(self, func: str) -> str:
        return self._title_of.get(func, func)

    def number_for(self, func: str) -> int:
        """The test's place in the run, or 0 for a test the plan does not name."""
        return self._order.index(func) + 1 if func in self._order else 0

    def sections_in_order(self) -> list[str]:
        return [section for section, _ in self.plan] + [OTHER]

    def facts(self, tally: dict) -> list[tuple[str, int]]:
        """What the run actually did, in a fixed order, skipping what it did not."""
        known = [(key, tally[key]) for key in self.fact_order if tally.get(key)]
        extra = [(k, v) for k, v in sorted(tally.items())
                 if k not in self.fact_order and v]
        return known + extra


GENERIC = SuiteProfile(key="generic", path_prefix="", title="Test run")

_REGISTRY: dict[str, SuiteProfile] = {}


def register(profile: SuiteProfile) -> SuiteProfile:
    _REGISTRY[profile.key] = profile
    return profile


def registered() -> list[SuiteProfile]:
    return list(_REGISTRY.values())


def clear():
    _REGISTRY.clear()


def profile_for(nodeid: str) -> SuiteProfile:
    """The profile whose tests this nodeid belongs to, longest prefix winning."""
    path = (nodeid or "").replace("\\", "/")
    matches = [p for p in _REGISTRY.values() if path.startswith(p.path_prefix)]
    return max(matches, key=lambda p: len(p.path_prefix)) if matches else GENERIC


def active() -> SuiteProfile:
    """The profile a whole run is reported under, when exactly one is registered."""
    return _REGISTRY[next(iter(_REGISTRY))] if len(_REGISTRY) == 1 else GENERIC
