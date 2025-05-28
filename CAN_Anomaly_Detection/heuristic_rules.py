import time
from collections import defaultdict

DM1_PGN = 0xFECA  # J1939 PGN for DM1 messages (65226)
DEFAULT_TIMEOUT = 0.5  # seconds

class HeuristicEngine:
    def __init__(self, timeout_s=DEFAULT_TIMEOUT):
        self.last_seen = {}  # ID → timestamp
        self.prev_data = {}  # ID → data bytes
        self.timeout_s = timeout_s
        self.anomalies = defaultdict(list)  # ID → [reason, ...]

    def check(self, msg):
        timestamp = msg.timestamp
        arb_id = msg.arbitration_id
        reasons = []

        # 1. Timeout check
        if arb_id in self.last_seen:
            delta = timestamp - self.last_seen[arb_id]
            if delta > self.timeout_s:
                reasons.append(f"Timeout: brak ID {hex(arb_id)} przez {delta:.2f}s")
        self.last_seen[arb_id] = timestamp

        # 2. Bit change detection
        if arb_id in self.prev_data:
            prev = self.prev_data[arb_id]
            current = bytes(msg.data)
            if len(prev) == len(current):
                for i in range(len(current)):
                    changed = (~prev[i] & current[i]) & 0xFF  # 0→1 bits
                    if changed:
                        reasons.append(f"Bit 0→1 w bajcie {i}: {bin(changed)}")
        self.prev_data[arb_id] = bytes(msg.data)

        # 3. DM1 content check (SPN/FMI errors in data)
        if self.is_dm1(msg):
            if self.has_dm1_fault(msg):
                reasons.append("DM1: zawiera błędy (DTC != 0)")

        return reasons

    def is_dm1(self, msg):
        """Check if arbitration ID corresponds to PGN 65226 (DM1)"""
        # For J1939: PGN = (ID >> 8) & 0xFFFF
        pgn = (msg.arbitration_id >> 8) & 0xFFFF
        return pgn == DM1_PGN

    def has_dm1_fault(self, msg):
        """Check if DM1 frame contains actual DTCs (SPN/FMI != 0)"""
        # DM1 DTCs start from byte 8, each DTC = 4 bytes
        dtc_start = 8
        dtc_count = (len(msg.data) - dtc_start) // 4
        if dtc_count <= 0:
            return False
        for i in range(dtc_count):
            base = dtc_start + i * 4
            dtc_bytes = msg.data[base:base+4]
            if any(b != 0xFF and b != 0x00 for b in dtc_bytes):
                return True
        return False
