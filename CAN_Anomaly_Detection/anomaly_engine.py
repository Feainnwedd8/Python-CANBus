from autoencoder import CANAutoencoderEngine
from heuristic_rules import HeuristicEngine


class AnomalyEngine:
    def __init__(self, use_ai=True, use_heuristic=True):
        self.use_ai = use_ai
        self.use_heuristic = use_heuristic
        self.ai = CANAutoencoderEngine()
        self.heuristic = HeuristicEngine()

    def train_ai(self, messages):
        if self.use_ai:
            self.ai.train(messages)

    def evaluate(self, msg):
        result = {
            "ai": False,
            "heur": [],
        }

        if self.use_ai:
            result["ai"] = self.ai.is_anomalous(msg)

        if self.use_heuristic:
            result["heur"] = self.heuristic.check(msg)

        return result
