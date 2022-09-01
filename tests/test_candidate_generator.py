from candidate_generator import CandidateGenerator

if __name__ == '__main__':
    cand_gen = CandidateGenerator(path_to_entity_dict='/ivi/ilps/personal/vprovat/REL_files/wiki_frequencies.p')
    print(cand_gen.get_candidates('Michael Jordan'))
    print(cand_gen.get_candidates('U. S.'))
