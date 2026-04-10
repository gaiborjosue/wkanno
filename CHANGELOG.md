# Changelog

## 0.1.1

- Fixed box and segment matching for annotations whose segment names are prefixed with `Annotations `.
- Made box-name lookup tolerant of case differences and pasted curly quote characters from chat apps.
- Added regression tests covering the live `WM 2` and `GM 1` matching failures.

## 0.1.0

- Initial public CLI scaffold for WebKnossos annotation workflows.
- Added commands for `inspect`, `list-boxes`, `download-raw`, `extract-labels`, `extract-archive`, `export-nifti`, and `fetch-box`.
- Added support for direct REST access against older WebKnossos API deployments.
- Added aligned raw-patch download, label extraction, valid-mask creation, and NIfTI export.
- Added unit tests covering overlap computation, NML parsing, segment fallback resolution, and box listing summaries.