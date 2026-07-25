# Artifact Requirements

## Supported Environment


| Component | Reference version |
| --- | --- |
| Operating system | Windows 10/11 x86-64 |
| C++ compiler | MinGW-w64 GCC 8.1.0, POSIX threads, SEH |
| C++ language mode | C++17 |
| Python | CPython 3.12.13, 64-bit |
| NumPy | 2.3.5 |
| pandas | 3.0.1 |
| SciPy | 1.18.0 |
| PowerShell | Windows PowerShell 5.1 or PowerShell 7 |

The checked-in legacy executable identifies itself as MinGW-w64 GCC 8.1.0
with the POSIX threading model. Rebuilding from the documented source is
recommended.

## Hardware

### Replay and Analysis

- x86-64 CPU with at least 8 logical cores; 16 or more are recommended.
- 48 GiB RAM minimum; 64 GiB or more is recommended.
- Approximately 700 GiB free storage for both complete voltage-sweep
  datasets. A 1 TiB SSD is recommended for the data and generated outputs.
- An SSD is strongly recommended because each condition reads 127 large
  binary files.

The largest C++ allocation is the in-memory voltage sweep. It is approximately
24.56 GiB for `3DV7` and 24.19 GiB for `X3_9070`, before source states,
transition matrices, process overhead, and operating-system memory.

Approximate readout storage:

| Chip | One voltage file | One block-retention condition | All 32 conditions |
| --- | ---: | ---: | ---: |
| `3DV7` | 0.073 GiB | 9.21 GiB | 294.7 GiB |
| `X3_9070` | 0.072 GiB | 9.10 GiB | 291.3 GiB |

Only one block-retention condition is loaded at a time. Running two complete
instances concurrently roughly doubles the memory requirement.

### Regenerating the Measurements

Replay does not require NAND hardware. Regenerating the omitted raw data does
require the original or equivalent:

- Commercial TLC 3D NAND devices matching the evaluated chips.
- A programmable NAND characterization/test platform capable of raw page
  reads and read-reference offsets from -63 through +63.
- P/E cycling support through 6,000 cycles.
- Temperature-controlled accelerated-retention equipment.
- Controller or firmware access for reading LSB, CSB, and MSB pages without
  hiding raw errors behind ECC.

This is non-commodity laboratory equipment. A substitute platform must
preserve page layout, voltage-step definition, data pattern, P/E procedure,
and retention-equivalence procedure; otherwise the resulting dataset is a
replication on different hardware rather than an exact reproduction.

## C++ Build Dependencies

Install a 64-bit MinGW-w64 distribution with:

- `g++`
- C++17 standard library
- POSIX pthread support
- `unistd.h`, `pthread.h`, and the standard Windows C runtime headers

Build from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_npc.ps1
```

Or compile directly:

```powershell
g++ -std=c++17 -O2 -pthread `
  .\cpp\impact_of_cell\get_cell_vth_nnew_combined_read_retry_below.cpp `
  -o .\cpp\impact_of_cell\get_cell_vth_nnew_combined_read_retry_below.exe
```

If a dynamically linked MinGW build is distributed, also provide compatible
copies of `libgcc_s_seh-1.dll`, `libstdc++-6.dll`, and
`libwinpthread-1.dll`, or ensure they are on `PATH`. The build helper accepts
`-StaticRuntime` to link the GCC and C++ runtimes statically:

```powershell
.\build_npc.ps1 -StaticRuntime
```

## Python Environment

Create a clean 64-bit environment and install the pinned packages:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`chips/impact_of_cell/get_all_info.py` requires pandas. The SimpleSSD helper
scripts additionally use NumPy and SciPy. `D:\NPC\DRRM\drrm_batch.py` uses
only the Python standard library.


## Storage and Archive Integrity

The code-only repository is small. The complete measurement archive is
approximately 586 GiB before metadata and generated outputs, so reserve at
least 700 GiB free space.

For a data release, provide:

- A machine-readable list of every file and its byte size.
- SHA-256 checksums.
- The chip, block, P/E count, retention age, and voltage offset represented
  by each path.
- Compression and extraction instructions.
- A statement of data redistribution rights.

Run the executable with `--validate-only` after extraction and before a full
replay.

## Known Environment Deviations

- The raw dataset and group-voltage pre-characterization tables are not in
  the current code-only package because of their size.
- The current workspace does not contain a C++ compiler, so the cleaned C++
  source was not rebuilt in that workspace. Rebuild it in the reference
  MinGW-w64 environment before submission.
- SciPy was not installed in the current workspace.