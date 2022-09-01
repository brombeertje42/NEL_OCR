import json
from candidate_generator import CandidateGenerator
from ocr_corrector import OCRCorrector
from tqdm import tqdm


def evaluate_candidate_retrieval(data, res):
    return {'failed to retrieve': "{:.4f}".format(len(res['failed_cands']) / len(data)),
            'managed to retrieve': "{:.4f}".format(len(res['found_cands']) / len(data)),
            'NIL in ground truth': "{:.4f}".format(len(res['nil_cands']) / len(data)),
            'disamb. pages in ground truth': "{:.4f}".format(len(res['weird_gt']) / len(data)),

            }

def get_failed_and_found_cands(data, cand_generator, ocr_corrector=None, post_correct=False):
    # todo: is it a good idea to pass cand_generator or is it better to keep it global?
    res = {'failed_cands': [],
           'found_cands': [],
           'nil_cands': [],
           'weird_gt': []}

    for item in tqdm(data):
        output = item['output']
        ment = item['mention']
        if output.startswith('NIL'):  # a NIL entity in gt
            res['nil_cands'].append({'mention': ment,
                                 'ground truth': output})
            continue

        if output.startswith('[DISAMB]'): # a disambiguation page in gt
            res['weird_gt'].append({'mention': ment,
                                 'ground truth': output})
            continue

        if post_correct:
            variants = [ment, ocr_corrector.correct_ocr(ment)]
        else:
            variants = [ment]

        # Try all possible word variants (corrected and not) of the mention, find their candidates
        cands_all = set()
        for ment_var in variants:
            cands_raw = cand_generator.get_candidates(ment_var)
            cands = [cand.replace('_', ' ') for cand in cands_raw.keys()]
            cands_all = cands_all.union(set(cands))

        if output not in cands_all:
            res['failed_cands'].append({'mention': ment,
                                 'ground truth': output,
                                 'candidates': cands})
        else:
            res['found_cands'].append({'mention': ment,
                                'ground truth': output,
                                'candidates': cands})

    return res