import tracemalloc

class MemoryAnalyzer:
    def __init__(self, growth_threshold_bytes=2_000_000): self.threshold=growth_threshold_bytes; self.baseline=None
    def start(self):
        if not tracemalloc.is_tracing(): tracemalloc.start()
        self.baseline=tracemalloc.get_traced_memory()[0]
    def snapshot(self):
        current, peak=tracemalloc.get_traced_memory()
        baseline=self.baseline if self.baseline is not None else current
        growth=max(0,current-baseline)
        return {"current_bytes":current,"peak_bytes":peak,"growth_since_baseline_bytes":growth,
                "growth_suspected":growth>=self.threshold,"interpretation":"Tăng bộ nhớ là dấu hiệu cần điều tra; không chứng minh memory leak hoặc buffer overflow."}
