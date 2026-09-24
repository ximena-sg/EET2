# Paper build tools

- `make_figures.py` — regenerates `../figures/figure1_architecture.png` and
  `../figures/figure2_workflow.png` (requires `matplotlib`).
- `build_final_docx.py` — builds `../RCES_Paper_AutoRedes_III.docx` by editing
  the official RCES template in place, preserving its exact styles, fonts,
  two-column layout, front-matter table and `[n]` reference numbering.
  Usage: unzip the official `RCES_Template.docx` into a `tpl/` directory next
  to this script, copy the two figure PNGs alongside it, then run
  `python3 build_final_docx.py`.
- `analyze_gitstore_timings.py` — computes n, mean, standard deviation
  (and median/IQR) of per-device backup cycle times from the real Auto-Redes
  III GitStore commit history, to fill in Table 3 with measured figures
  instead of observed ranges (see Section 7.1 of the paper). Requires no new
  experiment, only access to that repository: `python analyze_gitstore_timings.py
  /path/to/gitstore/repo`. Check `classify_device` in the script against the
  real repository's file/commit naming before trusting its output.

The canonical paper text lives in `../RCES_Paper_AutoRedes_III.md`; the DOCX
is the same content rendered in the official RCES (IIETA) template.
