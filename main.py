import uvicorn
from fastapi import FastAPI
from flask import Flask
import multiprocessing
import os
import signal
import sys

# Import your FastAPI app
from api import app as fastapi_app

# Import your Flask app
from app import app as flask_app

def run_fastapi():
    uvicorn.run(fastapi_app, host="127.0.0.1", port=8050)

def run_flask():
    flask_app.run(debug=False, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    # Create processes
    fastapi_process = multiprocessing.Process(target=run_fastapi)
    flask_process = multiprocessing.Process(target=run_flask)

    # Start processes
    fastapi_process.start()
    flask_process.start()

    def signal_handler(sig, frame):
        print("Stopping servers...")
        fastapi_process.terminate()
        flask_process.terminate()
        sys.exit(0)

    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Wait for processes to complete
    fastapi_process.join()
    flask_process.join()