# NPC Artifact

This artifact contains the evaluation code for **NPC: Neighbor Position
Co-Aware Read Voltage Calibration for Reliable 3D NAND Flash**. It replays
measured TLC NAND readouts, groups cells using vertical-neighbor states,
applies group-specific read-voltage offsets, and reports per-wordline (WL)
voltage settings, raw bit errors, page errors, and read-retry counts.

The repository also contains scripts for aggregating two-block measurements
and for reproducing the DRRM baseline. The raw NAND measurements are not
included in the current package because they are several hundred GiB.

## Artifact Scope

The primary executable is:

`cpp/impact_of_cell/get_cell_vth_nnew_combined_read_retry_below.cpp`

It processes both chips, all four P/E-cycle points, both blocks at each P/E
point, and all four retention ages in one run.

| Chip label | P/E cycles and block IDs                                     | Retention ages  |
| ---------- | ------------------------------------------------------------ | --------------- |
| `3DV7`     | 3000: 75, 76; 4000: 78, 82; 5000: 77, 79; 6000: 86, 87       | 1m, 3m, 6m, 12m |
| `X3_9070`  | 3000: 725, 729; 4000: 732, 733; 5000: 741, 745; 6000: 748, 749 | 1m, 3m, 6m, 12m |

The primary program evaluates the NARR-oriented `a1b8` configuration:
the above-neighbor states are merged into one class and the below-neighbor
states form eight classes. This produces eight cell groups. The paper's
general NPC evaluation uses the `a2b4` configuration, also totaling eight
groups. The older `get_cell_vth_update_combined.cpp` source retains that
configuration, but it is not the primary automated entry point documented
here.

The following parts are not included in this code-only release:

- Raw NAND source and voltage-sweep readout files.
- The flash test-board firmware and commands used to acquire those files.
- The pre-characterization program that generated
  `GP0_WL_offset.csv` through `GP7_WL_offset.csv`.
- Figure-rendering scripts. This artifact produces the CSV data used for
  analysis; plotting is a separate presentation step.

Consequently, the code can be built and its input layout can be validated
without the dataset, but numerical paper results require the archived
measurements and pre-characterized voltage tables.

## Repository Layout

```text
NPC_Code-main/
|-- README.md
|-- REQUIREMENTS
|-- REQUIREMENTS.md
|-- requirements.txt
|-- build_npc.ps1
|-- examples/
|   |-- sample_wl_errors.csv
|   `-- small_error_example.py
|-- cpp/impact_of_cell/
|   |-- get_cell_vth_nnew_combined_read_retry_below.cpp
|   |-- get_cell_vth_base_info_and_fun_combined_update.cpp
|   |-- get_cell_vth_base_info_and_fun_update.cpp
|   `-- chip_base_info.cpp
`-- chips/
    |-- impact_of_cell/get_all_info.py
    `-- simplessd/
```

The C++ files use the original single-translation-unit organization: the
primary source directly includes the three helper `.cpp` files. Compile only
the primary source; compiling every `.cpp` file together would create
duplicate definitions.

## Trace Analysis & Preprocessing

### `msr_workload2trace.cpp`

- **Purpose**: Converts raw Microsoft Research (MSR) workload data into the trace format recognized by SimpleSSD.
- **Input**: Raw MSR workload files.
- **Output**: Trace files in `.revised` format compliant with SimpleSSD input specifications.

---

### `analysis_trace_info.py` / `analysis_trace_info1.py`

- **Purpose**: Reads the most basic information from trace files (e.g., number of requests, read/write ratio, LBA distribution, request size distribution, etc.).
- **Input**: Original trace files (e.g., `test1.revised`).
- **Output**: Basic statistics printed to the terminal.
- **Use case**: Quickly understand the overall characteristics of a trace.

---

## SimpleSSD Runtime Data Extraction & Simulation

### `block_retrntiontime_get.py`

