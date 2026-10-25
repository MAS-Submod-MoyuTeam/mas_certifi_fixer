# CertifiFixer

CertifiFixer 是 [Monika After Story](https://github.com/Monika-After-Story/MonikaModDev) 的 submod，用于修复 MAS 无法导入 `certifi` 包的情况。

## 安装

1. 从 [Releases](https://github.com/MAS-Submod-MoyuTeam/mas_certifi_fixer/releases) 下载最新的 `CertifiFixer-<版本>.zip`。
2. 将 ZIP 解压到 MAS 安装目录，使文件位于 `game/Submods/CertifiFixer/` 下。
3. 启动游戏。submod 会在 MAS 检查 `certifi` 导入之前先检查并修复明显损坏的文件；无需为此额外重启。

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

启动早期，submod 会检查 `certifi` 必需文件是否存在、Python 模块语法与 `where`、`has_cert`、`set_parent_dir`、`check_update` 接口，以及证书文件的 PEM 标记。发现问题时，会在 MAS 首次导入检查前将随包文件覆盖到 `game/python-packages/certifi/`。若静态检查通过但 MAS 导入仍失败，submod 会覆盖文件并在本次启动中重新检查导入。正常导入时不会修改文件；有效但内容不同的证书也不会仅因版本不同而被覆盖。覆盖前不会备份原文件，源文件缺失或复制失败会写入游戏日志。

卸载 submod 时可以删除 `game/Submods/CertifiFixer/`，但已覆盖的 `python-packages/certifi/` 文件不会自动恢复。

## 发布

推送到 `main` 或手动运行 GitHub Actions 的 `Release` workflow 时，流程会从 `certifi_fixer.rpy` 读取版本号，打包 `game/Submods/CertifiFixer/`，并在同版本 Release 尚不存在时发布 ZIP。

## 证书更新

`Update CA certificates` workflow 每天 UTC 03:17（北京时间 11:17）从 [certifi/python-certifi](https://github.com/certifi/python-certifi) 获取最新的 `cacert.pem`，与仓库中的文件逐字节比较：

- 相同：不产生提交，直接结束。
- 不同：覆盖 `game/Submods/CertifiFixer/certifi/cacert.pem`，将 `certifi_fixer.rpy` 中 `version` 的补丁号加一，提交并推送到 `main`，随后由 `Release` workflow 自动发布新版本。

也可以手动触发（`workflow_dispatch`），或在本地运行 `python .github/scripts/update_cacert.py`（需要 Python 3.8+ 与网络访问）。脚本会校验下载内容是完整的 PEM 证书包，并在下载失败或本地版本号格式不符合预期时以非零状态退出。
