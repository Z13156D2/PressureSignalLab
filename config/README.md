# Configuration / 配置

Each application reads its own `<module_name>.local.json`, or `<module_name>.example.json` when the local file does not exist. Example values are taken from that application's original defaults. / 各程序读取自身的本机配置，缺失时读取示例配置；示例值来自对应程序原有默认值。

For example / 例如：

```powershell
Copy-Item config/pressure_serial.example.json config/pressure_serial.local.json
```

Edit the local file before launching. Applications that implement saving write their local file here. Restart after editing serial parameters. Pressure demo thresholds use **hPa**; serial and environmental thresholds use **Pa**. / 编辑本机文件后启动；支持保存设置的程序会将修改写入本机文件。手动更改串口参数后请重启程序。气压模拟阈值单位为 **hPa**，串口与环境程序使用 **Pa**。

`original_settings.reference.json` and `color_scheme.reference.json` are historical references, not active configuration inputs. / 这两个 reference 文件为历史参考，不会作为当前配置自动加载。
