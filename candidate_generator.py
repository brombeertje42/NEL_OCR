import pickle
class CandidateGenerator():
    def __init__(self, path_to_entity_dict):
        self.entity_dict = pickle.load(open(path_to_entity_dict, 'rb'))

    def preprocess_mention_name(self, name): # NB: there might be more cases where preprocessing is needed! keep track of the errors
        if name in self.entity_dict:
            return name
        if name.lower() in self.entity_dict:
            return name.lower()
        if name.title() in self.entity_dict:
            return name.title()

        return name

    # todo: add resolving redirects (it might be too slow but more precise)
    def get_candidates(self, mention_raw):
        mention = self.preprocess_mention_name(mention_raw)
        if mention in self.entity_dict:
            return self.entity_dict[mention]
        else:
            # print(f'Failed to find candidates for {mention_raw}, preprocessed as {mention}')
            return {'NIL':1}