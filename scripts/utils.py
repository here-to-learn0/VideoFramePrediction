import os
import torch 
import numpy as np
from tqdm import tqdm
from torchvision.utils import make_grid
import matplotlib.pyplot as plt
import wandb

def train_epoch(model, train_loader, optimizer, criterion, epoch, device):
    """ Training a model for one epoch """
    
    loss_list = []
    progress_bar = tqdm(enumerate(train_loader), total=len(train_loader))
    for idx, (seq, target) in progress_bar:

        seq = seq.type(torch.FloatTensor).to(device)
        target = target.type(torch.FloatTensor).to(device)
        
        # Clear gradients w.r.t. parameters
        optimizer.zero_grad()
        
        predictions = model(seq)
        predictions = predictions.to(device)

        full_seq = torch.cat((seq, target), dim=1)

        loss = criterion(predictions[:, :, :, :, :], full_seq[:, 1:, :, :, :])
        
        loss_list.append(loss.item())

        # Getting gradients w.r.t. parameters
        loss.backward()
         
        # Updating parameters
        optimizer.step()
        
        progress_bar.set_description(f"Epoch {epoch+1} Iter {idx+1}: loss {loss.item():.5f}. ")
        if idx % 10 == 0:
            wandb.log({"loss": loss})

    mean_loss = np.mean(loss_list)

    return mean_loss, loss_list


@torch.no_grad()
def eval_model(model, eval_loader, criterion, device):
    """ Evaluating the model for either validation or test """
    loss_list = []
    pbar = tqdm(enumerate(eval_loader), total=len(eval_loader))
    for idx, (seq, target) in pbar:
        
        seq = seq.type(torch.FloatTensor).to(device)
        target = target.type(torch.FloatTensor).to(device)
        
        predictions = model(seq)
        predictions = predictions.to(device)
                
        loss = criterion(predictions[:, 9:, :, :, :], target)
        loss_list.append(loss.item())
            
        pbar.set_description(f"Test loss: loss {loss.item():.2f}")
    mean_loss = np.mean(loss_list)
    visualize_results(model, eval_loader, device)
    return mean_loss


def train_model(model, optimizer, scheduler, criterion, train_loader,\
                valid_loader, num_epochs, device):
    """ Training a model for a given number of epochs"""
    
    train_loss = []
    val_loss =  []
    loss_iters = []
    epochs = []
    
    for epoch in range(num_epochs):
           
        # validation epoch
        model.eval()  # important for dropout and batch norms
        loss = eval_model(
                    model=model, eval_loader=valid_loader,
                    criterion=criterion, device=device
            )
        val_loss.append(loss)
        epochs.append(epoch+1)
        
        # training epoch
        model.train()  # important for dropout and batch norms
        mean_loss, cur_loss_iters = train_epoch(
                model=model, train_loader=train_loader, optimizer=optimizer,
                criterion=criterion, epoch=epoch, device=device
            )
        scheduler.step()
        train_loss.append(mean_loss)
        loss_iters = loss_iters + cur_loss_iters
        

        print(f"Epoch {epoch+1}/{num_epochs}")
        print(f"    Train loss: {round(mean_loss, 5)}")
        print(f"    Valid loss: {round(loss, 5)}")
        print("\n")
        saving_model(model, optimizer, epoch)
        
    print(f"Training completed")
    return train_loss, val_loss, loss_iters, epochs


def saving_model(model, optimizer, epoch):
    if not os.path.exists("models"):
        os.makedirs("models")
    save_path = f"models/model_{epoch+1}.pth"
    torch.save({
        'epoch' : epoch,
        'model_state_dict' : model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        # 'stats': stats
    }, save_path)
    

def loading_model(model, path):
    optimizer = torch.optim.Adam(params=model.parameters(), lr= 3e-4)
    checkpoint =  torch.load(path)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    epoch = checkpoint['epoch']
    # stats = checkpoint['stats']
    return model, optimizer, epoch

def save_results(grid, name):
    fix, axs = plt.subplots()
    fix.set_size_inches(25,8)

    axs.imshow(grid.cpu().numpy().transpose(1,2,0))
    axs.set(xticklabels=[], yticklabels=[], xticks=[], yticks=[])
    fix.savefig(f"{name}.png", format="png", bbox_inches="tight")

def visualize_results(model, test_loader, device):
    test_input, test_target = next(iter(test_loader))
    
    test_input = test_input.to(device)
    test_target = test_target.to(device)
    
    full_gt_seq = torch.cat((test_input, test_target), dim=1)

    model.eval() 
    with torch.no_grad():
        predictions = model(test_input)
    
    grid_gt = make_grid(full_gt_seq[0])
    save_results(grid_gt, "gt")

    grid_out = make_grid(predictions[0])
    save_results(grid_out, "output")