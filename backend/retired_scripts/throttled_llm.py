# throttled_llm.py
import time
import random
from typing import Any, Dict, Optional
from langchain_core.runnables import Runnable

class ThrottledRunnable(Runnable):
    def __init__(
        self,
        runnable: Runnable,
        rpm_budget: int = 30,          # set conservatively (you can raise later)
        max_retries: int = 8,
        backoff_cap_s: float = 90.0,
        jitter_s: float = 0.25,
    ):
        self.runnable = runnable
        self.min_interval_s = 60.0 / max(rpm_budget, 1)
        self.max_retries = max_retries
        self.backoff_cap_s = backoff_cap_s
        self.jitter_s = jitter_s
        self._next_ok_time = 0.0

    def _wait_turn(self):
        now = time.time()
        if now < self._next_ok_time:
            time.sleep(self._next_ok_time - now)
        # schedule next slot (+ jitter)
        self._next_ok_time = time.time() + self.min_interval_s + random.uniform(0, self.jitter_s)

    def invoke(self, input: Any, config: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        last_err = None
        for attempt in range(self.max_retries):
            self._wait_turn()
            try:
                return self.runnable.invoke(input, config=config, **kwargs)
            except Exception as e:
                last_err = e
                # exponential backoff with jitter (good for 429)
                sleep_s = min(self.backoff_cap_s, (2 ** attempt)) + random.uniform(0, self.jitter_s)
                time.sleep(sleep_s)
        raise last_err