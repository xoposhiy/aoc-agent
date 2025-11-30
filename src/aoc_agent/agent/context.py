from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class AgentContext:
    run_id: str
    start_time: float
    output_tokens: int = 0
    
    # Part 1 stats
    part1_output_tokens: int = 0
    part1_duration: float = 0
    part1_finished: bool = False
    part2_duration: float = 0
    part2_finished: bool = False
    part2_output_tokens: int = 0

    # Submission stats
    part1_incorrect: int = 0
    part2_incorrect: int = 0

    # Run Code stats
    part1_run_code_errors: int = 0
    part2_run_code_errors: int = 0
    part1_run_code_success: int = 0
    part2_run_code_success: int = 0
    final_report_written: bool = False
    
    def record_success(self, part: int):
        if part == 1:
            self.part1_finished = True
            self.part1_duration = time.time() - self.start_time
            self.part1_output_tokens = self.output_tokens
        elif part == 2:
            self.part2_finished = True
            self.part2_duration = time.time() - self.start_time
            self.part2_output_tokens = self.output_tokens

    def record_incorrect_submission(self, part: int):
        if part == 1:
            self.part1_incorrect += 1
        elif part == 2:
            self.part2_incorrect += 1

    def record_run_code_error(self):
        if self.part2_finished:
            return
        if not self.part1_finished:
            self.part1_run_code_errors += 1
        else:
            self.part2_run_code_errors += 1

    def record_run_code_success(self):
        if self.part2_finished:
            return
        if not self.part1_finished:
            self.part1_run_code_success += 1
        else:
            self.part2_run_code_success += 1
