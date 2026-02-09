#!/usr/bin/env python3
"""
project_validator.py
====================

Валидатор Python проектов.
Проверяет: синтаксис, стиль кода, структуру, зависимости, безопасность.

Использование:
    python project_validator.py [путь_к_проекту] [--format json|text|github]
"""

import os
import ast
import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import argparse
import datetime


class IssueSeverity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationIssue:
    """Проблема, найденная при валидации"""
    file_path: str
    line: Optional[int] = None
    column: Optional[int] = None
    severity: IssueSeverity = IssueSeverity.WARNING
    code: str = ""
    message: str = ""
    suggestion: str = ""


@dataclass
class ValidationResult:
    """Результат валидации проекта"""
    total_files: int = 0
    valid_files: int = 0
    issues_by_severity: Dict[IssueSeverity, List[ValidationIssue]] = field(
        default_factory=lambda: {s: [] for s in IssueSeverity}
    )
    issues_by_category: Dict[str, List[ValidationIssue]] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)
    line_stats: Dict[str, Any] = field(default_factory=dict)  # Новая статистика по строкам


class IssueFilter:
    """Фильтр для управления выводом проблем"""

    def __init__(self, config: Dict):
        self.config = config
        self.filters = self._parse_filters()

    def _parse_filters(self) -> Dict:
        """Парсит фильтры из конфига"""
        filters = {
            "min_severity": IssueSeverity.INFO,  # Минимальная важность
            "max_issues_per_file": 10,  # Максимум проблем на файл
            "max_issues_per_category": 50,  # Максимум проблем на категорию
            "ignore_patterns": [],  # Паттерны для игнорирования
            "show_all": False,  # Показывать все проблемы
        }

        # Обновляем из конфига
        filters.update(self.config.get("filters", {}))
        return filters

    def filter_issues(self, issues: List[ValidationIssue]) -> List[ValidationIssue]:
        """Фильтрует список проблем"""
        if self.filters["show_all"]:
            return issues

        filtered = []
        issues_by_file = {}

        # Группируем по файлам
        for issue in issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)

        # Применяем фильтры
        for file_path, file_issues in issues_by_file.items():
            # Сортируем по важности (ERROR > WARNING > INFO)
            file_issues.sort(key=lambda x: (x.severity.value, x.line or 0))

            # Ограничиваем количество проблем на файл
            limited_issues = file_issues[:self.filters["max_issues_per_file"]]

            # Фильтруем по минимальной важности
            for issue in limited_issues:
                if self._should_show_issue(issue):
                    filtered.append(issue)

        return filtered

    def _should_show_issue(self, issue: ValidationIssue) -> bool:
        """Определяет, нужно ли показывать проблему"""
        # Проверяем минимальную важность
        severity_order = {IssueSeverity.ERROR: 3, IssueSeverity.WARNING: 2, IssueSeverity.INFO: 1}
        min_order = severity_order.get(self.filters["min_severity"], 1)
        issue_order = severity_order.get(issue.severity, 0)

        if issue_order < min_order:
            return False

        # Проверяем паттерны игнорирования
        for pattern in self.filters["ignore_patterns"]:
            if pattern in issue.code or pattern in issue.message:
                return False

        return True


