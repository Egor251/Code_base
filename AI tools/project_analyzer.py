"""
Скрипт для анализа структуры проекта
Показывает архитектуру, зависимости и ключевые компоненты
Версия 2.0: Декомпозированная, с разделением ответственности
"""

import os
import ast
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field
import json


@dataclass
class ProjectStats:
    """Статистика проекта"""
    total_py_files: int = 0
    total_lines: int = 0
    total_classes: int = 0
    total_functions: int = 0
    avg_file_size: float = 0.0


@dataclass
class FileInfo:
    """Информация о файле"""
    path: Path
    size_bytes: int
    lines: int
    imports: List[str] = field(default_factory=list)
    classes: List[Dict] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)


@dataclass
class DirectoryInfo:
    """Информация о директории"""
    path: Path
    is_package: bool
    subdirectories: Dict[str, 'DirectoryInfo'] = field(default_factory=dict)
    files: List[FileInfo] = field(default_factory=list)


class ProjectStructure:
    """Отвечает только за анализ структуры файлов и директорий"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self._ignored_dirs = {'.git', '__pycache__', 'venv', 'env', '.venv', 'node_modules'}
        self._ignored_files = {'.DS_Store', 'thumbs.db'}

    def build_tree(self) -> DirectoryInfo:
        """Строит дерево директорий проекта"""
        return self._build_directory_tree(self.project_root)

    def _build_directory_tree(self, dir_path: Path) -> DirectoryInfo:
        """Рекурсивно строит дерево директорий"""
        dir_info = DirectoryInfo(
            path=dir_path.relative_to(self.project_root),
            is_package=self._is_package(dir_path)
        )

        try:
            entries = list(dir_path.iterdir())
        except (PermissionError, OSError):
            return dir_info

        # Сначала обрабатываем поддиректории
        for entry in entries:
            if entry.is_dir() and entry.name not in self._ignored_dirs:
                if not entry.name.startswith('.'):
                    sub_dir = self._build_directory_tree(entry)
                    dir_info.subdirectories[entry.name] = sub_dir

        # Затем файлы
        for entry in entries:
            if entry.is_file() and entry.name not in self._ignored_files:
                if entry.suffix == '.py':
                    file_info = self._analyze_file(entry)
                    dir_info.files.append(file_info)

        return dir_info

    def _is_package(self, dir_path: Path) -> bool:
        """Проверяет, является ли директория Python пакетом"""
        return (dir_path / '__init__.py').exists()

    def _analyze_file(self, file_path: Path) -> FileInfo:
        """Анализирует отдельный файл"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.count('\n') + 1

            # Базовая информация о файле
            file_info = FileInfo(
                path=file_path.relative_to(self.project_root),
                size_bytes=file_path.stat().st_size,
                lines=lines
            )

            # Извлекаем структуру файла
            try:
                tree = ast.parse(content, filename=str(file_path))

                # Импорты
                file_info.imports = self._extract_imports_from_tree(tree)

                # Классы
                file_info.classes = self._extract_classes_from_tree(tree)

                # Функции
                file_info.functions = self._extract_functions_from_tree(tree)

            except SyntaxError:
                # Файл с синтаксической ошибкой, пропускаем анализ AST
                pass

        except (UnicodeDecodeError, OSError) as e:
            # Создаем минимальную информацию для проблемных файлов
            file_info = FileInfo(
                path=file_path.relative_to(self.project_root),
                size_bytes=0,
                lines=0
            )

        return file_info

    @staticmethod
    def _extract_imports_from_tree(tree: ast.AST) -> List[str]:
        """Извлекает импорты из AST дерева"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                imports.append(f"from {module} import {', '.join(names)}")

        return imports

    @staticmethod
    def _extract_classes_from_tree(tree: ast.AST) -> List[Dict]:
        """Извлекает информацию о классах из AST"""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "bases": [ProjectStructure._get_base_name(base) for base in node.bases],
                    "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                    "line": node.lineno
                }
                classes.append(class_info)

        return classes

    @staticmethod
    def _extract_functions_from_tree(tree: ast.AST) -> List[str]:
        """Извлекает имена функций из AST"""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)

        return functions

    @staticmethod
    def _get_base_name(base_node: ast.AST) -> str:
        """Получает имя базового класса"""
        if isinstance(base_node, ast.Name):
            return base_node.id
        elif isinstance(base_node, ast.Attribute):
            # Рекурсивно собираем полное имя атрибута
            return ProjectStructure._get_attribute_name(base_node)
        elif isinstance(base_node, ast.Subscript):
            return "Generic"
        else:
            return "unknown"

    @staticmethod
    def _get_attribute_name(node: ast.Attribute) -> str:
        """Рекурсивно собирает имя атрибута"""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{ProjectStructure._get_attribute_name(node.value)}.{node.attr}"
        else:
            return f"unknown.{node.attr}"


class ProjectAnalyzer:
    """Главный класс анализатора, координирующий все компоненты"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.structure_analyzer = ProjectStructure(project_root)

    def analyze(self) -> Dict[str, Any]:
        """Полный анализ проекта с разделением ответственности"""
        print("🔍 Анализирую структуру проекта...")

        # 1. Строим дерево структуры
        dir_tree = self.structure_analyzer.build_tree()

        # 2. Собираем статистику
        stats = self._collect_stats(dir_tree)

        # 3. Анализируем зависимости
        dependencies = self._analyze_dependencies(dir_tree)

        # 4. Находим точки входа
        entry_points = self._find_entry_points(dir_tree)

        return {
            "structure": self._serialize_tree(dir_tree),
            "stats": stats,
            "dependencies": dependencies,
            "entry_points": entry_points,
            "tree": dir_tree  # сохраняем объект для дальнейшего использования
        }

    def _collect_stats(self, dir_tree: DirectoryInfo) -> ProjectStats:
        """Собирает статистику проекта"""
        stats = ProjectStats()

        def process_directory(directory: DirectoryInfo):
            for file_info in directory.files:
                stats.total_py_files += 1
                stats.total_lines += file_info.lines
                stats.total_classes += len(file_info.classes)
                stats.total_functions += len(file_info.functions)

            for sub_dir in directory.subdirectories.values():
                process_directory(sub_dir)

        process_directory(dir_tree)

        if stats.total_py_files > 0:
            stats.avg_file_size = stats.total_lines / stats.total_py_files

        return stats

    def _analyze_dependencies(self, dir_tree: DirectoryInfo) -> Dict[str, List[str]]:
        """Анализирует зависимости проекта"""
        dependencies = {
            "internal": set(),
            "external": set(),
            "standard_lib": set()
        }

        # Стандартные библиотеки (расширенный список)
        stdlib_modules = {
            'os', 'sys', 'json', 'ast', 'typing', 'datetime', 'time', 'pathlib',
            'logging', 'inspect', 'importlib', 'collections', 'itertools', 'functools',
            'math', 're', 'hashlib', 'base64', 'random', 'statistics'
        }

        def collect_imports(directory: DirectoryInfo):
            for file_info in directory.files:
                for import_stmt in file_info.imports:
                    module = self._extract_module_name(import_stmt)
                    if not module:
                        continue

                    # Определяем тип зависимости
                    if self._is_internal_module(module):
                        dependencies["internal"].add(module)
                    elif module in stdlib_modules:
                        dependencies["standard_lib"].add(module)
                    else:
                        dependencies["external"].add(module.split('.')[0])

            for sub_dir in directory.subdirectories.values():
                collect_imports(sub_dir)

        collect_imports(dir_tree)

        # Сортируем для читаемости
        return {
            "internal": sorted(dependencies["internal"]),
            "external": sorted(dependencies["external"]),
            "standard_lib": sorted(dependencies["standard_lib"])
        }

    @staticmethod
    def _extract_module_name(import_stmt: str) -> Optional[str]:
        """Извлекает имя модуля из строки импорта"""
        if import_stmt.startswith('import '):
            return import_stmt.replace('import ', '').split()[0].split('.')[0]
        elif import_stmt.startswith('from '):
            parts = import_stmt.split()
            if len(parts) >= 2:
                return parts[1].split('.')[0]
        return None

    def _is_internal_module(self, module: str) -> bool:
        """Проверяет, является ли модуль внутренним"""
        # Простая эвристика: если модуль начинается с точки или короткое имя
        if module.startswith('.'):
            return True

        # Можно добавить проверку существования файла/папки
        possible_paths = [
            self.project_root / module,
            self.project_root / f"{module}.py",
            self.project_root / module.replace('.', '/')
        ]

        return any(p.exists() for p in possible_paths)

    def _find_entry_points(self, dir_tree: DirectoryInfo) -> List[str]:
        """Находит точки входа в проекте"""
        entry_points = []
        main_files = {'main.py', 'app.py', 'run.py', 'start.py', 'manage.py', 'cli.py'}

        def search_in_directory(directory: DirectoryInfo):
            for file_info in directory.files:
                if file_info.path.name in main_files:
                    entry_points.append(str(file_info.path))

                # Проверяем наличие if __name__ == "__main__"
                if self._has_main_block(file_info):
                    entry_points.append(str(file_info.path))

            for sub_dir in directory.subdirectories.values():
                search_in_directory(sub_dir)

        search_in_directory(dir_tree)
        return sorted(set(entry_points))

    def _has_main_block(self, file_info: FileInfo) -> bool:
        """Проверяет, содержит ли файл if __name__ == "__main__" """
        try:
            file_path = self.project_root / file_info.path
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return 'if __name__ == "__main__"' in content
        except:
            return False

    def _serialize_tree(self, dir_tree: DirectoryInfo) -> Dict:
        """Сериализует дерево директорий в словарь"""
        result = {}

        # Добавляем поддиректории
        for name, sub_dir in dir_tree.subdirectories.items():
            result[name] = self._serialize_tree(sub_dir)

        # Добавляем файлы
        if dir_tree.files:
            result['__files__'] = [str(f.path) for f in dir_tree.files]

        # Добавляем признак пакета
        if dir_tree.is_package:
            result['__package__'] = True

        return result


