"""Optional duty-cycle pacing, independent of model scores and random streams."""
import math
import os
import time
from pathlib import Path


def cpu_temperatures():
    values = []
    for zone in Path("/sys/class/thermal").glob("thermal_zone*"):
        try:
            kind = (zone / "type").read_text().strip().lower()
            if "cpu" in kind or "x86_pkg" in kind:
                value = float((zone / "temp").read_text())/1000
                if 0 < value < 120:
                    values.append(value)
        except (OSError, ValueError):
            continue
    return values


class CoolingBreaks:
    def __init__(self):
        self.seconds = float(os.environ.get("KGC_COOLING_SECONDS", "0"))
        self.active_seconds = float(os.environ.get("KGC_ACTIVE_SECONDS", "5"))
        if not math.isfinite(self.seconds) or self.seconds < 0 or not math.isfinite(self.active_seconds) or self.active_seconds <= 0:
            raise ValueError("Cooling seconds must be finite/nonnegative; active seconds must be finite/positive")
        self.last = time.perf_counter()
        self.waited = 0.
        self.max_cpu = float(os.environ.get("KGC_MAX_CPU_C", "0"))
        self.resume_cpu = float(os.environ.get("KGC_RESUME_CPU_C", str(self.max_cpu-10)))
        if self.max_cpu and not 0 < self.resume_cpu < self.max_cpu < 110:
            raise ValueError("Invalid CPU cooling temperature thresholds")
        self.thermal_waited = 0.
        self.temperatures_observed = []
        self.max_thermal_wait = float(os.environ.get("KGC_MAX_THERMAL_WAIT_SECONDS", "180"))
        if not math.isfinite(self.max_thermal_wait) or self.max_thermal_wait <= 0:
            raise ValueError("Thermal wait limit must be finite and positive")

    def thermal_rest(self):
        if not self.max_cpu:
            return
        values = cpu_temperatures()
        if not values:
            return
        self.temperatures_observed.append(max(values))
        if max(values) < self.max_cpu:
            return
        print(f"Cooling at CPU {max(values):.1f} C; resume below {self.resume_cpu:.1f} C", flush=True)
        start = time.perf_counter()
        while values and max(values) > self.resume_cpu:
            if time.perf_counter()-start > self.max_thermal_wait:
                raise RuntimeError("CPU did not cool within the configured limit; run remains incomplete")
            time.sleep(5)
            values = cpu_temperatures()
        elapsed = time.perf_counter()-start
        self.waited += elapsed
        self.thermal_waited += elapsed

    def rest(self):
        if self.seconds and time.perf_counter() - self.last >= self.active_seconds:
            self.thermal_rest()
            start = time.perf_counter()
            time.sleep(self.seconds)
            self.waited += time.perf_counter() - start
            self.last = time.perf_counter()

    def record(self):
        return {"cooling_seconds_per_break": self.seconds, "active_seconds_between_checks": self.active_seconds,
                "cooling_seconds_elapsed": self.waited,
                "cpu_temperature_limit_c": self.max_cpu or None, "cpu_resume_below_c": self.resume_cpu if self.max_cpu else None,
                "thermal_wait_seconds": self.thermal_waited,
                "maximum_single_thermal_wait_seconds": self.max_thermal_wait,
                "max_observed_cpu_temperature_c": max(self.temperatures_observed) if self.temperatures_observed else None,
                "scope": "single process/thread; wall-clock breaks at safe work boundaries; no score, RNG, epoch or selection changes"}
