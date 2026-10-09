# CertifiFixer

CertifiFixer 是 [Monika After Story](https://github.com/Monika-After-Story/MonikaModDev) 的 submod，用于修复 MAS 无法导入 `certifi` 包的情况。

## 安装

1. 从 [Releases](https://github.com/MAS-Submod-MoyuTeam/mas_certifi_fixer/releases) 下载最新的 `CertifiFixer-<版本>.zip`。
2. 将 ZIP 解压到 MAS 安装目录，使文件位于 `game/Submods/CertifiFixer/` 下。
3. 启动游戏。如果此前 `certifi` 导入失败，请在首次启动后重启游戏，让 MAS 重新检查导入状态。

安装后的目录应包含：

```text
game/
└── Submods/
    └── CertifiFixer/
        ├── certifi_fixer.rpy
        └── certifi/
            ├── __init__.py
            ├── core.py
            └── cacert.pem
```

## 工作方式

启动时，submod 调用 `store.mas_can_import.certifi()`。检查成功时不会修改文件；检查失败时，将随 submod 提供的 `certifi` 文件直接覆盖到 `game/python-packages/certifi/`。覆盖前不会备份原文件。若随包的源目录不存在，submod 会记录错误日志。

卸载 submod 时可以删除 `game/Submods/CertifiFixer/`，但已覆盖的 `python-packages/certifi/` 文件不会自动恢复。

## 发布

推送到 `main` 或手动运行 GitHub Actions 的 `Release` workflow 时，流程会从 `certifi_fixer.rpy` 读取版本号，打包 `game/Submods/CertifiFixer/`，并在同版本 Release 尚不存在时发布 ZIP。
