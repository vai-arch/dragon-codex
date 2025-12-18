# Conda-style (portable)

conda env export --no-builds > environment.yml

## Later, on the other machine

conda env create -f environment.yml
conda activate codex
