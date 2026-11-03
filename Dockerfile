# Container for the GTA Cheatsheet web app (Hugging Face Spaces, Docker SDK).
FROM python:3.12-slim

# Spaces runs the container as user 1000; give it a home it can write to.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    HOST=0.0.0.0 \
    PORT=7860
WORKDIR /home/user/app

# Libraries first, so this slow layer is reused when only the code changes.
# CPU-only PyTorch: much smaller than the default build, and Spaces has no GPU.
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir --user -r requirements.txt

# The code and data, then the embeddings (this also downloads the model into the image).
COPY --chown=user . .
RUN python -m runs.build_index

EXPOSE 7860
CMD ["python", "-m", "runs.serve"]
