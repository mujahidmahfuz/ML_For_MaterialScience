# Source and citation of the MAGNDATA-derived files

The files in this folder (`magndata_entries.csv`, `anchor_by_composition.csv`, `anchor_agreement.csv`, `anchor_confusion_*.csv`, `three_way.csv`) were
derived from structures in **MAGNDATA**, a database of magnetic structures hosted by the **Bilbao Crystallographic Server** (https://cryst.ehu.es).

- **How the structures were obtained.** The official repository download of the server (MAGNDATA, mcif files, version dated 2026-11-01), through a
  registered academic account, after accepting the usage conditions (2026-11-16). The structure files themselves are NOT redistributed here; anyone
  can obtain them in the same way (`https://cryst.ehu.es/magndata/magndata_download.html`).
- **What was derived.** For each collinear, ordered structure, a ferromagnetic / antiferromagnetic / ferrimagnetic label computed from the moments in the
  file (`final/revision/scripts/a16_magndata_anchor.py`), and the agreement of two other label sources with it. No text of the database is reproduced.
- **Condition of use.** The usage conditions require that the Bilbao Crystallographic Server and MAGNDATA are cited in any output that uses them.
  Anyone who reuses these files must cite them as well.

## Required citations

(as listed on https://cryst.ehu.es/wiki/index.php/How_to_cite_the_Bilbao_Crystallographic_Server, read 2026-11-16)

Bilbao Crystallographic Server (generic):
1. M. I. Aroyo, J. M. Perez-Mato, D. Orobengoa, E. Tasci, G. de la Flor, A. Kirov, "Crystallography online: Bilbao Crystallographic Server",
   Bulg. Chem. Commun. 43(2), 183-197 (2011).
2. M. I. Aroyo, J. M. Perez-Mato, C. Capillas, E. Kroumova, S. Ivantchev, G. Madariaga, A. Kirov, H. Wondratschek, "Bilbao Crystallographic Server:
   I. Databases and crystallographic computing programs", Z. Kristallogr. 221, 15-27 (2006), doi:10.1524/zkri.2006.221.1.15.
3. M. I. Aroyo, A. Kirov, C. Capillas, J. M. Perez-Mato, H. Wondratschek, "Bilbao Crystallographic Server. II. Representations of crystallographic point
   groups and space groups", Acta Cryst. A62, 115-128 (2006), doi:10.1107/S0108767305040286.

MAGNDATA:
4. S. V. Gallego, J. M. Perez-Mato, L. Elcoro, E. S. Tasci, R. M. Hanson, K. Momma, M. I. Aroyo, G. Madariaga, "MAGNDATA: towards a database of magnetic
   structures. I. The commensurate case", J. Appl. Cryst. 49, 1750-1776 (2016), doi:10.1107/S1600576716012863.
5. S. V. Gallego, J. M. Perez-Mato, L. Elcoro, E. S. Tasci, R. M. Hanson, M. I. Aroyo, G. Madariaga, "MAGNDATA: towards a database of magnetic structures.
   II. The incommensurate case", J. Appl. Cryst. 49, 1941-1956 (2016), doi:10.1107/S1600576716015491.
6. J. M. Perez-Mato, S. V. Gallego, E. S. Tasci, L. Elcoro, G. de la Flor, M. I. Aroyo, "Symmetry-based computational tools for magnetic
   crystallography", Annu. Rev. Mater. Res. 45, 217-248 (2015), doi:10.1146/annurev-matsci-070214-021008.
7. E. S. Tasci, L. Elcoro, J. M. Perez-Mato, G. de la Flor, G. Madariaga, M. I. Aroyo, "Computational analysis tools for magnetic structures in the Bilbao
   Crystallographic Server", Acta Cryst. B81, 181-191 (2025), doi:10.1107/S2052520625000277.
