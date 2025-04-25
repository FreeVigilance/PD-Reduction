from huggingface_hub import snapshot_download

snapshot_download(repo_id="Vikhrmodels/Vikhr-Gemma-2B-instruct", 
                  local_dir="models/vikhr-gemma-2b-instruct")
