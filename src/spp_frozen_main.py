###############################################################
# spp_frozen_main.py
# Entry point per la build congelata (cx_Freeze).
#
# main.py usa import relativi di pacchetto (`from .Globals import glb`),
# quindi NON può essere congelato come script __main__ di primo livello:
# in quel contesto __package__ è vuoto e ogni import relativo fallisce con
# "attempted relative import with no known parent package".
#
# Questo launcher importa il package `songpressplusplus` (cx_Freeze aggiunge
# la cartella di questo script — src/ — al percorso di ricerca dei moduli,
# rendendo il package individuabile) e ne invoca main() con il corretto
# contesto di pacchetto.
###############################################################

import multiprocessing

# Nota: il nome del package rispecchia la cartella reale su disco
# (src/songpressPlusPlus). Gli import interni sono relativi, quindi il
# nome di primo livello è quello della directory. Python impone la
# corrispondenza esatta del case anche su Windows: usare la stessa
# capitalizzazione della cartella è indispensabile.
from songpressPlusPlus.main import main

if __name__ == "__main__":
    # Necessario nelle build congelate su Windows: evita che i processi
    # figli di multiprocessing rilancino l'intera GUI.
    multiprocessing.freeze_support()
    main()
