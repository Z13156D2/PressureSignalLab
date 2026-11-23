# Data files / 数据文件

`samples/` contains the six original workbooks, preserved byte for byte. Filenames describe their observed contents; their experimental provenance has not been established. / `samples/` 保留原始六个表格，内容未改写；新名称依据可观察内容命名，不推断实验来源。

| Current file / 当前文件 | Original / 原文件 | Contents / 内容 |
| --- | --- | --- |
| `samples/voltage_baseline.xlsx` | `112.xlsx` | One sheet, 60 rows of data, 3 columns; baseline voltage series. / 单表，60 条数据，3 列。 |
| `samples/voltage_series_02.xlsx` | `2.xlsx` | One sheet, 60 data rows, 3 columns. / 单表，60 条数据，3 列。 |
| `samples/voltage_series_03.xlsx` | `3.xlsx` | One sheet, 60 data rows, 3 columns. / 单表，60 条数据，3 列。 |
| `samples/pressure_voltage_corrected.xlsx` | `pressure_600_700_800hPa_0p4Pa_step_voltage_corrected.xlsx` | Sheets `600hPa`, `700hPa`, `800hPa`; each has 60 data rows and 3 columns. Default Qt input; only the first sheet is currently loaded. / 三个工作表，Qt 默认只读取首表。 |
| `samples/pressure_voltage_corrected_variant.xlsx` | `pressure_600_700_800hPa_0p4Pa_step_voltage_corrected_1.xlsx` | Three corresponding sheets; original variant retained separately. / 对应的另一版本，独立保留。 |
| `samples/sensor_recording_001.xlsx` | `sensor_data_001.xlsx` | One sheet, 109 data rows and 2 columns. / 单表，109 条数据，2 列。 |

Counts exclude the header. Some original headers contain encoding artifacts and remain unchanged. The Qt dashboard reads columns by position, using the third column as voltage and generating a 0.1-second time axis instead of preserving the workbook's time values. / 行数不含表头；部分原始表头存在乱码，保持原样。Qt 程序按位置取第三列电压，并生成间隔 0.1 秒的时间轴。

`exports/` is for newly generated measurements. Its contents are ignored by Git, except for `.gitkeep`. Keep the sample workbooks as inputs and export new recordings separately. / `exports/` 用于新导出数据，除 `.gitkeep` 外均被 Git 忽略；请将输入样例与新采集数据分开保存。
