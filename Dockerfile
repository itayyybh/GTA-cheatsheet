# Container for the GTA Cheatsheet web app (Google Cloud Run; also runs anywhere Docker does).
FROM python:3.12-slim

# Run as a normal user (not root), with a home it can write to.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    HOST=0.0.0.0 \
    PORT=7860
# Create the app folder as `user` (WORKDIR alone would create it owned by root,
# and the app could then not create logs/ at runtime).
RUN mkdir -p /home/user/app/logs
WORKDIR /home/user/app

# Libraries first, so this slow layer is reused when only the code changes.
# CPU-only PyTorch: much smaller than the default build, and there is no GPU.
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir --user -r requirements.txt

# The code and data, then the embeddings (this also downloads the model into the image).
COPY --chown=user . .
RUN python -m runs.build_index

# From here on, never contact the Hugging Face Hub: the model is already in the image.
# Without this, every cold start asks the Hub for model metadata, and Cloud Run's
# shared IPs get rate-limited (HTTP 429), which stalls startup.
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

# Cloud Run sets PORT itself at runtime (8080); 7860 is only the fallback.
EXPOSE 7860
CMD ["python", "-m", "runs.serve"]
