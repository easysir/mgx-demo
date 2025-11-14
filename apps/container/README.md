# Container App

该应用集中管理沙箱容器的生命周期、文件系统、命令执行与 GC 逻辑，供 `apps/backend` 或其他服务通过 `container_app` 包复用。

## 目录结构

```
apps/container/
  container_app/            # Python package
    services/
      container.py          # Docker 容器管理与配置
      filesystem.py         # 沙箱文件读写能力
      sandbox_exec.py       # 容器内命令执行
      sandbox_gc.py         # 空闲回收协程
  .env                      # 沙箱默认配置
```

## 用法

后端代码可通过 `from container_app import container_manager` 等导出对象直接使用；也可以按需实例化 `ContainerManager` / `FileService` 等类，并将 `apps/container/.env` 作为默认配置（优先级：本地 `.env` > 环境变量 > 代码默认值）。
