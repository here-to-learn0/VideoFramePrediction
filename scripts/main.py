import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
import torch.nn.functional as F

from dataset import MNIST_Moving
from model import Model
import utils

if __name__ == "__main__":
    # Adding dataloader
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)
    train_set = MNIST_Moving(root='.data/mnist', train=True, download=True)
    test_set = MNIST_Moving(root='.data/mnist', train=False, download=True)

    batch_size = 64

    train_loader = torch.utils.data.DataLoader(
                    dataset=train_set,
                    batch_size=batch_size,
                    
                    shuffle=True)
    test_loader = torch.utils.data.DataLoader(
                    dataset=test_set,
                    batch_size=batch_size,
                    shuffle=False)
    print("Data loaders ready")

    model = Model()
    print("Model Loaded")
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.2)

    train_loss, test_loss, loss_iter, epochs = utils.train_model(model, optimizer, scheduler, criterion,\
                                                                train_loader, test_loader, 100, device)

