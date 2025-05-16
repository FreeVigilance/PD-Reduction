import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from free_vigilance_reduction.core import FreeVigilanceReduction

base_dir     = os.path.dirname(__file__)
config_path  = os.path.join(base_dir, 'config', 'profiles.json')
regex_path   = os.path.join(base_dir, 'config', 'regex_patterns.json')
input_path   = os.path.join(base_dir, 'inputs', 'input.txt')
output_path  = os.path.join(base_dir, 'outputs', 'input_redacted.txt')
report_path  = os.path.join(base_dir, 'outputs', 'report.json')

fvr = FreeVigilanceReduction(
    config_path=config_path,
    regex_path=regex_path
)

print("Загруженные профили:", fvr.config_manager.get_profile_list())

report = fvr.process_file(input_path, profile_id="demo_profile")

report.save_to_file(report_path)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    text_to_write = getattr(report, 'anonymized_text', None) or getattr(report, 'reduced_text', '')
    f.write(text_to_write)

print("Обработка завершена.")
print(f"  Анонимизированный текст: {output_path}")
print(f"  Отчёт: {report_path}")
