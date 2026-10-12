import logging
from pathlib import Path
LOG_DIR = Path("logs")
LOG_DIR = Path(__file__).resolve().parent / "logs"


# LOG_DIR.mkdir()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    # datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler( 
            LOG_DIR / "pipeline.log",
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
    force=True,
)