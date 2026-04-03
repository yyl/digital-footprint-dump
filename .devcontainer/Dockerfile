FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Copy uv binaries directly from astral's official image
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /bin/
