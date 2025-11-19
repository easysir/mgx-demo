from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from .container import ContainerManager, container_manager


class FileAccessError(RuntimeError):
    """Raised when sandbox files cannot be accessed."""


class FileValidationError(FileAccessError):
    """Raised when written file does not pass validation."""


class FileValidator:
    """一个可选的钩子，用于在写入后校验文件内容。"""

    def validate(self, path: Path, content: str) -> None:
        pass


class DefaultFileValidator(FileValidator):
    JSON_EXTS = {".json", ".jsonc"}

    def validate(self, path: Path, content: str) -> None:
        suffix = path.suffix.lower()
        if suffix in self.JSON_EXTS:
            try:
                json.loads(content)
            except json.JSONDecodeError as exc:
                raise FileValidationError(f"{path} 不是合法 JSON: {exc}") from exc


@dataclass(slots=True)
class FileServiceConfig:
    project_root: Path = Path(os.getenv("SANDBOX_PROJECT_ROOT", "."))
    max_entries: int = int(os.getenv("SANDBOX_FILE_LIMIT", "2000"))
    max_depth: int = int(os.getenv("SANDBOX_TREE_DEPTH", "4"))


class FileService:
    def __init__(
        self,
        manager: ContainerManager,
        config: Optional[FileServiceConfig] = None,
        validator: Optional[FileValidator] = None,
    ) -> None:
        # 注入容器管理器、配置以及可选的内容校验器
        self.manager = manager
        self.config = config or FileServiceConfig()
        self.validator = validator or DefaultFileValidator()

    def _resolve_base(self, *, session_id: str, owner_id: str) -> Path:
        """定位当前会话对应容器的工作目录，并保证目录存在。"""
        instance = self.manager.ensure_session_container(session_id=session_id, owner_id=owner_id)
        base_path = (instance.workspace_path / self.config.project_root).resolve()
        if not base_path.exists():
            base_path.mkdir(parents=True, exist_ok=True)
        return base_path

    def _resolve_path(self, *, session_id: str, owner_id: str, relative_path: str) -> Path:
        """把用户输入的相对路径转换为沙箱内安全的绝对路径。"""
        base_path = self._resolve_base(session_id=session_id, owner_id=owner_id)
        candidate = (base_path / relative_path.lstrip("/")) if relative_path else base_path
        resolved = candidate.resolve()
        if base_path not in resolved.parents and resolved != base_path:
            raise FileAccessError("路径越界: 仅允许访问沙箱工作目录内的文件")
        return resolved

    def list_tree(
        self,
        *,
        session_id: str,
        owner_id: str,
        root: str = "",
        depth: int = 4,
        include_hidden: bool = False,
    ) -> list[dict]:
        """列出指定目录的文件树，受最大深度与条数限制。"""
        if depth <= 0:
            raise FileAccessError("深度必须大于 0")
        depth = min(depth, self.config.max_depth)
        project_root = self._resolve_base(session_id=session_id, owner_id=owner_id)
        base = self._resolve_path(session_id=session_id, owner_id=owner_id, relative_path=root)

        entries: list[dict] = []
        total_entries = 0

        def rel(entry_path: Path) -> str:
            rel_path = entry_path.relative_to(project_root)
            rel_str = str(rel_path)
            return '' if rel_str == '.' else rel_str

        def walk(path: Path, current_depth: int) -> list[dict]:
            # DFS 遍历文件树，统计条目并生成结构化描述
            nonlocal total_entries
            if current_depth > depth:
                return []
            children: list[dict] = []
            try:
                items: Iterable[os.DirEntry[str]] = os.scandir(path)
            except FileNotFoundError:
                return []
            for entry in sorted(items, key=lambda d: d.name):
                if not include_hidden and entry.name.startswith('.'):  # skip hidden
                    continue
                total_entries += 1
                if total_entries > self.config.max_entries:
                    raise FileAccessError("目录过大，已超过展示上限")
                entry_path = Path(entry.path)
                stat = entry.stat(follow_symlinks=False)
                node = {
                    "name": entry.name,
                    "path": rel(entry_path),
                    "type": "directory" if entry.is_dir(follow_symlinks=False) else "file",
                    "size": stat.st_size,
                }
                if entry.is_dir(follow_symlinks=False):
                    node["children"] = walk(entry_path, current_depth + 1)
                children.append(node)
            return children

        if base.is_file():
            file_stat = base.stat()
            entries.append(
                {
                    "name": base.name,
                    "path": rel(base),
                    "type": "file",
                    "size": file_stat.st_size,
                }
            )
        else:
            entries = walk(base, 1)
        return entries

    def read_file(self, *, session_id: str, owner_id: str, path: str) -> dict:
        target = self._resolve_path(session_id=session_id, owner_id=owner_id, relative_path=path)
        if not target.exists() or not target.is_file():
            raise FileAccessError("文件不存在")
        content = target.read_text(encoding="utf-8", errors="ignore")
        stat = target.stat()
        return {
            "name": target.name,
            "path": path,
            "size": stat.st_size,
            "modified_at": stat.st_mtime,
            "content": content,
        }

    def write_file(
        self,
        *,
        session_id: str,
        owner_id: str,
        path: str,
        content: str,
        encoding: str = "utf-8",
        overwrite: bool = True,
        append: bool = False,
    ) -> dict:
        """写入/追加文件，写后可触发自定义校验，失败则回滚。"""
        path = path.strip()
        if not path or path.endswith("/"):
            raise FileAccessError("请提供有效的文件路径，不能是目录")
        target = self._resolve_path(session_id=session_id, owner_id=owner_id, relative_path=path)
        existed = target.exists()
        if existed and target.is_dir():
            raise FileAccessError("目标路径是目录，无法写入文件")
        if existed and not overwrite and not append:
            raise FileAccessError("文件已存在，如需覆盖请设置 overwrite=True")
        encoding = encoding or "utf-8"
        target.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with target.open(mode, encoding=encoding) as handler:
            handler.write(content)
        previous_content: str | None = None
        if existed:
            previous_content = target.read_text(encoding=encoding, errors="ignore")
        stat = None
        project_root = self._resolve_base(session_id=session_id, owner_id=owner_id)
        rel_path = str(target.relative_to(project_root))
        if rel_path == ".":
            rel_path = target.name
        stat = target.stat()
        if self.validator:
            try:
                # 校验写入结果，若失败则根据 previous_content 做回滚
                validated_content = target.read_text(encoding="utf-8", errors="ignore")
                self.validator.validate(target, validated_content)
            except FileValidationError as exc:
                if previous_content is None:
                    try:
                        target.unlink()
                    except FileNotFoundError:
                        pass
                else:
                    with target.open("w", encoding="utf-8") as handler:
                        handler.write(previous_content)
                raise FileAccessError(str(exc)) from exc

        return {
            "name": target.name,
            "path": rel_path,
            "size": stat.st_size,
            "modified_at": stat.st_mtime,
            "created": not existed,
        }


file_service = FileService(container_manager)
