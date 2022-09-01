from wikipedia import wikipedia, DisambiguationError
import pickle

class RedirectResolver():
    def __init__(self, path_to_cache=None):
        if path_to_cache:
            self.cache = pickle.load(open(path_to_cache, 'rb'))
        else:
            self.cache = {}

    def process_redirect(self, name):
        '''
        Redirects when needed.
        '''
        if name in self.cache:
            return self.cache[name]
        try:
            pg = wikipedia.page(name.title())
            res = pg.title
        except DisambiguationError:
            res = f"[DISAMB] {name}"
        except:
            # print(f'Failed to find {name} in wikipedia, returning it anyway')  # todo remove
            res = name

        self.cache[name] = res
        return res

    def save_cache(self, path):
        pickle.dump(self.cache, open(path, 'wb'))