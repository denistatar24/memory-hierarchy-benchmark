# Memory Hierarchy Benchmark

## Overview
This is a project I built to visualize the performance differences in computer memory levels (**Cache**, **RAM**, and **Disk**).

I wrote the benchmarking engine in **C** to get accurate low-level access speeds (using pointers and matrix operations), and I created a **Python GUI** to control the tests and plot the bandwidth results in real-time.

## Project Structure
* `main.c` - The C source code that performs the memory read/write operations.
* `start.py` - The Python dashboard for monitoring system resources and viewing graphs.
* `rezultate.csv` - Automatically generated file storing the benchmark data.

## How to Run

### 1. Compile the C backend
The Python script needs the compiled C executable to run the tests. Since I used Windows timers, use GCC (MinGW) to compile it:

gcc main.c -o bin/Debug/proiect.exe

(Note: The Python script expects the executable to be in `bin/Debug/`. If you compile it to a different name or location, you just need to update the path inside `start.py`)

### 2. Install Python libraries
You need a few libraries for the GUI and the charts:

pip install matplotlib pandas psutil py-cpuinfo

### 3. Start the application
Run the Python script to open the dashboard:

python start.py

## Technologies Used
* **C** (for raw performance and memory management)
* **Python** (Tkinter for GUI, Matplotlib for graphing)
* **OS**: Windows (uses specific API for high-precision timing)