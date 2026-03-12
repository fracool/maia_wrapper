# Maia Wrapper

A UCI-compatible wrapper for the [Lc0](https://lczero.org/) chess engine that lets you play against [Maia](https://maiachess.com/) - a human-like chess engine trained on real online games. Select a strength level between **1100** and **1900 Elo** directly from your chess GUI, and the wrapper handles everything else.

## How It Works

Maia Wrapper sits between your chess GUI and Lc0, intercepting UCI commands to:

- **Swap neural network weights** when you change the Elo setting
- **Limit search to 1 node** (as recommended by the Maia authors for realistic play)
- **Present a clean UCI interface** with a custom `UCI_Elo` option

## Prerequisites

- **Python 3.10+**
- **[Lc0](https://github.com/LeelaChessZero/lc0)** (the Leela Chess Zero engine)
- **Maia weight files** — download from [CSSLab/maia-chess](https://github.com/CSSLab/maia-chess/tree/master/maia_weights)

### Supported Models

| Elo  | Weight File        |
|------|--------------------|
| 1100 | maia-1100.pb.gz    |
| 1200 | maia-1200.pb.gz    |
| 1300 | maia-1300.pb.gz    |
| 1400 | maia-1400.pb.gz    |
| 1500 | maia-1500.pb.gz    |
| 1600 | maia-1600.pb.gz    |
| 1700 | maia-1700.pb.gz    |
| 1800 | maia-1800.pb.gz    |
| 1900 | maia-1900.pb.gz    |

## Installation

1. **Download Maia weight files** from the [maia-chess repository](https://github.com/CSSLab/maia-chess/tree/master/maia_weights) and place them all in a single directory.

2. **Clone this repository** (or download `maia.py`):
   ```bash
   git clone https://github.com/fracool/maia_wrapper.git
   ```

3. **Make the script executable:**
   ```bash
   chmod +x maia.py
   ```

4. **Configure paths** — either edit the defaults at the top of `maia.py`, or set environment variables:
   ```bash
   export LC0_BINARY="/path/to/lc0"
   export WEIGHTS_DIR="/path/to/maia/weights"
   ```

5. **Add the engine to your chess GUI** — point it at `maia.py` just as you would any other UCI engine.

## Configuration

| Variable      | Description                        | Default                                              |
|---------------|------------------------------------|------------------------------------------------------|
| `LC0_BINARY`  | Path to the Lc0 binary             | `/opt/homebrew/bin/lc0`                              |
| `WEIGHTS_DIR` | Directory containing weight files  | Directory where `maia.py` is located                 |

These can be set as environment variables or edited directly in `maia.py`.

## Usage

Once added to your chess GUI, the engine will appear as **Maia**. Use the `UCI_Elo` option in your GUI's engine settings to select a strength level from 1100 to 1900. The wrapper will automatically load the appropriate Maia model.

If your GUI sends an Elo value that doesn't exactly match a model (e.g. 1250), the wrapper will pick the closest available level.

## Logging

The wrapper writes a debug log to `maia_wrapper.log` in the working directory, which can be helpful for troubleshooting.

## License

See [LICENSE](LICENSE) for details.
