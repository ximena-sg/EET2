# Paper build tools

- `make_figures.py` — regenerates `../figures/figure1_architecture.png` and
  `../figures/figure2_workflow.png` (requires `matplotlib`).
- `build_final_docx.py` — builds `../RCES_Paper_AutoRedes_III.docx` by editing
  the official RCES template in place, preserving its exact styles, fonts,
  two-column layout, front-matter table and `[n]` reference numbering.
  Usage: unzip the official `RCES_Template.docx` into a `tpl/` directory next
  to this script, copy the two figure PNGs alongside it, then run
  `python3 build_final_docx.py`.

The canonical paper text lives in `../RCES_Paper_AutoRedes_III.md`; the DOCX
is the same content rendered in the official RCES (IIETA) template.
