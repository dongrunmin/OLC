import sys
import os
import cv2
sys.path.insert(0, os.getcwd())
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from utils.lr_scheduler import build_scheduler
from torch.utils.tensorboard import SummaryWriter
import numpy as np
import os
from models import get_model
from utils.config_files_utils import read_yaml, copy_yaml, get_params_values
from utils.torch_utils import get_device, get_net_trainable_params, load_from_checkpoint
from data import get_dataloaders
from metrics.torch_metrics import get_mean_metrics
from metrics.numpy_metrics import get_classification_metrics, get_per_class_loss
from metrics.loss_functions import get_loss
from utils.summaries import write_mean_summaries, write_class_summaries
from data import get_loss_data_input
from data.Nigeria.dataloader import get_dataloader as get_nigeria_seg_dataloader
from data.Nigeria.data_transforms import Nigeria_segmentation_transform
import time

valid_years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
inference_times = []

def evaluate_and_test(net, dataloaders, config, device, save_path, save_path_prob, lin_cls=False):

    def weight_map(crop_size, stride):
      weight = np.ones((crop_size, crop_size), dtype=np.float32)
      border = crop_size - stride
      for i in range(crop_size):
        weight_i = 1.0
        if i < border:
            weight_i *= (1.0 * (i + 1)/border)
        if i > stride:
            weight_i *= (1.0 * (crop_size - i)/border)
        for j in range(crop_size):
            weight_j = 1.0 * weight_i
            if j < border:
                weight_j *= (1.0 * (j + 1)/border)
            if j > stride:
                weight_j *= (1.0 * (crop_size - j)/border)
            weight[i][j] *= weight_j
      return weight

    def evaluate(net, evalloader, config):
        num_classes = config['MODEL']['num_classes']
        input_img_res = config['MODEL']['infer_res']

        predicted_all = []
        labels_all = []

        net.eval()
        results = []
        patch_size = 256
        stride = 128

        crop_weight = weight_map(patch_size, stride)

        with torch.no_grad():
            for step, (sample,img_names) in enumerate(evalloader):
                feat = np.zeros((8, input_img_res, input_img_res, num_classes), dtype=np.float32)
                weights = np.zeros((input_img_res, input_img_res), dtype=np.float32)
                for top in range(0, input_img_res - patch_size + 1, stride):
                  for left in range(0, input_img_res - patch_size + 1, stride):
                    patch_tmp = sample['img'][:,:,:, top:top + patch_size, left:left + patch_size]
                    start_time = time.time()
                    logits = net(patch_tmp.to(torch.float32).to(device))
                    end_time = time.time()
                    inference_times.append(end_time - start_time)

                    logits = logits.permute(0, 1, 3, 4, 2)
                    probabilities = F.softmax(logits, dim=-1).squeeze(0).data.cpu().numpy()

                    feat[:, top:top + patch_size, left:left + patch_size, :] += (probabilities * crop_weight.reshape(1,patch_size,patch_size,1).repeat(8, axis=0)) #.transpose((0, 2, 3, 1))
                    weights[top:top + patch_size, left:left + patch_size] += crop_weight

                feat = (feat.transpose((0,3,1,2)) / weights).transpose((0,2,3,1))
                predicted = np.argmax(feat, axis=-1)
                pos_prob = feat[:,:,:,1] * 255
                pos_prob = pos_prob.astype('uint8')

                for t in range(predicted.shape[0]):
                    cv2.imwrite(os.path.join(save_path, str(valid_years[t]), img_names[0].replace('.pkl', '.png')), (predicted[t]*255).astype('uint8'))
                    cv2.imwrite(os.path.join(save_path_prob, str(valid_years[t]), img_names[0].replace('.pkl', '.png')), pos_prob[t])


        print(
            "-----------------------------------------------------------------------------------------------------------------------------------------------------------------")
        average_inference_time = np.mean(inference_times)
        print(f"Average Inference Time: {average_inference_time:.4f} seconds")


    #------------------------------------------------------------------------------------------------------------------#
    num_classes = config['MODEL']['num_classes']
    lr = float(config['SOLVER']['lr_base'])
    local_device_ids = config['local_device_ids']
    weight_decay = get_params_values(config['SOLVER'], "weight_decay", 0)

    if len(local_device_ids) > 1:
        net = nn.DataParallel(net, device_ids=local_device_ids)
    net.to(device)

    # evaluate model ------------------------------------------------------------------------------------------#
    eval_metrics = evaluate(net, dataloaders['test'], config)



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='PyTorch ImageNet Training')
    parser.add_argument('--config', help='configuration (.yaml) file to use')
    parser.add_argument('--device', default='0,1', type=str,
                         help='gpu ids to use')
    parser.add_argument('--lin', action='store_true',
                         help='train linear classifier only')

    args = parser.parse_args()
    config_file = args.config
    print(args.device)
    device_ids = [int(d) for d in args.device.split(',')]
    lin_cls = args.lin

    device = get_device(device_ids, allow_cpu=False)

    config = read_yaml(config_file)
    config['local_device_ids'] = device_ids

    dataloaders = {}
    dataloaders['test'] = get_nigeria_seg_dataloader(
            paths_file=config['DATASETS']['test']['csv_path'], root_dir=config['DATASETS']['test']['base_dir'],
            transform=Nigeria_segmentation_transform(config['MODEL'], is_training=False, is_testing=True),
            batch_size=config['DATASETS']['test']['batch_size'], shuffle=False, num_workers=config['DATASETS']['test']['num_workers'], return_paths=True)

    model = torch.load(config['MODEL']['model_path'], map_location=device)
    net = get_model(config, device)
    net.load_state_dict(model, strict=True)

    save_path = config['DATASETS']['test']['save_path']
    save_path_prob = config['DATASETS']['test']['save_path_prob']
    for name in valid_years:
        save_path_sub = os.path.join(save_path, str(name))
        save_path_prob_sub = os.path.join(save_path_prob, str(name))
        if save_path_sub and (not os.path.exists(save_path_sub)):
            os.makedirs(save_path_sub)
        if save_path_prob_sub and (not os.path.exists(save_path_prob_sub)):
            os.makedirs(save_path_prob_sub)

    evaluate_and_test(net, dataloaders, config, device, save_path, save_path_prob)
