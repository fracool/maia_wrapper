#!/usr/bin/env python3

import sys
import subprocess
import threading
import queue
import os
import logging

###############################################################################
# LOGGING SETUP
###############################################################################
logging.basicConfig(
    filename="maia_wrapper.log",
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logging.info("Starting Maia wrapper that reads all lines (no lines missed).")

###############################################################################
# ENGINE CONFIGURATION
###############################################################################
LC0_BINARY  = os.environ.get("LC0_BINARY", "/opt/homebrew/bin/lc0")
WEIGHTS_DIR = os.environ.get("WEIGHTS_DIR", os.path.dirname(os.path.abspath(__file__)))

ELO_TO_WEIGHTS = {
    1100: "maia-1100.pb.gz",
    1200: "maia-1200.pb.gz",
    1300: "maia-1300.pb.gz",
    1400: "maia-1400.pb.gz",
    1500: "maia-1500.pb.gz",
    1600: "maia-1600.pb.gz",
    1700: "maia-1700.pb.gz",
    1800: "maia-1800.pb.gz",
    1900: "maia-1900.pb.gz",
}

def get_closest_elo(target_elo: int, available_elos: list[int]) -> int:
    """Return the available Elo closest to target_elo."""
    return min(available_elos, key=lambda e: abs(e - target_elo))

###############################################################################
# HELPER FUNCTIONS
###############################################################################
def launch_engine(weights_file: str) -> subprocess.Popen:
    """
    Launch Lc0 with unbuffered output so we read lines as soon as they're written.
    """
    if not os.path.isfile(weights_file):
        logging.error(f"Weights file not found: {weights_file}")
        raise FileNotFoundError(f"Weights file not found: {weights_file}")
    logging.info(f"Launching Lc0 with weights={weights_file}")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"  # Force unbuffered output

    return subprocess.Popen(
        [LC0_BINARY, f"--weights={weights_file}"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,  # Capture stderr as well
        text=True,
        bufsize=1,  # Line buffering
        env=env,
    )

def kill_engine(proc: subprocess.Popen):
    """Kill the engine process if it's still running."""
    if proc.poll() is None:
        logging.info("Terminating current Lc0 process.")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logging.warning("Engine did not terminate gracefully, killing.")
            proc.kill()

def engine_write(proc: subprocess.Popen, cmd: str):
    """Send a line to Lc0 (if it's alive)."""
    if proc.poll() is not None:
        logging.warning("Engine process is not alive. Cannot write command.")
        return
    logging.debug(f"[TO ENGINE] {cmd}")
    proc.stdin.write(cmd + "\n")
    proc.stdin.flush()

def wrapper_print(msg: str):
    """Output one line to the GUI (stdout)."""
    logging.debug(f"[TO GUI] {msg}")
    print(msg, flush=True)

###############################################################################
# GLOBAL STATE
###############################################################################
new_weights = None
quitting = threading.Event()          # Thread-safe quit flag
changing_weights = threading.Event()  # Thread-safe flag to change weights

def change_weights(elo: int, engine):
    """Change the weights of the engine to match the requested ELO."""
    global new_weights
    closest_elo = get_closest_elo(elo, list(ELO_TO_WEIGHTS.keys()))
    if closest_elo != elo:
        logging.info(f"Requested ELO {elo} not available, using closest: {closest_elo}")
    weights_file = f"{WEIGHTS_DIR}/{ELO_TO_WEIGHTS[closest_elo]}"
    if not os.path.isfile(weights_file):
        logging.error(f"Weights file not found: {weights_file}")
        return
    changing_weights.set()  # Signal to stop main loop
    kill_engine(engine)
    new_weights = weights_file

def customise_command(cmd, engine):
    """Customize command before sending to engine."""
    global collecting_uci_response
    if cmd.strip() == "uci":
        collecting_uci_response = True
        logging.info("Detected 'uci' command from GUI.")
    elif cmd.strip() == "quit":
        logging.info("Detected 'quit' command from GUI.")
        quitting.set()  # Signal all threads to stop
        return cmd

    elif cmd.startswith("setoption name UCI_Elo value"):
        try:
            elo_value = int(cmd.split()[-1])
        except (ValueError, IndexError):
            logging.warning(f"Invalid ELO value in command: {cmd}")
            return ""
        change_weights(elo_value, engine)
        return ""

    elif cmd.startswith("go"):
        # Customise 'go' command
        return "go nodes 1"  # Only search one node recommended by Maia
    return cmd


###############################################################################
# HANDSHAKE CONTROL
###############################################################################
collecting_uci_response = False

logging.info("Entering main event loop.")

###############################################################################
# THREADING SETUP
###############################################################################
output_queue = queue.Queue()

def reader_thread(stream, queue):
    """Read lines from a stream and put them into a queue."""
    for line in iter(stream.readline, ""):
        queue.put(line.strip())
    stream.close()

def writer_thread(proc):
    """Read commands from stdin and send them to the engine."""
    while not quitting.is_set() and not changing_weights.is_set():
        line = sys.stdin.readline().strip()
        if not line:
            continue
        cmd = customise_command(line, proc)
        if cmd:  # Only send valid commands
            logging.debug(f"[FROM GUI] {cmd}")
            engine_write(proc, cmd)

###############################################################################
# INITIAL SETUP
###############################################################################
def initialise_threads(engine):
    """Initialise and start reader and writer threads."""
    threading.Thread(target=reader_thread, args=(engine.stdout, output_queue), daemon=True).start()
    threading.Thread(target=reader_thread, args=(engine.stderr, output_queue), daemon=True).start()
    threading.Thread(target=writer_thread, args=(engine,), daemon=True).start()

UCI_ELO = 1100
init_weights = f"{WEIGHTS_DIR}/{ELO_TO_WEIGHTS[UCI_ELO]}"

###############################################################################
# MAIN LOOP
###############################################################################

def main(weights=init_weights):
    global new_weights
    engine = launch_engine(weights)
    initialise_threads(engine)
    global collecting_uci_response
    if weights != init_weights:
        wrapper_print("uciok")

    while not quitting.is_set() and not changing_weights.is_set():
        try:
            line_out = output_queue.get(timeout=0.1)
            logging.debug(f"[FROM ENGINE] {line_out}")

            if collecting_uci_response:
                if line_out.startswith("id name"):
                    wrapper_print("id name Maia")
                elif line_out.startswith("id author"):
                    wrapper_print("id author Maia Team")
                elif line_out.startswith("option name"):
                    if "UCI_Elo" in line_out or "UCI_LimitStrength" in line_out:
                        continue
                    wrapper_print(line_out)
                elif line_out == "uciok":
                    # Append custom fields before uciok
                    wrapper_print(f"option name UCI_Elo type spin default {UCI_ELO} min 1100 max 1900")
                    wrapper_print("option name UCI_LimitStrength type check default false")
                    wrapper_print(line_out)
                    collecting_uci_response = False
                else:
                    wrapper_print(line_out)
            else:
                wrapper_print(line_out)
        except queue.Empty:
            continue

    logging.info("Shutting down Maia wrapper.")

if __name__ == "__main__":
    main()

    while changing_weights.is_set():
        logging.info("Changing weights.")
        changing_weights.clear()
        main(new_weights)

    if quitting.is_set():
        logging.info("Quitting Maia wrapper.")

    sys.exit(0)
