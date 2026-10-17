"""Single-process unified backend, runnable locally or behind the Site proxy."""
import argparse
import os
from pathlib import Path
import uvicorn
from .app import create_app

parser=argparse.ArgumentParser(description='Kiki unified FastAPI prototype')
parser.add_argument('--host',default='127.0.0.1')
parser.add_argument('--port',type=int,default=int(os.environ.get('PORT','8765')))
parser.add_argument('--data-dir',type=Path,default=Path(os.environ.get('KIKI_DATA_DIR','work/backend')))
args=parser.parse_args()
uvicorn.run(create_app(args.data_dir),host=args.host,port=args.port,ws_max_size=1_000_000,access_log=False)
