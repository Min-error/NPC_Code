# NPC_Code Toolset Overview

The files under this directory are used to process the input and output data of SimpleSSD, covering trace analysis, wear simulation, read retry statistics, data format conversion, NPC (Noise-Perturbation-Compensation) processing, and more.

---

## Directory Structure Overview

```
chips/
├── impact of cell/
│   └──get_all_info.py             # Post-NPC data processing (multiple methods)
└── impact of cell/
    ├── analysis_trace_info.py          # Basic trace info extraction
    ├── analysis_trace_info1.py         # Basic trace info extraction
    ├── block_retrntiontime_get.py     # Block wear/retention time simulation
    ├── get_readretry_num.py            # Read Retry count statistics
    ├── compare_retrytime.py            # Read Retry time comparison analysis
    └── msr_workload2trace.cpp          # MSR workload → trace format conversion
cpp/
└──impact of cell/
    ├── chip_base_info.cpp              # Chip basic data
    ├── get_cell_vth_base_info_and_fun_combined_update.cpp.cpp  # Some required basic functions
    ├── get_cell_vth_base_info_and_fun_update.cpp.cpp           # Some required basic functions
    ├── get_cell_vth_nnew_combined_read_retry_below.cpp         # Core NPC processor
    └── get_cell_vth_update_combined.cpp                        # Auxiliary program for core NPC processing
```

---

## 1. Trace Analysis & Preprocessing

### 1. `msr_workload2trace.cpp`

- **Purpose**: Converts raw Microsoft Research (MSR) workload data into the trace format recognized by SimpleSSD.
- **Input**: Raw MSR workload files.
- **Output**: Trace files in `.revised` format compliant with SimpleSSD input specifications.

---

### 2. `analysis_trace_info.py` / `analysis_trace_info1.py`

- **Purpose**: Reads the most basic information from trace files (e.g., number of requests, read/write ratio, LBA distribution, request size distribution, etc.).
- **Input**: Original trace files (e.g., `test1.revised`).
- **Output**: Basic statistics printed to the terminal.
- **Use case**: Quickly understand the overall characteristics of a trace.

---

## 2. SSD Runtime Data Extraction & Simulation

### 3. `block_retrntiontime_get.py`

- **Purpose**: Simulates the wear condition of different blocks during normal SSD usage, generating retention time assignments for each block.
- **Output**: `block_rt_assignment.csv` – records the retention time assignment per block.
- **Use case**: Provides retention time input for subsequent read retry analysis.

> Output file: `block_rt_assignment.csv`

---

### 4. `get_readretry_num.py`

- **Purpose**: Extracts read retry related data from simulation outputs, counting how many times each read operation triggers a retry.
- **Input**: SimpleSSD simulation logs or output files.
- **Output**: Statistics of read retry counts.

---

### 5. `compare_retrytime.py`

- **Purpose**: Performs comparative analysis on read retry time data under different conditions (e.g., varying wear levels, temperatures, retention times).
- **Input**: Multiple sets of read retry data files.
- **Output**: Comparative analysis results.

---

## 3. NPC Processing

### 6. `impact of cell/cpp/get_cell_vth_nnew_combined_read_retry_below.cpp`

> ⭐ **Core file** – The most critical program in the entire NPC processing flow.

- **Purpose**: Executes NPC model processing on raw chip scan data, simulating the corresponding processing pipeline.
- **Input**: Raw voltage data (Vth distribution) after chip scanning.
- **Output**:
  - **Error data**: BER/error rate information after NPC model processing.
  - **Read Vth data**: Corresponding voltage threshold offset.
  - **Read Retry data**: Number of read retries.
- **Note**: Different outputs can be obtained by modifying certain parameters in this file.

---

### 7. `impact of cell/get_all_info.py`

- **Purpose**: Processes the output data from the NPC model. It contains multiple data processing schemes (e.g., statistics at different granularities, visualization, filtering conditions, etc.).
- **Input**: Error and read Vth data after NPC processing.
- **Output**: Multi-dimensional analysis results (depending on the scheme selected within the script).
- **Use case**: Secondary analysis of NPC outputs to extract meaningful features for upper-level simulations or paper plotting.

---

## License

This toolset is intended for research and educational purposes only.
