import json
from candidate_generator import CandidateGenerator
from ocr_corrector import OCRCorrector
from candidate_retrieval_evaluation import get_failed_and_found_cands
import pandas as pd
import argparse

if __name__ == '__main__':
    cand_generator = CandidateGenerator(path_to_entity_dict='/ivi/ilps/personal/vprovat/REL_files/wiki_frequencies.p')
    ocr_corrector = OCRCorrector(path_to_post_correction_data='/home/vprovat/post_ocr_correction/')
    rows = []
    cnt = 0
    for dataset_name in 'aida_val ace2004  aquaint  clueweb  msnbc  wikipedia'.split():
        for mode in ['original', 'ocr', 'mix']:
            data = [json.loads(line) for line in open(f'data/{dataset_name}_{mode}.jsonl', 'r')]
            res_no_correction = get_failed_and_found_cands(data, cand_generator)
            res_with_correction = get_failed_and_found_cands(data, cand_generator, ocr_corrector, post_correct=True)
            res_no_correction['post_correction_method'] = 'None'
            res_with_correction['post_correction_method'] = 'post_ocr_correction library; 5-grams, beam search'

            rows.append(res_no_correction)
            rows.append(res_with_correction)

    df_table = pd.DataFrame.from_dict(rows)
    df_table.to_csv('results/candidate_retrieval_results_all.tsv', sep='\t')