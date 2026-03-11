#!/usr/bin/env python3
import sys
import matplotlib
matplotlib.use("Qt5Agg")

from qworld.app import QWorldApp


def main():
    app = QWorldApp(sys.argv)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
