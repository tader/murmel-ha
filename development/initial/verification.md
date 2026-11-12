# Initial validation

- Python sources compile locally.
- Initial GitHub Actions run passed 12 protocol/configuration tests and metadata validation.
- Model cache and Supervisor-discovery tests additionally cover offline restart and the discovery payload.
- The container pipeline builds linux/amd64 and checks actual Murmel/PyTorch imports before publishing.
- Real model transcription, latency, peak RSS and end-to-end Home Assistant discovery require a locally configured Hugging Face token and target installation. These are not yet verified.
- Model revision defaults to main for the first download, then the resolved snapshot directory is retained across restarts. An explicit commit SHA is supported. No unverified model SHA is embedded in the release.
- No private audio, credentials or integration identifiers are included in the repository.
