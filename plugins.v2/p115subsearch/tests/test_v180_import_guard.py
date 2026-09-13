# -*- coding: utf-8 -*-
"""
P115SubSearch 加载级守护测试（v1.8.0）

背景（血泪教训，来自同类插件 v1.5.13）：
    仅用「AST 抽取单个方法 + 假类 exec」的测试会绕过真实模块的 import，
    从而放行 import 期错误（典型：注解用了 ``Set[str]`` 却没
    ``from typing import Set``）。Python 3.12 类体内的函数注解会立即求值，
    缺导入在 import 期就抛 NameError → 插件不注册 → 前端显示「没装上」。

因此本测试做两件**加载级**校验：
    1. 全量静态扫描：任何出现在注解位置的 typing 名字都必须已导入；
    2. 全模块 compile()：语法层面零错误。

不使用 pytest（与项目既有脚本式测试一致），直接 python 执行。
"""
import ast
import pathlib
import sys
import types
import typing

PLUGIN = pathlib.Path(__file__).resolve().parent.parent

FAILURES = []


def check(name, cond, extra=""):
    if cond:
        print(f"[PASS] {name}")
    else:
        print(f"[FAIL] {name} {extra}")
        FAILURES.append(name)


TYPING_NAMES = {n for n in dir(typing) if n[:1].isupper()}


def py_files():
    for p in sorted(PLUGIN.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        yield p


# ================= 1. typing 名字已导入 =================


def scan_typing_imports():
    problems = []
    for p in py_files():
        src = p.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            problems.append(f"{p.relative_to(PLUGIN)}: 语法错误 {e}")
            continue

        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "typing":
                imported |= {a.name for a in node.names}
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name == "typing":
                        # import typing 后用 typing.X 访问，视为已导入
                        imported |= set(TYPING_NAMES)

        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in TYPING_NAMES:
                used.add(node.id)
            elif isinstance(node, ast.Attribute) and node.attr in TYPING_NAMES:
                # 形如 typing.Optional，import typing 时已覆盖
                if isinstance(node.value, ast.Name) and node.value.id == "typing":
                    continue
                used.add(node.attr)

        missing = used - imported
        if missing:
            problems.append(
                f"{p.relative_to(PLUGIN)}: 使用了未导入的 typing 名字 {sorted(missing)}"
            )
    return problems


problems = scan_typing_imports()
check("1-1 无未导入的 typing 名字", not problems, f"problems={problems}")


# ================= 2. 全模块可编译 =================


def compile_all():
    errors = []
    for p in py_files():
        src = p.read_text(encoding="utf-8")
        try:
            compile(src, str(p), "exec")
        except SyntaxError as e:
            errors.append(f"{p.relative_to(PLUGIN)}: {e}")
    return errors


errors = compile_all()
check("2-1 全部模块语法可编译", not errors, f"errors={errors}")


# ================= 3. 新增模块可真实导入（桩掉 app.*） =================


def _install_stubs():
    if "app" in sys.modules:
        return
    app = types.ModuleType("app")
    log = types.ModuleType("app.log")

    class _L:
        def info(self, *a, **k):
            pass

        warning = error = debug = info

    log.logger = _L()
    app.log = log
    sys.modules.update({"app": app, "app.log": log})


_install_stubs()


def import_module_file(name, path):
    spec_path = pathlib.Path(path)
    src = spec_path.read_text(encoding="utf-8")
    mod = types.ModuleType(name)
    mod.__file__ = str(spec_path)
    sys.modules[name] = mod
    exec(compile(src, str(spec_path), "exec"), mod.__dict__)
    return mod


targets = [
    ("_guard_dian115", "clients/dian115.py"),
    ("_guard_checkin", "handlers/checkin.py"),
]

for mod_name, rel in targets:
    try:
        m = import_module_file(mod_name, PLUGIN / rel)
        ok = m is not None
    except Exception as e:  # noqa: BLE001 - 需要把任何导入期错误都暴露出来
        ok = False
        print(f"       导入异常：{e.__class__.__name__}: {e}")
    check(f"3-x {rel} 可导入", ok)


# ================= 4. 关键常量与接口契约 =================

try:
    dian = sys.modules["_guard_dian115"]
    check("4-1 暴露 Dian115Client", hasattr(dian, "Dian115Client"))
    check("4-2 暴露 Dian115Error", hasattr(dian, "Dian115Error"))
    check("4-3 暴露 is_115_share_url", callable(getattr(dian, "is_115_share_url", None)))
    check("4-4 暴露 resource_path / share_path",
          callable(getattr(dian, "resource_path", None))
          and callable(getattr(dian, "share_path", None)))
    client_api = ["is_configured", "search_resources", "get_account_info",
                  "signin", "run_lottery"]
    missing_api = [m for m in client_api
                   if not hasattr(dian.Dian115Client, m)]
    check("4-5 客户端接口齐备", not missing_api, f"missing={missing_api}")

    checkin = sys.modules["_guard_checkin"]
    check("4-6 暴露 CheckinHandler", hasattr(checkin, "CheckinHandler"))
    handler_api = ["enabled_providers", "run_checkin", "get_history", "last_record"]
    missing_h = [m for m in handler_api if not hasattr(checkin.CheckinHandler, m)]
    check("4-7 签到处理器接口齐备", not missing_h, f"missing={missing_h}")
    # 只校验「没有真实引入 sqlite」，文档字符串里提到 SQLite 属正常
    src = (PLUGIN / "handlers" / "checkin.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported_mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_mods |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_mods.add(node.module.split(".")[0])
    check("4-8 历史使用插件数据键而非独立存储",
          "sqlite3" not in imported_mods and "sqlalchemy" not in imported_mods,
          f"imported={sorted(imported_mods)}")
except Exception as e:  # noqa: BLE001
    check("4-x 契约检查可执行", False, f"{e.__class__.__name__}: {e}")


# ================= 结果 =================

print("=" * 60)
if FAILURES:
    print(f"结果：{len(FAILURES)} 项失败 -> {FAILURES}")
    sys.exit(1)
print("结果：全部断言通过")
