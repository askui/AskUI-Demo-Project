"""Allow running as: python -m sil_mock_service"""
from .server import run_server, FIXTURES_DIR
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Honda SIL Mock Service")
parser.add_argument("--port", type=int, default=5100)
parser.add_argument("--fixtures", type=str, default=str(FIXTURES_DIR))
args = parser.parse_args()
run_server(port=args.port, fixtures_dir=Path(args.fixtures))
