import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

class CANAutoencoder(nn.Module):
    def __init__(self, input_size=10, hidden_size=16):
        super(CANAutoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 8)
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, input_size)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

class CANAutoencoderEngine:
    def __init__(self, threshold=0.1, device='cpu'):
        self.device = device
        self.model = CANAutoencoder().to(self.device)
        self.threshold = threshold
        self.trained = False

    def preprocess(self, msg):
        vec = [msg.arbitration_id / 2048.0, msg.dlc / 8.0] + [b / 255.0 for b in msg.data] + [0.0] * (8 - len(msg.data))
        return torch.tensor(vec[:10], dtype=torch.float32).to(self.device)

    def train(self, messages, epochs=10, lr=0.001):
        self.model.train()
        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        loss_fn = nn.MSELoss()
        data = torch.stack([self.preprocess(msg) for msg in messages])
        for epoch in range(epochs):
            output = self.model(data)
            loss = loss_fn(output, data)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        self.trained = True

    def is_anomalous(self, msg):
        if not self.trained:
            return False
        self.model.eval()
        with torch.no_grad():
            x = self.preprocess(msg)
            output = self.model(x)
            loss = nn.functional.mse_loss(output, x)
            return loss.item() > self.threshold

    def save_model(self, path="model.pth"):
        torch.save({
            "model_state": self.model.state_dict(),
            "threshold": self.threshold
        }, path)

    def load_model(self, path="model.pth"):
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state"])
        self.threshold = checkpoint.get("threshold", 0.05)
        self.trained = True