- **Purpose**: Simulates the wear condition of different blocks during normal SSD usage, generating retention time assignments for each block.
- **Output**: `block_rt_assignment.csv` – records the retention time assignment per block.
- **Use case**: Provides retention time input for subsequent read retry analysis.

> Output file: `block_rt_assignment.csv`

---

### `get_readretry_num.py`

- **Purpose**: Extracts read retry related data from simulation outputs, counting how many times each read operation triggers a retry.
- **Input**: NPC simulation output files.
- **Output**: Statistics of read retry counts.

---

### `compare_retrytime.py`

- **Purpose**: Performs comparative analysis on read retry time data under different conditions (e.g., varying wear levels, temperatures, retention times).
- **Input**: Multiple sets of read retry data files.
- **Output**: Comparative analysis results.

---

## NPC Processing

### `get_cell_vth_nnew_combined_read_retry_below.cpp`

> ⭐ **Core file** – The most critical program in the entire NPC processing flow.

- **Purpose**: Executes NPC model processing on raw chip scan data, simulating the corresponding processing pipeline.
- **Input**: Raw voltage data (Vth distribution) after chip scanning.
- **Output**:
  - **Error data**: BER/error rate information after NPC model processing.
  - **Read Vth data**: Corresponding voltage threshold offset.
  - **Read Retry data**: Number of read retries.
- **Function**:
    `read_file()` decodes each TLC cell from its LSB, CSB, and MSB bits.
    `get_wl_cell_num()` builds source-to-read state-transition counts for
       every voltage offset and neighbor-state group.
    `get_trans_cell_vthlist_and_avg()` converts transition changes into
       smoothed threshold-voltage distributions.
    `get_default_vth_list_and_error_each_wl()` finds the per-WL optimum over
       offsets -20 through +15 and also evaluates the default offset 0.
    `get_gp_best_vth_list_and_error_each_wl_best_retry()` applies the
       pre-characterized group-specific offsets when the page RBER exceeds the
       configured ECC threshold.
    `update_cell_info()` updates the current states before processing the next
       WL, enabling below-neighbor reuse for sequential NARR processing.
    `out_all_data()` writes voltage, error, and retry CSV files.

- **Note**: Different outputs can be obtained by modifying certain parameters in this file.
---

### `get_all_info.py`

- **Purpose**: Processes the output data from the NPC model. It contains multiple data processing schemes (e.g., statistics at different granularities, visualization, filtering conditions, etc.).
- **Input**: Error and read Vth data after NPC processing.
- **Output**: Multi-dimensional analysis results (depending on the scheme selected within the script).
- **Use case**: Secondary analysis of NPC outputs to extract meaningful features for upper-level simulations or paper plotting.

---

## Data Provenance and Status

The measurements were produced from two commercial TLC 3D NAND devices.
Each condition contains two independently measured blocks. Devices were
cycled to 3,000, 4,000, 5,000, and 6,000 P/E cycles. Retention conditions
represent 1, 3, 6, and 12 months at 40 degrees Celsius using accelerated
high-temperature retention tests as described in the paper.

These are device-level electrical measurements. They contain no human
subjects, personal information, or user content. The code license does not
grant permission to redistribute vendor-confidential traces, test-board
firmware, or other third-party material. Before releasing the dataset,
confirm the device-data redistribution rights, remove proprietary test
metadata, and publish a checksum manifest and acquisition protocol.

## Input Data Layout

The executable accepts three configurable roots:

```text
<source-root>/
|-- 3DV7_random
`-- X3_9070_random

