import re
from collections import defaultdict

from numpy.linalg import norm
from numpy import dot, array, zeros


def tokenize(sent):
    return sent.split()


def case_fold(tokens):
    return [x.lower() for x in tokens]


def remove_punctuation(tokens):
    return [re.sub("[.,!&@%+-=()?\[\]{}<>\"'$.*^]", "", x) for x in tokens]


def rm_stop_words(tokens):
    stops = {
        "a",
        "an",
        "the",
        "and",
        "to",
        "is",
        "am",
        "one",
        "two",
        "three",
        "1",
        "2",
        "3",
        "or",
        "",
        "for",
    }
    return [x for x in tokens if not x in stops]


def stem(tokens):
    return [re.sub("ing$", "", x) for x in tokens]


def normalize(sent):
    return stem(rm_stop_words(remove_punctuation(case_fold(tokenize(sent)))))


def tfidf_similarity(docs: dict):
    n_docs = {k: normalize(v) for k, v in docs.items()}

    for k,v in list(n_docs.items()):
        if v =='':
            n_docs.pop(k)

    MIN_DF_COUNT = 5
    MAX_DF_COUNT = len(n_docs) * 0.8
    
    df = defaultdict(int)
    tf = defaultdict(lambda: defaultdict(int))

    # count appearance in docs
    for k, v in n_docs.items():
        for w in set(v):
            df[w] += 1

    # feature reduction
    for w, c in list(df.items()):
        if c < MIN_DF_COUNT or c > MAX_DF_COUNT:
            df.pop(w)

    # count occurences in each doc
    for k, v in n_docs.items():
        for w in v:
            if w in df:
                tf[k][w] += 1

    # quantify importance of each term to the doc
    tfidf = defaultdict(dict)
    for k, v in tf.items():
        for w in v:
            tfidf[k][w] = v[w] / df[w]

    one_hot_sparse = {k: i for i, k in enumerate(df)}
    N = len(df)

    def some_hot(word, weight=1):  # might not be one, so ... some
        v = zeros(N)
        v[one_hot_sparse[word]] = weight
        return v

    def encode_doc(doc_tfidf):
        v = zeros(N)
        for word, weight in doc_tfidf.items():
            v += some_hot(word, weight)
        return v
    if len(tfidf) == 0:
        return {}
    doc_vectors = {k: encode_doc(v) for k, v in tfidf.items()}
    doc_keys, X = zip(*doc_vectors.items())
    X = array(X)
    sim = [
        dot(X, x) / (norm(X, axis=1) * norm(x)) for x in X
    ]  # cosine similarity between all other docs

    return {
        key: sorted(list(zip(doc_keys, sim_vector)), key=lambda x:x[1], reverse=True)
        for key, sim_vector in zip(doc_keys, sim)
    }
