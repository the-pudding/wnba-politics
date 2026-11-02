import os
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer as CV
import string
exclude = set(string.punctuation)

def basic_sanitize(in_string):
    '''Returns a very roughly sanitized version of the input string.'''  
    # punctuation goes, except a hyphen inside a word ("hip-check")
    in_string = ''.join([ch for ch in in_string if ch not in exclude or ch in "-'"])
    in_string = in_string.lower()
    in_string = ' '.join(in_string.split())
    return in_string

# The informative prior (Monroe et al. 2008): each word's prior is its share of a
# background corpus, all WNBA coverage, which the notebooks pass as `background`
# (a list of texts, or a dict of counts by word). The site's default;
# FW_PRIOR=uniform gives every word the same pseudo-count instead (the ?checks
# comparison). FW_WEIGHT sets how much the prior weighs: a number is that many
# times the smaller of the two samples; "raw" takes the background's own
# counts, unscaled (as in Cheng et al. 2023's Marked Personas code).
INFORMATIVE = os.environ.get("FW_PRIOR", "informative") != "uniform"
WEIGHT = os.environ.get("FW_WEIGHT", "1")
_SANITIZED = {}

def background_prior(background, cv, n1, n2):
    vocab = cv.vocabulary_
    terms = sorted(vocab, key=vocab.get)
    if isinstance(background, dict):
        if id(background) not in _SANITIZED:
            counts_by_word = {}
            for word, n in background.items():
                key = basic_sanitize(word)
                counts_by_word[key] = counts_by_word.get(key, 0) + n
            _SANITIZED[id(background)] = counts_by_word
        counts_by_word = _SANITIZED[id(background)]
        counts = np.array([counts_by_word.get(t, 0) for t in terms], dtype=float)
    else:
        if id(background) not in _SANITIZED:
            _SANITIZED[id(background)] = [basic_sanitize(t) for t in background]
        bg_cv = CV(decode_error='ignore', vocabulary=vocab, token_pattern=cv.token_pattern,
                   ngram_range=cv.ngram_range, lowercase=cv.lowercase)
        counts = np.asarray(bg_cv.transform(_SANITIZED[id(background)]).sum(axis=0)).ravel().astype(float)
    if WEIGHT == "raw":
        return np.maximum(counts, 1)   # a word the background lacks counts once
    counts += 0.01   # a word the background lacks still gets a sliver
    return float(WEIGHT) * min(n1, n2) * counts / counts.sum()

def bayes_compare_language(l1, l2, ngram = 1, prior=.01, cv = None, background = None):
    '''
    Arguments:
    - l1, l2; a list of strings from each language sample
    - ngram; an int describing up to what n gram you want to consider (1 is unigrams,
    2 is bigrams + unigrams, etc). Ignored if a custom CountVectorizer is passed.
    - prior; either a float describing a uniform prior, or a vector describing a prior
    over vocabulary items. If you're using a predefined vocabulary, make sure to specify that
    when you make your CountVectorizer object.
    - cv; a sklearn.feature_extraction.text.CountVectorizer object, if desired.

    Returns:
    - A list of length |Vocab| where each entry is a (n-gram, zscore) tuple.'''
    if cv is None and type(prior) is not float:
        print("If using a non-uniform prior:")
        print("Please also pass a count vectorizer with the vocabulary parameter set.")
        quit()
    l1 = [basic_sanitize(l) for l in l1]
    l2 = [basic_sanitize(l) for l in l2]
    if cv is None:
        # a hyphenated word ("hip-check") stays one token, as in the cleaned text
        # every word, however rare or common: the prior handles both (Monroe
        # et al. 2008), so there is no minimum count, no cut-off for words in
        # most articles and no cap on the vocabulary
        cv = CV(decode_error = 'ignore', min_df = 1, max_df = 1.0, ngram_range=(1,ngram),
                token_pattern=r"(?u)\S+",
                binary = False)
    # kept sparse: a dense articles-by-words grid runs to gigabytes on full text
    counts_mat = cv.fit_transform(l1+l2)
    # Now sum over languages...
    vocab_size = len(cv.vocabulary_)
    print("Vocab size is {}".format(vocab_size))
    if type(prior) is float:
        priors = np.array([prior for i in range(vocab_size)])
    else:
        priors = prior
    count_matrix = np.empty([2, vocab_size], dtype=np.float32)
    count_matrix[0, :] = np.asarray(counts_mat[:len(l1), :].sum(axis = 0)).ravel()
    count_matrix[1, :] = np.asarray(counts_mat[len(l1):, :].sum(axis = 0)).ravel()
    n1 = 1.*np.sum(count_matrix[0,:])
    n2 = 1.*np.sum(count_matrix[1,:])
    if background is not None and INFORMATIVE:
        priors = background_prior(background, cv, n1, n2)
    a0 = np.sum(priors)
    print("Comparing language...")
    # every word at once: the same sums as the loop in Hessel's version, which
    # a full vocabulary makes too slow
    y1, y2 = count_matrix[0, :].astype(float), count_matrix[1, :].astype(float)
    term1 = np.log((y1 + priors) / (n1 + a0 - y1 - priors))
    term2 = np.log((y2 + priors) / (n2 + a0 - y2 - priors))
    z_scores = (term1 - term2) / np.sqrt(1. / (y1 + priors) + 1. / (y2 + priors))
    index_to_term = {v:k for k,v in cv.vocabulary_.items()}
    sorted_indices = np.argsort(z_scores)
    return [(index_to_term[i], z_scores[i]) for i in sorted_indices]