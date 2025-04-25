import torch
import os
import glob
import sys


def load_from_checkpoint(net, checkpoint, partial_restore=False, device=None):
    
    assert checkpoint is not None, "no path provided for checkpoint, value is None"
    if os.path.isdir(checkpoint):
        checkpoint = max(glob.iglob(checkpoint + '/*.pth'), key=os.path.getctime)
        print("loading model from %s" % checkpoint)
        saved_net = torch.load(checkpoint)
    elif os.path.isfile(checkpoint):
        print("loading model from %s" % checkpoint)
        if device is None:
            saved_net = torch.load(checkpoint)
        else:
            saved_net = torch.load(checkpoint, map_location=device)
    else:
        raise FileNotFoundError("provided checkpoint not found, does not mach any directory or file")
    
    if partial_restore:
        net_dict = net.state_dict()
        saved_net = {k: v for k, v in saved_net.items() if (k in net_dict) and (k not in ["linear_out.weight", "linear_out.bias"])}
        print("params to keep from checkpoint:")
        print(saved_net.keys())
        extra_params = {k: v for k, v in net_dict.items() if k not in saved_net}
        print("params to randomly init:")
        print(extra_params.keys())
        for param in extra_params:
            saved_net[param] = net_dict[param]

    net.load_state_dict(saved_net, strict=True)
    return checkpoint


def get_net_trainable_params(net):
    try:
        trainable_params = net.trainable_params
    except AttributeError:
        trainable_params = list(net.parameters())
    print("Trainable params shapes are:")
    print([trp.shape for trp in trainable_params])
    return trainable_params
    
    
def get_device(device_ids, allow_cpu=False):
    if torch.cuda.is_available():
        device = torch.device("cuda:%d" % device_ids[0])
    elif allow_cpu:
        device = torch.device("cpu")
    else:
        sys.exit("No allowed device is found")
    return device

def check_keys(model, pretrained_state_dict):

    ckpt_keys = set(pretrained_state_dict.keys())
    model_keys = set(model.state_dict().keys())
    used_pretrained_keys = model_keys & ckpt_keys
    unused_pretrained_keys = ckpt_keys - model_keys
    missing_keys = model_keys - ckpt_keys
    #pprint.pprint(model_keys)
    #pprint.pprint(ckpt_keys)
    logger.info('missing keys:{}'.format(len(missing_keys)))
    #logger.info('unused checkpoint keys:{}'.format(len(unused_pretrained_keys)))
    #logger.info('used keys:{}'.format(len(used_pretrained_keys)))
    #pprint.pprint("Unused: {}".format(unused_pretrained_keys))
    #assert len(used_pretrained_keys) > 0, 'load NONE from pretrained checkpoint'
    return True

def load_pretrain(model, pretrained_path):
    device = torch.cuda.current_device()
    pretrained_dict = torch.load(pretrained_path, map_location = lambda storage, loc: storage.cuda(device))
    #if 'state_dict' in pretrained_dict.keys():
    #    pretrained_dict = remove_prefix(pretrained_dict['state_dict'], 'module.')
    #else:
    #    pretrained_dict = remove_prefix(pretrained_dict, 'module.')
    #check_keys(model, pretrained_dict['state_dict'])
    model.load_state_dict(pretrained_dict, strict=False)
    return model
