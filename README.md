\# Emulator Launcher



A simple Windows launcher for managing and running executable files with icon extraction and renaming.



\## Features

\- Extract and display icons from EXE files

\- Rename display names without affecting files

\- Double-click to launch

\- Persistent configuration



\## Installation

Look at requirements.txt



\## Usage

Once the requirements in requirements.txt have been met, run with python 3.13 or later



\## Building EXE

Put this command line in PowerShell: python -m PyInstaller --onefile --windowed --icon=launcher\_icon.ico --name "Emulator Launcher" launcher.py --clean

Note that you have to change to the directory with the python file in PowerShell using EX: cd "C:\\Users\\your\_username\\OneDrive\_(if\_you\_use\_it)\\Documents\\Python Launcher - Github Repo "

The launcher will create launcher\_config.json automatically when you add programs.

