import sys
sys.path.append(r"c:\Users\jayanth\Downloads\online-harassment-detection\backend")
from dotenv import load_dotenv
load_dotenv(r"c:\Users\jayanth\Downloads\online-harassment-detection\backend\.env")
from ml.explain_transformer import compute_ig_attributions, _model, _tokenizer as tokenizer
from captum.attr import IntegratedGradients
import torch

text = "You are an idiot."
label = "Threat"

# Original LIG
res1 = compute_ig_attributions(text, label)

# New IG with inputs_embeds
_labels = ["Safe", "Threat", "Insult", "Identity Hate", "Profanity"]
label_idx = _labels.index(label)
encoding = tokenizer(text, max_length=256, padding="max_length", truncation=True, return_tensors="pt")
input_ids = encoding["input_ids"]
attention_mask = encoding["attention_mask"]
pad_id = tokenizer.pad_token_id
baseline_ids = torch.full_like(input_ids, pad_id)

def forward_func(inputs_embeds_):
    batch = inputs_embeds_.shape[0]
    mask = attention_mask.expand(batch, -1)
    outputs = _model(inputs_embeds=inputs_embeds_, attention_mask=mask)
    return torch.sigmoid(outputs.logits[:, label_idx])

inputs_embeds = _model.distilbert.embeddings(input_ids)
baseline_embeds = _model.distilbert.embeddings(baseline_ids)

ig = IntegratedGradients(forward_func)
attr, delta = ig.attribute(inputs=inputs_embeds, baselines=baseline_embeds, n_steps=50, internal_batch_size=8, return_convergence_delta=True)

attr = attr.sum(dim=-1).squeeze(0)
attr = attr / torch.norm(attr)
attr = attr.detach().numpy()

# Compare top 5 tokens
tokens = tokenizer.convert_ids_to_tokens(input_ids.squeeze(0).tolist())

res2_tokens = []
for i, token in enumerate(tokens):
    if token not in ("[PAD]", "[CLS]", "[SEP]"):
        res2_tokens.append({"token": token, "score": float(attr[i])})

print("LIG top 3:", sorted(res1["tokens"], key=lambda x: abs(x["score"]), reverse=True)[:3])
print("IG top 3:", sorted(res2_tokens, key=lambda x: abs(x["score"]), reverse=True)[:3])
