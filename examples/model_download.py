from transformers import AutoModelForCausalLM, AutoTokenizer
import os

model_name = "Vikhrmodels/Vikhr-Gemma-2B-instruct"
model_path = os.path.expanduser("~/models/Vikhr-Gemma-2B-instruct")

os.makedirs(model_path, exist_ok=True)

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

tokenizer.save_pretrained(model_path)
model.save_pretrained(model_path)

print(f"Модель и токенизатор сохранены в {model_path}")