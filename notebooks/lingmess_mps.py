"""LingMess (fastcoref) on Apple's MPS device.

The model builds its mention-pair category labels as a float64 NumPy array and
moves it to the model's device; MPS has no float64, so the call fails. The
labels are small integers: the same method with an int64 array works on MPS.
    import lingmess_mps   # before LingMessCoref(device="mps")
"""
import numpy as np, torch
import fastcoref.coref_models.modeling_lingmess as ML

def _get_categories_labels(self, tokens, subtoken_map, new_token_map, span_starts, span_ends):
    batch_size, max_k = span_starts.size()
    spans = []
    for b, (starts, ends) in enumerate(zip(span_starts.cpu().tolist(), span_ends.cpu().tolist())):
        doc_spans = []
        for start, end in zip(starts, ends):
            token_indices = [new_token_map[b][idx] for idx in set(subtoken_map[b][start:end + 1]) - {None}]
            span = {tokens[b][idx].lower() for idx in token_indices if idx is not None}
            pronoun_id = ML.get_pronoun_id(span)
            doc_spans.append((span - ML.STOPWORDS, pronoun_id))
        spans.append(doc_spans)
    categories_labels = np.zeros((batch_size, max_k, max_k), dtype=np.int64) - 1
    for b in range(batch_size):
        for i in range(max_k):
            for j in range(i):
                categories_labels[b, i, j] = ML.get_category_id(spans[b][i], spans[b][j])
    categories_labels = torch.tensor(categories_labels, device=self.device)
    categories_masks = [categories_labels == cat_id for cat_id in range(self.num_cats - 1)] + [categories_labels != -1]
    categories_masks = torch.stack(categories_masks, dim=1).int()
    return categories_labels, categories_masks

ML.LingMessModel._get_categories_labels = _get_categories_labels
