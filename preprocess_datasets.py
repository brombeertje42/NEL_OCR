import json, argparse
from redirect_resolver import RedirectResolver
from bs4 import BeautifulSoup

rr = RedirectResolver('/ivi/ilps/personal/vprovat/EL_pickles/redirects_cache.p')

def truncate_context(words, window_size=100, mode='left'):
    '''
    words: a list
    mode: 'left' for left context or 'right' for right context

    returns a string
    '''

    assert mode in ['left', 'right'], f'Unknown mode: {mode}. Use left or right'

    if mode == 'left':
        start = max(len(words) - window_size, 0)
        return ' '.join(words[start:])
    else:
        end = min(len(words), window_size)
        return ' '.join(words[:end])

def conll_lines_to_entities(data_lines_split, bio_tags, doc_id=0):
    res = []
    words = [line[0] for line in data_lines_split]

    for i, line in enumerate(data_lines_split):
        tag = bio_tags[i]
        prev_tag = bio_tags[i - 1] if i else 'O'
        prev_line = data_lines_split[i - 1] if i else ''

        if tag == 'O' and prev_tag != 'O':  # an entity ended here
            mention = prev_line[2]
            if len(prev_line) > 4 and prev_line[4].find('/') != -1:
                output = prev_line[4].split('/')[-1].replace('_', ' ')
                output = rr.process_redirect(output)
            else:  # ground-truth NIL entity
                output = 'NIL'

            all_words_left = ' '.join(words[:i]).split()
            all_words_right = ' '.join(words[i:]).split()

            left_context = truncate_context(all_words_left, window_size=100, mode='left')
            right_context = truncate_context(all_words_right, window_size=100, mode='right')

            res.append({'doc_id': doc_id,
                        'mention': mention,
                        'output': output,
                        'left_context': left_context,
                        'right_context': right_context
                        })
    return res


def improve_offset(mention, text, offset, length):  # sometimes the original offset number is wrong
    if text[offset:offset + length] == mention:
        return offset  # it's correct

    for new_offset in range(max(offset - 2 * length, 0), offset):  # naar links!
        if text[new_offset:new_offset + length] == mention:
            return new_offset

    for new_offset in range(offset, min(offset + 2 * length, len(text) - length)):  # naar rechts!
        if text[new_offset:new_offset + length] == mention:
            return new_offset

    return text.find(mention)  # if our heuristics failed

def write_jsonl(data, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in data:
            json_record = json.dumps(line, ensure_ascii=False)
            f.write(json_record + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--PATH_TO_DATA', help="Where the OCRed EL datasets are stored")
    parser.add_argument('--DATASET_NAME', help="Options for xml: ace2004, aquaint, clueweb, msnbc, wikipedia. For conll: aida"
                        )
    parser.add_argument('--MODE', help="Options: ocr, mix or original")
    args = parser.parse_args()
    print(args)
    PATH_TO_DATA = args.PATH_TO_DATA # '/ivi/ilps/personal/vprovat/NEL_OCR_data'
    DATASET_NAME = args.DATASET_NAME
    MODE = args.MODE

    if DATASET_NAME == 'aida':
        doc_path = f"{PATH_TO_DATA}/{DATASET_NAME}/{MODE}/{DATASET_NAME}_{MODE}.conll" if MODE != 'original' else f"{PATH_TO_DATA}/{DATASET_NAME}/{MODE}/{DATASET_NAME}.conll"
        with open(doc_path, encoding='utf-8') as f:
            data_raw_lines = [line for line in f.readlines()]

        # Split the lines and get their tags
        data_lines_split = [line.split('\t') for line in data_raw_lines]
        bio_tags = [line_split[1] if len(line_split) > 1 and line_split[1] in ['B', 'I'] else 'O'
                    for line_split in data_lines_split]

        # Separate the lines into documents
        lines_by_doc = {}
        tags_by_doc = {}
        cur_doc_id = -1
        for i, line in enumerate(data_lines_split):
            if line[0].startswith('-DOCSTART-'):  # a new document begins here
                cur_doc_id = line[0].split()[1].strip('()')
                lines_by_doc[cur_doc_id] = []
                tags_by_doc[cur_doc_id] = []
                continue

            lines_by_doc[cur_doc_id].append(line)
            tags_by_doc[cur_doc_id].append(bio_tags[i])

        docs = {doc_id: conll_lines_to_entities(lines_by_doc[doc_id], tags_by_doc[doc_id], doc_id)
                for doc_id in lines_by_doc.keys()}  # a document is a list of entities w. context?

        docs_val = {doc_id: docs[doc_id] for doc_id in docs.keys() if doc_id.endswith('a')}
        docs_test = {doc_id: docs[doc_id] for doc_id in docs.keys() if doc_id.endswith('b')}
        docs_val_flat = [item for doc_id in docs_val.keys() for item in docs_val[doc_id]]
        docs_test_flat = [item for doc_id in docs_test.keys() for item in docs_test[doc_id]]

        write_jsonl(docs_val_flat, f'data/{DATASET_NAME}_{MODE}_val.jsonl')
        write_jsonl(docs_test_flat, f'data/{DATASET_NAME}_{MODE}_test.jsonl')
    else:

        doc_path = f"{PATH_TO_DATA}/{DATASET_NAME}/{MODE}/{DATASET_NAME}_{MODE}.xml" if MODE != 'original' else f"{PATH_TO_DATA}/{DATASET_NAME}/{MODE}/{DATASET_NAME}.xml"
        with open(doc_path, encoding='utf-8') as f:
            data_raw = f.read()
        soup = BeautifulSoup(data_raw)
        data = []
        # Every document is inside a tag
        for doc in soup.find_all('document'):
            docname = doc['docname']
            text_path = f"{PATH_TO_DATA}/{DATASET_NAME}/{MODE}/RawText/{docname}"
            if MODE != 'original': # inconsistent data format, what can we do..
                text_path = text_path + ".txt"
            #     print(text_path)
            text = open(text_path, 'r').read()
            #     print(text)
            for annotation in doc.find_all('annotation'):  # nb: offset in chars, not tokens
                mention = annotation.find_all('mention')[0].text
                output = annotation.find_all('wikiname')[0].text
                output = rr.process_redirect(output)
                offset = int(annotation.find_all('offset')[0].text)
                length = int(annotation.find_all('length')[0].text)
                offset = improve_offset(mention, text, offset, length)
                cont_left_raw = text[:offset].split()
                cont_right_raw = text[offset + length:].split()
                cont_left = truncate_context(cont_left_raw, 100, 'left')
                cont_right = truncate_context(cont_right_raw, 100, 'right')
                item = {'doc_id': docname,
                        'mention': mention,
                        'output': output,
                        'left_context': cont_left,
                        'right_context': cont_right,
                        }
                data.append(item)

        write_jsonl(data, f'data/{DATASET_NAME}_{MODE}.jsonl')

    # Saving redirects to avoid sending too many queries to the wiki api
    rr.save_cache('/ivi/ilps/personal/vprovat/EL_pickles/redirects_cache.p')