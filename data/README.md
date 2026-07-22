# Data directories

- `raw/`: source files, never committed
- `interim/`: temporary transformations, never committed
- `processed/`: complete analytical outputs, never committed by default
- `dashboard/`: only disclosure-checked files approved for public deployment

The restricted ATLAS isolate file and row-level derivatives must remain outside GitHub. The pipeline writes a SHA-256 source manifest for traceability. Public release of any ATLAS-derived aggregate still requires confirmation against the applicable Vivli data-use agreement.