<readout-root>/
|-- 3DV7/SourceFile/<block>_<retention>/{-63,...,0,...,63}
`-- X3_9070/SourceFile/<block>_<retention>/{-63,...,0,...,63}

<output-root>/
|-- 3DV7_2d/<block>_<retention>_2d_best_Output/
|   `-- down/WLReadVth_gauss_single1/GP{0,...,7}_WL_offset.csv
|-- X3_9070_2d/<block>_<retention>_2d_best_Output/
|   `-- down/WLReadVth_gauss_single1/GP{0,...,7}_WL_offset.csv
|-- 3DV7/
`-- X3_9070/
```

`<retention>` is one of `1m`, `3m`, `6m`, or `12m`. Voltage-sweep files have
integer names with no extension and cover every offset from `-63` to `63`.

### Binary Format

Both ground-truth and voltage-sweep files use WL-major binary storage:

```text
WL0 LSB page
WL0 CSB page
WL0 MSB page
WL1 LSB page
...
```

Bits are decoded from bit 7 to bit 0. A cell's integer state is
`LSB_bit * 4 + CSB_bit * 2 + MSB_bit`.

| Chip      | WL count | Bytes stored per page | Valid bytes evaluated per page |
| --------- | -------: | --------------------: | -----------------------------: |
| `3DV7`    |    1,408 |                18,432 |                         18,432 |
| `X3_9070` |    1,392 |                18,432 |                         18,368 |

For `X3_9070`, the final 64 stored bytes of each page are not included in the
error denominator or cell evaluation.

Each `GP*_WL_offset.csv` must contain one row per WL and seven numeric read
offsets in `R0` through `R6` order. The current parser ignores nonnumeric
header fields. Do not include an additional numeric WL-index column in these
files because it would be interpreted as `R0`.

## Installation

See `REQUIREMENTS.md` for the tested compiler, Python environment, hardware,
storage, VM, and NAND acquisition requirements.

Create the Python environment from the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Build the C++ program:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_npc.ps1
```

Equivalent direct command:

```powershell
g++ -std=c++17 -O2 -pthread `
  .\cpp\impact_of_cell\get_cell_vth_nnew_combined_read_retry_below.cpp `
  -o .\cpp\impact_of_cell\get_cell_vth_nnew_combined_read_retry_below.exe
```

The checked-in executable predates the command-line cleanup. Rebuild from
source before using the options below.

## Small Example and Input Check

Run the bundled one-WL example to verify the transition-error, page-error,
and chip-specific RBER calculations without the large NAND dataset:

```powershell
.\.venv\Scripts\python.exe .\examples\small_error_example.py
```

Expected output:

```text
Boundary errors: {'R0': 12, 'R1': 8, 'R2': 8, 'R3': 8, 'R4': 8, 'R5': 4, 'R6': 10}
Page errors: {'LSB': 20, 'CSB': 20, 'MSB': 18}
WL total error: 58
3DV7 WL RBER: 0.000393337674
X3_9070 WL RBER: 0.000394708188
```

The C++ code-only smoke test prints the available options and does not
require the NAND dataset:

```powershell
.\cpp\impact_of_cell\get_cell_vth_nnew_combined_read_retry_below.exe --help
```

After mounting or copying the dataset, validate its layout without loading
the large arrays:

```powershell
.\cpp\impact_of_cell\get_cell_vth_nnew_combined_read_retry_below.exe `
  --source-root D:\NPC\data\source `
  --readout-root D:\NPC\data\readouts `
  --output-root D:\NPC\data\npc-work `
  --validate-only
```

A complete archive reports `4321/4321 required files valid` for each chip:
one source file plus 32 block-retention conditions, each with 127 readout
files and eight group-voltage tables. Binary byte sizes are checked as well.
Exit code 2 indicates missing or size-mismatched inputs; the program prints
up to twelve examples.

## Reproducing NPC Results

1. Install the environment and rebuild the executable.
2. Restore the source binaries, voltage-sweep readouts, and group-voltage
   tables using the exact layout above.
3. Run `--validate-only` and require a complete result for both chips.
4. Run the full replay:

```powershell
.\cpp\impact_of_cell\get_cell_vth_nnew_combined_read_retry_below.exe `
  --source-root D:\NPC\data\source `
  --readout-root D:\NPC\data\readouts `
  --output-root D:\NPC\data\npc-work
