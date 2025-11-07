# merge_model.py (Final All-in-One Version)
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

base_model_id = "microsoft/Phi-3-mini-4k-instruct"
adapter_path = r"D:\Ram Dwivedi\Fauxy\Fauxychatbot\Fauxychatmodel\checkpoint-3770"
output_path = "./merged_fauxy_model"

print(f"Loading base model and tokenizer: {base_model_id}")
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    torch_dtype=torch.float16,
    trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)

# --- THE FIX IS INTEGRATED HERE ---
# Manually get the chat template from the loaded tokenizer...
chat_template = tokenizer.chat_template
if chat_template:
    print("Found chat template, injecting it into the main model config...")
    # ...and add it to the main model's configuration before saving.
    base_model.config.chat_template = chat_template
else:
    print("WARNING: Could not find chat template in the tokenizer.")
# --- END OF FIX ---


print(f"Loading LoRA adapter: {adapter_path}")
model = PeftModel.from_pretrained(base_model, adapter_path)

print("Merging the adapter with the base model...")
model = model.merge_and_unload()

print(f"Saving the final merged model to: {output_path}")
model.save_pretrained(output_path)
tokenizer.save_pretrained(output_path)

print("✅ Done! Your final model with the corrected config is ready.")