from models.STMamba.STMamba import STMamba

def get_model(config, device):
    model_config = config['MODEL']

    if model_config['architecture'] == "STMamba":
        return STMamba(model_config).to(device)

    else:
        raise NameError("Model architecture %s not found, choose from: 'STMamba'")
