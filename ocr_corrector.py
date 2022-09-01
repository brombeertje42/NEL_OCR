import pickle
import torch
from pytorch_beam_search import seq2seq
from post_ocr_correction import correction
import re

class OCRCorrector():
    def __init__(self, path_to_post_correction_data):
        # load vocabularies and model
        with open(path_to_post_correction_data + "data/models/en/model_en.arch", "rb") as file:
            architecture = pickle.load(file)
        source = list(architecture["in_vocabulary"].keys())
        target = list(architecture["out_vocabulary"].values())
        self.source_index = seq2seq.Index(source)
        self.target_index = seq2seq.Index(target)

        # remove keys from old API of pytorch_beam_search
        for k in [
            "in_vocabulary",
            "out_vocabulary",
            "model",
            "parameters"
        ]:
            architecture.pop(k)
        self.model = seq2seq.Transformer(self.source_index, self.target_index, **architecture)
        state_dict = torch.load(
            path_to_post_correction_data + "data/models/en/model_en.pt",
            map_location=torch.device("cpu")  # comment this line if you have a GPU
        )

        # change names from old API of pytorch_beam_search
        state_dict["source_embeddings.weight"] = state_dict.pop("in_embeddings.weight")
        state_dict["target_embeddings.weight"] = state_dict.pop("out_embeddings.weight")
        self.model.load_state_dict(state_dict)
        self.model.eval()

    def correct_ocr(self, text):
        _, n_grams_beam = correction.n_grams(
            text,
            self.model,
            self.source_index,
            self.target_index,
            5,
            "beam_search",
            "triangle"
        )
        return n_grams_beam
