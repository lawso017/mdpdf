@echo off
set IMAGE=ghcr.io/lawso017/mdpdf:latest
docker run --rm -v "%cd%:/workspace" -w /workspace %IMAGE% %*