class ReportGenerator:
    """Отвечает только за генерацию отчетов"""

    @staticmethod
    def generate_text_report(analysis_result: Dict) -> str:
        """Генерирует текстовый отчет"""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("📊 PROJECT STRUCTURE REPORT")
        report_lines.append("=" * 60)

        # Статистика
        stats = analysis_result.get("stats", {})
        report_lines.append(f"\n📈 СТАТИСТИКА:")
        report_lines.append(f"  Файлы Python: {stats.get('total_py_files', 0)}")
        report_lines.append(f"  Всего строк: {stats.get('total_lines', 0)}")
        report_lines.append(f"  Классы: {stats.get('total_classes', 0)}")
        report_lines.append(f"  Функции: {stats.get('total_functions', 0)}")
        report_lines.append(f"  Средний размер файла: {stats.get('avg_file_size', 0):.1f} строк")

        # Структура
        report_lines.append(f"\n📁 СТРУКТУРА ПРОЕКТА:")
        report_lines.append(ReportGenerator._format_tree(analysis_result.get("structure", {})))

        # Точки входа
        report_lines.append(f"\n🎯 ТОЧКИ ВХОДА:")
        for entry in analysis_result.get("entry_points", []):
            report_lines.append(f"  • {entry}")

        # Зависимости
        deps = analysis_result.get("dependencies", {})
        report_lines.append(f"\n📦 ЗАВИСИМОСТИ:")
        report_lines.append(f"  Внутренние ({len(deps.get('internal', []))}):")
        for dep in deps.get('internal', [])[:10]:  # Показываем первые 10
            report_lines.append(f"    - {dep}")
        if len(deps.get('internal', [])) > 10:
            report_lines.append(f"    ... и ещё {len(deps.get('internal', [])) - 10}")

        report_lines.append(f"  Внешние ({len(deps.get('external', []))}):")
        for dep in deps.get('external', [])[:15]:
            report_lines.append(f"    - {dep}")

        report_lines.append(f"  Стандартные библиотеки: {len(deps.get('standard_lib', []))}")

        report_lines.append("\n" + "=" * 60)

        return "\n".join(report_lines)

    @staticmethod
    def _format_tree(structure: Dict, indent: int = 0, prefix: str = "") -> str:
        """Форматирует дерево структуры"""
        lines = []

        for key, value in structure.items():
            if key.startswith('__'):
                continue

            current_prefix = "  " * indent + prefix

            if isinstance(value, dict):
                # Это директория
                if value.get('__package__'):
                    lines.append(f"{current_prefix}📦 {key}/")
                else:
                    lines.append(f"{current_prefix}📁 {key}/")

                # Рекурсивно форматируем поддиректории
                lines.append(ReportGenerator._format_tree(value, indent + 1))

                # Добавляем файлы
                if '__files__' in value:
                    file_prefix = "  " * (indent + 1)
                    for file in value['__files__']:
                        lines.append(f"{file_prefix}📄 {Path(file).name}")

        return "\n".join(lines)

    @staticmethod
    def generate_json_report(analysis_result: Dict, output_file: str = None) -> str:
        """Генерирует JSON отчет"""
        # Убираем несериализуемые объекты
        report_data = {k: v for k, v in analysis_result.items() if k != 'tree'}

        json_str = json.dumps(report_data, indent=2, ensure_ascii=False)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    @staticmethod
    def generate_markdown_report(analysis_result: Dict) -> str:
        """Генерирует Markdown отчет"""
        lines = ["# Project Analysis Report", ""]

        stats = analysis_result.get("stats", {})
        lines.append("## 📊 Statistics")
        lines.append(f"- **Python Files**: {stats.get('total_py_files', 0)}")
        lines.append(f"- **Total Lines**: {stats.get('total_lines', 0)}")
        lines.append(f"- **Classes**: {stats.get('total_classes', 0)}")
        lines.append(f"- **Functions**: {stats.get('total_functions', 0)}")
        lines.append("")

        lines.append("## 🎯 Entry Points")
        for entry in analysis_result.get("entry_points", []):
            lines.append(f"- `{entry}`")
        lines.append("")

        return "\n".join(lines)