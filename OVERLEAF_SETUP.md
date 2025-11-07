# Overleaf CLSI Setup Guide

This guide explains how to set up Overleaf CLSI (Common LaTeX Service Interface) for LaTeX compilation in the Hack-A-Job application.

## What is Overleaf CLSI?

Overleaf CLSI is Overleaf's open-source LaTeX compilation service. It allows you to compile LaTeX documents to PDF programmatically without installing LaTeX locally.

## Quick Start (Recommended)

Use the provided Docker Compose file:

```bash
# Start Overleaf CLSI
docker-compose -f docker-compose.overleaf.yml up -d

# Verify it's running
curl http://localhost:3013/health
```

This will start CLSI on `http://localhost:3013` with proper configuration.

## Option 1: Using Docker Compose (Easiest)

The project includes `docker-compose.overleaf.yml` for easy setup:

```bash
docker-compose -f docker-compose.overleaf.yml up -d
```

## Option 2: Using Docker Directly

```bash
# Pull and run the CLSI Docker image
docker run -d \
  --name overleaf-clsi \
  -p 3013:3013 \
  --restart unless-stopped \
  overleaf/clsi
```

## Configuration

Once CLSI is running, add these to your `.env` file:

```bash
# Overleaf CLSI Configuration
OVERLEAF_CLSI_URL=http://localhost:3013
# OVERLEAF_CLSI_KEY=your_api_key_if_required  # Optional
```

## Verify CLSI is Running

Test if CLSI is accessible:

```bash
curl http://localhost:3013/health
```

You should get a response indicating the service is running.

## How It Works

1. When you upload a resume, the system converts it to LaTeX
2. When tailoring, the LaTeX is compiled to PDF using Overleaf CLSI
3. The PDF is returned and stored

## Fallback Behavior

If CLSI is not configured or unavailable, the system will:
1. Try to use local `pdflatex` if installed
2. Fall back to ReportLab PDF generation if both fail

## Troubleshooting

### CLSI not responding
- Check if Docker container is running: `docker ps`
- Check CLSI logs: `docker logs overleaf-clsi`
- Verify port 3013 is accessible: `curl http://localhost:3013/health`

### Compilation errors
- Check the LaTeX code for syntax errors
- Review CLSI logs for detailed error messages
- Ensure all required LaTeX packages are available in CLSI

### Performance
- CLSI compilation typically takes 5-15 seconds
- For faster compilation, consider running CLSI on a dedicated server
- Use connection pooling if handling multiple concurrent requests

## Production Deployment

For production, consider:
- Running CLSI on a separate server/container
- Setting up load balancing for multiple CLSI instances
- Configuring proper authentication (CLSI_KEY)
- Monitoring CLSI health and performance

## Alternative: Local pdflatex

If you prefer not to use CLSI, you can install LaTeX locally:

**macOS:**
```bash
brew install --cask mactex
```

**Linux:**
```bash
sudo apt-get install texlive-full
```

**Windows:**
Download and install MiKTeX from https://miktex.org/

The system will automatically detect and use local `pdflatex` if CLSI is not configured.

