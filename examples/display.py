from threading import local
from vilib import Vilib

def main():
    Vilib.camera_start(inverted_flag=False)
    Vilib.display(local=True,web=True)

if __name__ == "__main__":
    main()