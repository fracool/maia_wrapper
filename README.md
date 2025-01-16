# maia_wrapper
wrapper for lc0 to play nice with chess engines using maia. Selects the various strenght models based on what elo you choose in your GUI.

You need to set the following variables:

`LC0_BINARY  = "/opt/homebrew/bin/lc0"
`WEIGHTS_DIR = "/Users/fraser/Documents/HIARCS Chess/EngineData"

The weights directory must contain the models from https://github.com/CSSLab/maia-chess

1100 	maia1 	maia-1100.pb.gz
1500 	maia5 	maia-1500.pb.gz
1900 	maia9 	maia-1900.pb.gz
1200 	maia-1200.pb.gz
1300 	maia-1300.pb.gz
1400 	maia-1400.pb.gz
1600 	maia-1600.pb.gz
1700 	maia-1700.pb.gz
1800 	maia-1800.pb.gz

save this script in the engines folder, e.g. /Users/fraser/Documents/HIARCS Chess/Engines
Then `chmod +x maia.py` and after add the engine as you would to the chess gui of choice.
