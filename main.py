from icecream import ic
import ssl
import logging
from app.app import app
import uvicorn
import sys
import os
from os import getenv
# import pwd
import json
import time
# import pytz
from tempfile import gettempdir
# import fcntl
# import aiofiles
# import httptools
# import httpx
# import uvloop
# from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
from dotenv import dotenv_values

if __name__ == "__main__":
    # Load the .env file
    load_dotenv(".env")
    # Set up basic authentication
    # security = HTTPBasic()
    # uvloop.install()
    # Ensure we are relating imports to are current directory
    # env_config ={**dotenv_values(".env"), **os.environ  }
    # print(env_config)
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # parent_dir = os.path.dirname(current_dir)
    # sys.path.append(current_dir)
    # HOST = os.getenv("HOST")  # , '127.0.0.1')
    # PORT = os.getenv("PORT")  # , 8443)
    # ssl_cert = os.getenv('CERT_FILE', '../certs/example.com+5.pem')
    # ssl_key = os.getenv('KEY_FILE', '../certs/example.com+5-key.pem')
    # # If cert or key file not present, create new certs
    # if not os.path.isfile(ssl_cert) or not os.path.isfile(ssl_key):
    #     # NOTE: This [genert] will create certificates matching
    #     # the file names listed in CERTFILE and KEYFILE at the top
    #     # gencert.gencert(rootDomain)
    #     from os.path import dirname as up
    #     dir = up(up(__file__))
    #     cert_file_path = os.path.join(dir, "certs")
    #     ssl_cert = os.path.join(cert_file_path, "example.com+5.pem")
    #     ssl_key = os.path.join(cert_file_path, "example.com+5-key.pem")
    #     print("Certfile(s) NOT present; new certs created.")
    # else:
    #     print("Certfiles Verified Present")

    # ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    # ssl_context.load_cert_chain(ssl_cert, ssl_key)
    # ssl_context.check_hostname = False
    # ssl_context.verify_mode = ssl.CERT_NONE
    # logging.basicConfig(level=logging.INFO)
    # logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info(f"WORKER STARTING with pid {os.getpid()}")
    config = uvicorn.Config(
        app,
        host=HOST,
        port=PORT,
        # ssl_keyfile=ssl_key,
        # ssl_certfile=ssl_cert,
        # ssl_version=ssl.PROTOCOL_TLS,
        reload=True, log_level="debug",
        workers=4, limit_max_requests=1024
    )
    server = uvicorn.Server(config)
    server.run()