```

With no arguments, the historical roots are preserved:

```text
source:  E:/disk/result/Union/data
readout: F:/ATC_NVMSA/atc
output:  D:/disk/result/ATC
```

The program processes one block-retention condition at a time. Do not launch
multiple full instances unless the host has enough memory for every process.

### Per-Condition Outputs

Results are written under:

```text
<output-root>/<chip>/<block>_<retention>_2d_Output_retry_down_more_best/
  up1_combined_down8/Result/
```

Important files are:

| File                                                    | Meaning                                                      |
| ------------------------------------------------------- | ------------------------------------------------------------ |
| `GP0_best_vth_offset.csv` ... `GP7_best_vth_offset.csv` | Seven applied read offsets for each neighbor-state group and WL |
| `GP0_best_vth_error.csv` ... `GP7_best_vth_error.csv`   | Boundary, page, and total errors for each group              |
| `GP_best_vth_error.csv`                                 | Group-aware aggregate error for each WL                      |
| `default_vth_offset.csv`                                | Default offset, normally zero                                |
| `default_vth_error.csv`                                 | Error at the default offsets                                 |
| `best_vth_offset.csv`                                   | Individually optimized WL-level offsets                      |
| `best_vth_error.csv`                                    | Error at the individually optimized WL-level offsets         |
| `default_retry_vth_offset.csv`                          | WL-level retry offsets                                       |
| `default_retry_vth_error.csv`                           | WL-level retry errors                                        |
| `GP_retry_num.csv`                                      | Group-aware retry counts and failure flags                   |
| `defalut_retry_num.csv`                                 | WL-level retry counts; the historical filename typo is retained for compatibility |

Error CSV columns are `R0` through `R6`, `LSB`, `CSB`, `MSB`, and `error`.
Offset CSV columns are `R0` through `R6`. Rows are indexed by WL.

### Paper Result Map

| Paper result                                         | Artifact data path                                           | Reproduction status                                          |
| ---------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| Figure 10, grouping comparison                       | Sum the `error` column in `GP_best_vth_error.csv` for every tested `aibj` build | Partially covered. The primary build is `a1b8`; the legacy source is `a2b4`. Other grouping builds and their raw data are not included. |
| Figure 11, per-WL RBER                               | Two-block strategy averages divided by the chip-specific RBER denominator | Partially supported. `get_all_info.py` aggregates the three fixed legacy trees; the practical NPC/NARR result must be merged from the primary output. |
| Figure 12, P/E and retention sweeps                  | `all_wl_error_together_rate_order_pe.csv` and `all_wl_error_together_rate_order_time.csv` | Partially supported by `get_all_info.py`; DRRM baseline generation is documented in the final section. |
| Figures 13 and 14, endurance and retention extension | Extrapolation from the RBER sweep to the ECC threshold       | The underlying RBER CSVs are produced, but the extrapolation/plotting script is not included. |
| Figure 15, average read retry                        | `GP_retry_num.csv`, `defalut_retry_num.csv`, and `chips/simplessd/get_readretry_num.py` | Retry CSV generation is supported. The helper has legacy simulator paths that must be updated to the restored SimpleSSD traces. |
| Figure 16, read response time                        | SimpleSSD workload replay using the generated retry counts   | Not fully self-contained. The modified SimpleSSD simulator, workloads, and VM image must be distributed separately. |

For a paper-value reproduction claim, archive the exact input checksum
manifest, compiler version, command log, complete-condition manifest, and
final plotting/extrapolation scripts together with this repository.

### Aggregate Two Blocks

`chips/impact_of_cell/get_all_info.py` aggregates per-WL CSVs, averages the
two blocks for every P/E-retention condition, converts total errors to RBER,
and emits both P/E-major and retention-major tables.

It expects the legacy `a2b4` result layout under a common workspace:

```text
<workspace>/<chip>/<block>_<retention>m_3d_Output/
  up2_combined_down4/Result/best_vth_error.csv
