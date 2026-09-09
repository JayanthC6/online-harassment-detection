import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from captum.attr import LayerIntegratedGradients
import warnings
warnings.filterwarnings('ignore')

repo = "Jayant62003/shieldai-distilbert-multilabel"
tokenizer = AutoTokenizer.from_pretrained(repo)
model = AutoModelForSequenceClassification.from_pretrained(repo)
model.eval()

text = "This is a test."
encoding = tokenizer(text, return_tensors="pt", max_length=256, padding="max_length")
input_ids = encoding["input_ids"]
attention_mask = encoding["attention_mask"]

embed_layer = model.distilbert.embeddings

def forward_func(input_ids_):
    batch = input_ids_.shape[0]
    mask = attention_mask.expand(batch, -1)
    outputs = model(input_ids=input_ids_, attention_mask=mask)
    return torch.sigmoid(outputs.logits[:, 0])

lig = LayerIntegratedGradients(forward_func, embed_layer)
baseline_ids = torch.full_like(input_ids, tokenizer.pad_token_id)

try:
    lig.attribute(inputs=input_ids, baselines=baseline_ids, n_steps=5, internal_batch_size=8)
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