class ProjectValidator:
    """Основной класс валидатора проектов"""

    def __init__(self, project_root: str = ".", config: Optional[Dict] = None):
        self.project_root = Path(project_root).resolve()
        self.config = config or self._default_config()
        self.ignored_dirs = self.config.get("ignored_dirs", ['.git', '__pycache__', 'venv'])
        self.ignored_files = self.config.get("ignored_files", [])

    def _default_config(self) -> Dict:
        """Конфигурация по умолчанию"""
        return {
            "ignored_dirs": ['.git', '__pycache__', 'venv', 'env', '.venv', 'node_modules'],
            "ignored_files": ['.DS_Store', 'thumbs.db'],
            "max_file_size_kb": 100,
            "max_line_length": 120,
            "max_function_lines": 50,
            "max_nesting_depth": 5,
            "check_security": True,
            "check_performance": True,
            "check_style": True,
            "enforce_type_hints": False,
            "require_docstrings": False,
            "output_file": "validation_report.txt",
        }

    def validate_project(self) -> ValidationResult:
        """Полная валидация проекта"""
        print(f"🔍 Валидация проекта: {self.project_root}")

        result = ValidationResult()
        all_issues = []
        line_stats = {
            "total_lines": 0,
            "max_lines": 0,
            "min_lines": float('inf'),
            "file_line_counts": {},
            "avg_lines_per_file": 0
        }

        # Находим все Python файлы
        python_files = self._find_all_python_files()
        result.total_files = len(python_files)

        if result.total_files == 0:
            print("⚠️  Не найдено Python файлов для проверки")
            return result

        print(f"📁 Найдено файлов: {result.total_files}")

        # Проверяем каждый файл и собираем статистику по строкам
        for file_path in python_files:
            rel_path = str(file_path.relative_to(self.project_root))

            # Собираем статистику по строкам
            file_line_count = self._count_file_lines(file_path)
            line_stats["total_lines"] += file_line_count
            line_stats["max_lines"] = max(line_stats["max_lines"], file_line_count)
            line_stats["min_lines"] = min(line_stats["min_lines"], file_line_count)
            line_stats["file_line_counts"][rel_path] = file_line_count

            file_issues = self._validate_file(file_path)
            all_issues.extend(file_issues)

        # Рассчитываем среднее количество строк
        if result.total_files > 0:
            line_stats["avg_lines_per_file"] = line_stats["total_lines"] / result.total_files

        result.line_stats = line_stats

        # Группируем проблемы
        result.issues_by_category = self._categorize_issues(all_issues)
        for severity in IssueSeverity:
            result.issues_by_severity[severity] = [
                issue for issue in all_issues if issue.severity == severity
            ]

        # Считаем статистику
        error_issues = result.issues_by_severity[IssueSeverity.ERROR]
        files_with_errors = len({issue.file_path for issue in error_issues})

        result.valid_files = result.total_files - files_with_errors

        result.stats = {
            "error_count": len(error_issues),
            "warning_count": len(result.issues_by_severity[IssueSeverity.WARNING]),
            "info_count": len(result.issues_by_severity[IssueSeverity.INFO]),
            "files_with_errors": files_with_errors,
            "files_with_warnings": len({issue.file_path for issue in result.issues_by_severity[IssueSeverity.WARNING]}),
            "files_with_info": len({issue.file_path for issue in result.issues_by_severity[IssueSeverity.INFO]}),
        }

        return result

    def _count_file_lines(self, file_path: Path) -> int:
        """Считает количество строк в файле"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except:
            return 0

    def _find_all_python_files(self) -> List[Path]:
        """Находит все Python файлы в проекте"""
        python_files = []

        for root, dirs, files in os.walk(self.project_root):
            # Пропускаем игнорируемые директории
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs and not d.startswith('.')]

            for file in files:
                if file.endswith('.py') and file not in self.ignored_files:
                    python_files.append(Path(root) / file)

        return python_files

    def _validate_file(self, file_path: Path) -> List[ValidationIssue]:
        """Валидирует отдельный файл"""
        issues = []
        rel_path = str(file_path.relative_to(self.project_root))

        # 1. Проверка размера файла
        issues.extend(self._check_file_size(file_path))

        # 2. Проверка синтаксиса
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                issues.append(ValidationIssue(
                    file_path=rel_path,
                    line=e.lineno,
                    column=e.offset,
                    severity=IssueSeverity.ERROR,
                    code="SYNTAX_ERROR",
                    message=f"Синтаксическая ошибка: {e.msg}",
                    suggestion="Исправьте синтаксис Python"
                ))
                return issues  # Не проверяем дальше файлы с синтаксическими ошибками

            # 3. Проверки на основе AST
            if self.config.get("check_style", True):
                issues.extend(self._check_ast_issues(tree, file_path))

            if self.config.get("check_security", True):
                issues.extend(self._check_security_issues(tree, file_path))

            # 4. Проверка стиля кода
            issues.extend(self._check_code_style(content, file_path))

            # 5. Проверка производительности
            if self.config.get("check_performance", True):
                issues.extend(self._check_performance_issues(tree, file_path))

        except (UnicodeDecodeError, PermissionError) as e:
            issues.append(ValidationIssue(
                file_path=rel_path,
                severity=IssueSeverity.ERROR,
                code="FILE_READ_ERROR",
                message=f"Не удалось прочитать файл: {e}",
                suggestion="Проверьте права доступа и кодировку файла"
            ))

        return issues

    def _check_file_size(self, file_path: Path) -> List[ValidationIssue]:
        """Проверяет размер файла"""
        issues = []
        rel_path = str(file_path.relative_to(self.project_root))

        max_size_kb = self.config.get("max_file_size_kb", 100)
        file_size_kb = file_path.stat().st_size / 1024

        if file_size_kb > max_size_kb:
            issues.append(ValidationIssue(
                file_path=rel_path,
                severity=IssueSeverity.WARNING,
                code="FILE_TOO_LARGE",
                message=f"Файл слишком большой: {file_size_kb:.1f}KB (макс: {max_size_kb}KB)",
                suggestion="Разбейте файл на несколько модулей"
            ))

        return issues

    def _check_ast_issues(self, tree: ast.AST, file_path: Path) -> List[ValidationIssue]:
        """Проверяет проблемы на уровне AST"""
        issues = []
        rel_path = str(file_path.relative_to(self.project_root))

        # Проверка на слишком глубокую вложенность
        max_depth = self.config.get("max_nesting_depth", 5)

        class DepthChecker(ast.NodeVisitor):
            def __init__(self):
                self.max_depth = 0
                self.current_depth = 0
                self.issues = []

            def visit_FunctionDef(self, node):
                self.current_depth += 1
                if self.current_depth > max_depth:
                    self.issues.append(ValidationIssue(
                        file_path=rel_path,
                        line=node.lineno,
                        severity=IssueSeverity.WARNING,
                        code="DEEP_NESTING",
                        message=f"Слишком глубокая вложенность: {self.current_depth} уровней",
                        suggestion="Рефакторите код, выделите части в отдельные функции"
                    ))
                self.generic_visit(node)
                self.current_depth -= 1

            def visit_ClassDef(self, node):
                self.current_depth += 1
                self.generic_visit(node)
                self.current_depth -= 1

        checker = DepthChecker()
        checker.visit(tree)
        issues.extend(checker.issues)

        # Проверка на слишком длинные функции
        max_lines = self.config.get("max_function_lines", 50)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Считаем строки в функции
                func_lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 0

                if func_lines > max_lines:
                    issues.append(ValidationIssue(
                        file_path=rel_path,
                        line=node.lineno,
                        severity=IssueSeverity.WARNING,
                        code="FUNCTION_TOO_LONG",
                        message=f"Функция слишком длинная: {func_lines} строк",
                        suggestion=f"Разбейте функцию на части (рекомендуется до {max_lines} строк)"
                    ))

        return issues

    def _check_security_issues(self, tree: ast.AST, file_path: Path) -> List[ValidationIssue]:
        """Проверяет потенциальные уязвимости безопасности"""
        issues = []
        rel_path = str(file_path.relative_to(self.project_root))

        dangerous_functions = {
            'eval': 'Использование eval() опасно',
            'exec': 'Использование exec() опасно',
            'pickle.loads': 'Десериализация pickle может быть опасна',
            'yaml.load': 'Используйте yaml.safe_load()',
            'subprocess.Popen': 'Проверяйте аргументы командной строки',
            'os.system': 'Используйте subprocess с аргументами',
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Проверяем вызовы опасных функций
                func_name = self._get_function_name(node.func)
                if func_name in dangerous_functions:
                    issues.append(ValidationIssue(
                        file_path=rel_path,
                        line=node.lineno,
                        severity=IssueSeverity.WARNING,
                        code="SECURITY_RISK",
                        message=dangerous_functions[func_name],
                        suggestion="Используйте безопасные альтернативы или проверяйте входные данные"
                    ))

        return issues

    @staticmethod
    def _get_function_name(node: ast.AST) -> str:
        """Получает имя функции из AST узла"""
        match node:
            case ast.Name():
                return node.id
            case ast.Attribute():
                if isinstance(node.value, ast.Name):
                    return f"{node.value.id}.{node.attr}"
        return ""

    def _check_code_style(self, content: str, file_path: Path) -> List[ValidationIssue]:
        """Проверяет стиль кода"""
        issues = []
        rel_path = str(file_path.relative_to(self.project_root))
        lines = content.split('\n')

        # Проверка длины строк
        max_line_length = self.config.get("max_line_length", 120)
        for i, line in enumerate(lines, 1):
            if len(line) > max_line_length:
                issues.append(ValidationIssue(
                    file_path=rel_path,
                    line=i,
                    severity=IssueSeverity.WARNING,
                    code="LINE_TOO_LONG",
                    message=f"Строка слишком длинная: {len(line)} символов",
                    suggestion=f"Разбейте строку (макс: {max_line_length} символов)"
                ))

        # Проверка на смешивание табов и пробелов
        if '\t' in content and '    ' in content:
            issues.append(ValidationIssue(
                file_path=rel_path,
                severity=IssueSeverity.ERROR,
                code="MIXED_INDENTATION",
                message="Смешаны табы и пробелы для отступов",
                suggestion="Используйте только пробелы (рекомендуется 4 пробела)"
            ))

        # Проверка на trailing whitespace
        for i, line in enumerate(lines, 1):
            if line.endswith(' ') or line.endswith('\t'):
                issues.append(ValidationIssue(
                    file_path=rel_path,
                    line=i,
                    severity=IssueSeverity.WARNING,
                    code="TRAILING_WHITESPACE",
                    message="Лишние пробелы в конце строки",
                    suggestion="Удалите пробелы в конце строки"
                ))

        return issues

    def _check_performance_issues(self, tree: ast.AST, file_path: Path) -> List[ValidationIssue]:
        """Проверяет потенциальные проблемы производительности"""
        issues = []
        rel_path = str(file_path.relative_to(self.project_root))

        for node in ast.walk(tree):
            match node:
                case ast.For(iter=ast.Call(func=ast.Name(id='range'), args=[ast.Call(func=ast.Name(id='len'))])):
                    # range(len(...)) в цикле for
                    issues.append(ValidationIssue(
                        file_path=rel_path,
                        line=node.lineno,
                        severity=IssueSeverity.INFO,
                        code="INEFFICIENT_RANGE",
                        message="Использование range(len(...)) может быть неэффективным",
                        suggestion="Используйте enumerate() для доступа к индексам и значениям"
                    ))

                case ast.For(iter=ast.Call(func=ast.Name(id='range'), args=[ast.Call(func=ast.Name(id='len'))] as args)) if len(args) == 1:
                    # Дополнительная проверка для range(len(...))
                    issues.append(ValidationIssue(
                        file_path=rel_path,
                        line=node.lineno,
                        severity=IssueSeverity.INFO,
                        code="INEFFICIENT_RANGE",
                        message="range(len(...)) вместо enumerate()",
                        suggestion="Замените на enumerate(iterable) для лучшей читаемости"
                    ))

                case ast.ListComp() | ast.SetComp() | ast.DictComp() as comp:
                    # Проверка сложных генераторов
                    if len(comp.generators) > 2:
                        issues.append(ValidationIssue(
                            file_path=rel_path,
                            line=node.lineno,
                            severity=IssueSeverity.INFO,
                            code="COMPLEX_COMPREHENSION",
                            message="Слишком сложное выражение-генератор",
                            suggestion="Рассмотрите использование обычных циклов для улучшения читаемости"
                        ))

                case ast.Call(func=ast.Attribute(value=ast.Name(id='re'), attr='compile')) if len(node.args) > 0:
                    # Компиляция regex в цикле
                    for parent in ast.walk(tree):
                        if isinstance(parent, (ast.For, ast.While)) and node in ast.walk(parent):
                            issues.append(ValidationIssue(
                                file_path=rel_path,
                                line=node.lineno,
                                severity=IssueSeverity.WARNING,
                                code="REGEX_IN_LOOP",
                                message="Компиляция регулярного выражения внутри цикла",
                                suggestion="Вынесите re.compile() за пределы цикла"
                            ))
                            break

                case ast.Call(func=ast.Name(id='list') | ast.Name(id='dict') | ast.Name(id='set') as func):
                    # Избыточное преобразование типов
                    if len(node.args) == 1 and isinstance(node.args[0], (ast.List, ast.Dict, ast.Set)):
                        func_name = func.id
                        issues.append(ValidationIssue(
                            file_path=rel_path,
                            line=node.lineno,
                            severity=IssueSeverity.INFO,
                            code="REDUNDANT_CONVERSION",
                            message=f"Избыточное преобразование {func_name}(...)",
                            suggestion=f"Используйте литерал напрямую вместо {func_name}()"
                        ))

        return issues

    def _categorize_issues(self, issues: List[ValidationIssue]) -> Dict[str, List[ValidationIssue]]:
        """Группирует проблемы по категориям"""
        categories = {
            "syntax": [],
            "security": [],
            "performance": [],
            "style": [],
            "structure": [],
            "other": []
        }

        category_mapping = {
            "SYNTAX": "syntax",
            "SECURITY": "security",
            "PERFORMANCE": "performance",
            "INEFFICIENT": "performance",
            "REGEX": "performance",
            "COMPLEX": "performance",
            "REDUNDANT": "performance",
            "LINE": "style",
            "WHITESPACE": "style",
            "INDENTATION": "style",
            "FILE": "structure",
            "FUNCTION": "structure",
            "NESTING": "structure",
            "DEEP": "structure",
        }

        for issue in issues:
            assigned = False
            for keyword, category in category_mapping.items():
                if keyword in issue.code:
                    categories[category].append(issue)
                    assigned = True
                    break

            if not assigned:
                categories["other"].append(issue)

        return categories

    def check_dependencies(self) -> List[ValidationIssue]:
        """Проверяет зависимости проекта"""
        issues = []

        # Проверяем наличие requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    requirements = f.readlines()

                # Простые проверки requirements.txt
                for i, line in enumerate(requirements, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '==' not in line and line.count('>') < 2 and line.count('<') < 2:
                        issues.append(ValidationIssue(
                            file_path="requirements.txt",
                            line=i,
                            severity=IssueSeverity.WARNING,
                            code="LOOSE_DEPENDENCY",
                            message=f"Зависимость без версии: {line}",
                            suggestion="Укажите конкретную версию зависимости (напр. 'package==1.0.0')"
                        ))
            except Exception as e:
                issues.append(ValidationIssue(
                    file_path="requirements.txt",
                    severity=IssueSeverity.ERROR,
                    code="REQUIREMENTS_ERROR",
                    message=f"Не удалось прочитать requirements.txt: {e}",
                    suggestion="Проверьте формат файла"
                ))
        else:
            issues.append(ValidationIssue(
                file_path="requirements.txt",
                severity=IssueSeverity.WARNING,
                code="NO_REQUIREMENTS",
                message="Файл requirements.txt не найден",
                suggestion="Создайте файл requirements.txt для управления зависимостями"
            ))

        return issues


class ReportFormatter:
    """Форматирует результаты валидации"""

    @staticmethod
    def format_text(
            result: ValidationResult,
            verbose: bool = False,
            output_file: str = None,
            issue_filter: Optional[IssueFilter] = None
    ) -> str:
        """Текстовый формат отчета"""
        lines = []

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines.append("=" * 70)
        lines.append(f"📋 ОТЧЕТ ВАЛИДАЦИИ ПРОЕКТА")
        lines.append(f"📅 {timestamp}")
        lines.append("=" * 70)

        # Статистика проекта
        lines.append(f"\n📊 СТАТИСТИКА ПРОЕКТА:")
        lines.append(f"  Всего файлов: {result.total_files}")
        lines.append(f"  Валидных файлов: {result.valid_files}")
        lines.append(f"  Ошибок: {result.stats.get('error_count', 0)}")
        lines.append(f"  Предупреждений: {result.stats.get('warning_count', 0)}")
        lines.append(f"  Замечаний: {result.stats.get('info_count', 0)}")

        # Статистика по строкам
        if result.line_stats:
            lines.append(f"\n📏 СТАТИСТИКА ПО СТРОКАМ:")
            lines.append(f"  Всего строк: {result.line_stats.get('total_lines', 0):,}")
            lines.append(f"  Среднее на файл: {result.line_stats.get('avg_lines_per_file', 0):.1f}")
            lines.append(f"  Максимум: {result.line_stats.get('max_lines', 0):,}")
            lines.append(f"  Минимум: {result.line_stats.get('min_lines', 0):,}")

            # Показываем топ-5 самых больших файлов
            file_counts = result.line_stats.get('file_line_counts', {})
            if file_counts:
                sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                lines.append(f"\n  📈 Топ-5 самых больших файлов:")
                for file_path, count in sorted_files:
                    lines.append(f"    • {file_path}: {count:,} строк")

        # Суммарная статистика по проблемам
        lines.append(f"\n⚠️  СВОДНАЯ СТАТИСТИКА ПРОБЛЕМ:")

        # Проблемы по категориям
        for category, category_issues in sorted(result.issues_by_category.items()):
            if category_issues:
                # Подсчитываем по важности
                error_count = len([i for i in category_issues if i.severity == IssueSeverity.ERROR])
                warning_count = len([i for i in category_issues if i.severity == IssueSeverity.WARNING])
                info_count = len([i for i in category_issues if i.severity == IssueSeverity.INFO])

                severity_summary = []
                if error_count > 0:
                    severity_summary.append(f"❌ {error_count}")
                if warning_count > 0:
                    severity_summary.append(f"⚠️  {warning_count}")
                if info_count > 0:
                    severity_summary.append(f"ℹ️  {info_count}")

                severity_str = " | ".join(severity_summary)
                lines.append(f"  {category.upper():12} ({len(category_issues):4}) [{severity_str}]")

        lines.append(f"\n📁 Файлов с проблемами:")
        lines.append(f"  С ошибками: {result.stats.get('files_with_errors', 0)}")
        lines.append(f"  С предупреждениями: {result.stats.get('files_with_warnings', 0)}")
        lines.append(f"  С замечаниями: {result.stats.get('files_with_info', 0)}")

        # Показываем детали по проблемам (с фильтрацией)
        lines.append(f"\n🔎 ДЕТАЛЬНЫЙ ОТЧЕТ ПО ПРОБЛЕМАМ:")

        # Применяем фильтр если есть
        filtered_categories = {}
        for category, category_issues in result.issues_by_category.items():
            if issue_filter:
                filtered_categories[category] = issue_filter.filter_issues(category_issues)
            else:
                filtered_categories[category] = category_issues[:50]  # Ограничиваем по умолчанию

        for category, category_issues in filtered_categories.items():
            if category_issues:
                # Группируем проблемы по файлам
                issues_by_file = {}
                for issue in category_issues:
                    if issue.file_path not in issues_by_file:
                        issues_by_file[issue.file_path] = []
                    issues_by_file[issue.file_path].append(issue)

                if issues_by_file:
                    lines.append(f"\n  {category.upper()} ({len(category_issues)}):")

                    # Показываем проблемы по файлам
                    for file_path, file_issues in sorted(issues_by_file.items())[:15]:  # Ограничиваем файлы
                        # Группируем по типам проблем
                        issues_by_type = {}
                        for issue in file_issues:
                            if issue.code not in issues_by_type:
                                issues_by_type[issue.code] = []
                            issues_by_type[issue.code].append(issue)

                        # Создаем краткое описание
                        type_summary = []
                        for code, type_issues in list(issues_by_type.items())[:3]:  # Показываем первые 3 типа
                            type_summary.append(f"{code}({len(type_issues)})")

                        if len(issues_by_type) > 3:
                            type_summary.append(f"...(+{len(issues_by_type) - 3})")

                        lines.append(f"    📄 {file_path}:")
                        lines.append(f"        Всего проблем: {len(file_issues)}")
                        lines.append(f"        Типы: {', '.join(type_summary)}")

                        # Показываем примеры проблем если verbose
                        if verbose:
                            for issue in file_issues[:5]:  # Показываем первые 5 проблем из файла
                                line_info = f" строка {issue.line}" if issue.line else ""
                                severity_icon = {
                                    IssueSeverity.ERROR: "❌",
                                    IssueSeverity.WARNING: "⚠️",
                                    IssueSeverity.INFO: "ℹ️"
                                }.get(issue.severity, "•")

                                lines.append(f"        {severity_icon} {issue.code}{line_info}: {issue.message}")
                                if issue.suggestion:
                                    lines.append(f"          💡 {issue.suggestion}")

        # Если проблемы были отфильтрованы, показываем информацию
        total_filtered_issues = sum(len(issues) for issues in filtered_categories.values())
        total_original_issues = sum(len(issues) for issues in result.issues_by_category.values())

        if total_filtered_issues < total_original_issues:
            lines.append(f"\n📝 Примечание:")
            lines.append(f"  Показано {total_filtered_issues} из {total_original_issues} проблем")
            lines.append(f"  Используйте --show-all для полного отчета")

        # Итог
        if result.stats.get('error_count', 0) == 0:
            lines.append("\n✅ ПРОЕКТ ПРОШЕЛ БАЗОВУЮ ВАЛИДАЦИЮ")
        else:
            lines.append(f"\n❌ НАЙДЕНО {result.stats.get('error_count', 0)} ОШИБОК")
            lines.append("   Рекомендуется исправить ошибки перед коммитом")

        lines.append("\n" + "=" * 70)

        report_text = "\n".join(lines)

        # Сохраняем в файл если указано
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                print(f"\n💾 Отчет сохранен в: {output_file}")
            except Exception as e:
                print(f"\n⚠️  Не удалось сохранить отчет: {e}")

        return report_text

    @staticmethod
    def format_compact(result: ValidationResult) -> str:
        """Компактный формат отчета для быстрого обзора"""
        lines = []

        lines.append("=" * 50)
        lines.append("📊 КОМПАКТНЫЙ ОТЧЕТ ВАЛИДАЦИИ")
        lines.append("=" * 50)

        # Основная статистика
        lines.append(f"\n📁 Файлов: {result.total_files}")
        lines.append(f"📏 Строк: {result.line_stats.get('total_lines', 0):,}")

        # Иконки статуса
        error_icon = "❌" if result.stats.get('error_count', 0) > 0 else "✅"
        warning_icon = "⚠️" if result.stats.get('warning_count', 0) > 0 else "✅"

        lines.append(f"\n{error_icon} Ошибок: {result.stats.get('error_count', 0)}")
        lines.append(f"{warning_icon} Предупреждений: {result.stats.get('warning_count', 0)}")

        # Самые проблемные файлы
        if result.issues_by_category:
            # Находим файлы с наибольшим количеством проблем
            all_issues = []
            for category_issues in result.issues_by_category.values():
                all_issues.extend(category_issues)

            issues_by_file = {}
            for issue in all_issues:
                if issue.file_path not in issues_by_file:
                    issues_by_file[issue.file_path] = []
                issues_by_file[issue.file_path].append(issue)

            # Сортируем по количеству проблем
            sorted_files = sorted(issues_by_file.items(), key=lambda x: len(x[1]), reverse=True)[:5]

            if sorted_files:
                lines.append(f"\n🔥 Топ-5 проблемных файлов:")
                for file_path, file_issues in sorted_files:
                    error_count = len([i for i in file_issues if i.severity == IssueSeverity.ERROR])
                    warning_count = len([i for i in file_issues if i.severity == IssueSeverity.WARNING])

                    severity_str = ""
                    if error_count > 0:
                        severity_str += f"❌{error_count} "
                    if warning_count > 0:
                        severity_str += f"⚠️{warning_count}"

                    lines.append(f"  • {file_path}: {len(file_issues)} проблем ({severity_str})")

        lines.append("\n" + "=" * 50)

        return "\n".join(lines)


# Обновим main функцию
def main():
    """Точка входа"""
    parser = argparse.ArgumentParser(
        description="Валидатор Python проектов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python project_validator.py                    # Базовая проверка текущей директории
  python project_validator.py --compact          # Компактный отчет
  python project_validator.py --show-all         # Показать все проблемы (без фильтрации)
  python project_validator.py --min-severity WARNING  # Только предупреждения и ошибки
  python project_validator.py --ignore trailing  # Игнорировать trailing whitespace
  python project_validator.py --output report.md # Сохранить как markdown
        """
    )

    parser.add_argument("path", nargs="?", default=".", help="Путь к проекту")
    parser.add_argument("--format", choices=["text", "json", "github", "compact"], default="text",
                        help="Формат вывода (по умолчанию: text)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    parser.add_argument("--compact", action="store_true", help="Компактный отчет")
    parser.add_argument("--config", help="Путь к конфигурационному файлу JSON")
    parser.add_argument("--output", "-o", help="Имя выходного файла для отчета")
    parser.add_argument("--no-save", action="store_true", help="Не сохранять отчет в файл")
    parser.add_argument("--show-all", action="store_true", help="Показать все проблемы (без ограничений)")
    parser.add_argument("--min-severity", choices=["ERROR", "WARNING", "INFO"], default="INFO",
                        help="Минимальная важность проблем для показа")
    parser.add_argument("--ignore", action="append", help="Игнорировать проблемы с указанным кодом")

    args = parser.parse_args()

    args.path = "C:\\Users\\Egor\\PycharmProjects\\ProjectMind\\ProjectMind\\ProjectMind-core"
    # Загружаем конфиг если указан
    config = {}
    if args.config and Path(args.config).exists():
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка чтения конфига: {e}")
            sys.exit(1)

    # Обновляем конфиг аргументами командной строки
    if "filters" not in config:
        config["filters"] = {}

    config["filters"]["show_all"] = args.show_all
    if args.min_severity:
        config["filters"]["min_severity"] = IssueSeverity[args.min_severity]
    if args.ignore:
        config["filters"]["ignore_patterns"] = args.ignore

    # Запускаем валидацию
    validator = ProjectValidator(args.path, config)

    try:
        result = validator.validate_project()

        # Добавляем проверку зависимостей
        dep_issues = validator.check_dependencies()
        for issue in dep_issues:
            result.issues_by_severity[issue.severity].append(issue)
            # Также добавляем в категоризацию
            result.issues_by_category.setdefault("dependencies", []).append(issue)

        # Создаем фильтр
        issue_filter = IssueFilter(config) if not args.show_all else None

        # Определяем имя выходного файла
        output_filename = args.output or config.get("output_file", "validation_report.txt")

        # Форматируем отчет
        if args.format == "json" or args.compact:
            output_file = None if args.no_save else output_filename.replace('.txt', '.json')
            report = ReportFormatter.format_json(result, output_file)
        elif args.format == "github":
            report = ReportFormatter.format_github_actions(result)
            if not args.no_save:
                with open("github_actions_report.txt", 'w', encoding='utf-8') as f:
                    f.write(report)
        elif args.compact:
            output_file = None if args.no_save else "validation_compact.txt"
            report = ReportFormatter.format_compact(result)
            if output_file and not args.no_save:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report)
        else:
            output_file = None if args.no_save else output_filename
            report = ReportFormatter.format_text(result, args.verbose, output_file, issue_filter)

        print(report)

        # Возвращаем код выхода
        if result.stats.get('error_count', 0) > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⏹️  Валидация прервана пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)



if __name__ == "__main__":
    main()