<workspace>/<chip>/<block>_<retention>m_3d_wl_group_Output/
  up2_combined_down4/Result/GP_best_vth_error.csv
<workspace>/<chip>/<block>_<retention>m_3d_best_Output/
  up2_combined_down4/Result/GP_best_vth_error.csv
```

The fixed internal labels are:

- `not_group`: an independently optimized voltage for each WL.
- `wl_group`: a shared voltage within each WL cluster.
- `best`: the grouped neighbor-aware result.

These labels describe the stored result directories. Map them to paper
legend names according to the experiment configuration used to create the
directories; the aggregation script intentionally does not relabel them.

Run the complete aggregation and fail on missing or malformed inputs:

```powershell
.\.venv\Scripts\python.exe .\chips\impact_of_cell\get_all_info.py `
  --workspace D:\NPC `
  --chips 3DV7 X3_9070 `
  --retentions 1 3 6 12 `
  --error-types error `
  --strict
```

Without `--strict`, available conditions are processed and all missing or
invalid inputs are recorded in
`all_wl_error_input_manifest.csv`. Each complete condition must contain both
blocks. The aggregate output directory is
`<workspace>/<chip>/0all_result_need_more_default_line_gauss/`.

### Reproduction Checks

Before using generated values in a paper figure or table, verify:

- Every voltage-sweep file has exactly `WL_count * 3 * 18,432` bytes.
- Every source file has the same stored layout.
- Every voltage table has exactly 1,408 or 1,392 data rows as appropriate.
- Every result CSV has a complete zero-based WL index.
- Both blocks are present before calculating a condition mean.
- `3DV7` RBER uses `18,432 * 8`; `X3_9070` uses `18,368 * 8`.
- The grouping configuration and strategy label match the target figure.
- Published data archives include cryptographic checksums.

## DRRM Reproduction

The DRRM reproduction script is maintained in the sibling directory
`D:\NPC\DRRM\drrm_batch.py`. In a redistributed artifact, retain the same
relative layout:

```text
<workspace>/
|-- DRRM/drrm_batch.py
|-- 3DV7/
|-- 3DV7_best_vth_offset_and_error/
|-- X3_9070/
|-- X3_9070_best_vth_offset_and_error/
`-- NPC_Code/NPC_Code-main/
```

The script reads measured optimum WL voltages from:

```text
<chip>_best_vth_offset_and_error/
  <block>_<retention>/best_vth_offset.csv
```

It reads voltage-indexed transition errors from:

```text
<chip>/<block>_<retention>/WL<wl>.csv
```

The implemented DRRM procedure is:

1. Assume all seven read-voltage offsets are zero at 1 hour.
2. Fit each base voltage linearly against `log10(retention_hours)` through
   the 1-hour origin.
3. For 1-, 3-, and 6-month targets, use the measured 12-month condition as
   the second fit point. For the 12-month target, use the measured 6-month
   condition.
4. Compute the OVD table once from the 1-month measurements at the same P/E
   count. For each WL and boundary, OVD is the two-block mean deviation from
   the global condition mean.
5. Calculate `predicted voltage = fitted base voltage + OVD`, then round
   half away from zero to select an available integer voltage row.
6. Sum adjacent-state transition errors, calculate LSB/CSB/MSB and total
   errors, calculate RBER, and average the two blocks for each WL.

Run all DRRM jobs:

```powershell
Set-Location D:\NPC\DRRM
py -3.12 .\drrm_batch.py --workers 8
```

The script produces 16 final CSV files: both chips for the four-point
PE3000 retention sweep and the four-point 3-month P/E sweep. It deliberately
keeps only:

```text
DRRM/results/<sweep>/<chip>/<condition>/
  <chip>_<condition>_block_average_by_wl.csv
```

Each row contains predicted and rounded `R0` through `R6`, average boundary
errors, average page errors, average total WL errors, and average WL RBER.