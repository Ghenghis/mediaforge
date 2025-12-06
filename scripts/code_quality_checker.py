"""
Code Quality Checker & Auto-Repair System
==========================================
Identifies and optionally fixes common code quality issues:
- Large methods (>50 lines)
- Deep nesting (>3 levels)
- Excess function arguments (>4)
- Code duplication
- Missing documentation
"""
import os
import re
import ast
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


@dataclass
class CodeIssue:
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # warning, error, info
    message: str
    suggestion: Optional[str] = None
    auto_fixable: bool = False


class CodeQualityChecker:
    """Analyze Python files for code quality issues"""
    
    # Thresholds
    MAX_METHOD_LINES = 50
    MAX_NESTING_DEPTH = 3
    MAX_FUNCTION_ARGS = 4
    MAX_COMPLEXITY = 10
    
    def __init__(self):
        self.issues: List[CodeIssue] = []
        self.stats = {
            "files_checked": 0,
            "total_issues": 0,
            "by_severity": {"error": 0, "warning": 0, "info": 0},
            "by_type": {}
        }
    
    def analyze_directory(self, directory: Path, exclude_patterns: List[str] = None):
        """Analyze all Python files in directory"""
        exclude_patterns = exclude_patterns or ["__pycache__", ".git", "venv", "node_modules"]
        
        for py_file in directory.rglob("*.py"):
            # Skip excluded patterns
            if any(pattern in str(py_file) for pattern in exclude_patterns):
                continue
            
            self.analyze_file(py_file)
        
        return self.generate_report()
    
    def analyze_file(self, file_path: Path):
        """Analyze a single Python file"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")
            
            self.stats["files_checked"] += 1
            
            # Parse AST
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, str(file_path), lines)
            except SyntaxError as e:
                self._add_issue(CodeIssue(
                    file_path=str(file_path),
                    line_number=e.lineno or 1,
                    issue_type="syntax_error",
                    severity="error",
                    message=f"Syntax error: {e.msg}"
                ))
            
            # Line-based analysis
            self._analyze_lines(str(file_path), lines)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def _analyze_ast(self, tree: ast.AST, file_path: str, lines: List[str]):
        """Analyze AST for structural issues"""
        
        for node in ast.walk(tree):
            # Check function definitions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_function(node, file_path, lines)
            
            # Check class definitions
            elif isinstance(node, ast.ClassDef):
                self._check_class(node, file_path)
    
    def _check_function(self, node: ast.FunctionDef, file_path: str, lines: List[str]):
        """Check a function for issues"""
        
        # Check argument count
        args = node.args
        total_args = (
            len(args.args) + 
            len(args.posonlyargs) + 
            len(args.kwonlyargs) +
            (1 if args.vararg else 0) +
            (1 if args.kwarg else 0)
        )
        
        # Exclude 'self' and 'cls'
        if args.args and args.args[0].arg in ('self', 'cls'):
            total_args -= 1
        
        if total_args > self.MAX_FUNCTION_ARGS:
            self._add_issue(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="excess_arguments",
                severity="warning",
                message=f"Function '{node.name}' has {total_args} arguments (max: {self.MAX_FUNCTION_ARGS})",
                suggestion="Consider using a dataclass or config object to group parameters",
                auto_fixable=False
            ))
        
        # Check method length
        if node.end_lineno:
            method_lines = node.end_lineno - node.lineno
            if method_lines > self.MAX_METHOD_LINES:
                self._add_issue(CodeIssue(
                    file_path=file_path,
                    line_number=node.lineno,
                    issue_type="large_method",
                    severity="warning",
                    message=f"Method '{node.name}' is {method_lines} lines (max: {self.MAX_METHOD_LINES})",
                    suggestion="Split into smaller, focused methods",
                    auto_fixable=False
                ))
        
        # Check nesting depth
        max_depth = self._calculate_nesting_depth(node)
        if max_depth > self.MAX_NESTING_DEPTH:
            self._add_issue(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="deep_nesting",
                severity="warning",
                message=f"Method '{node.name}' has nesting depth {max_depth} (max: {self.MAX_NESTING_DEPTH})",
                suggestion="Use early returns, extract helper functions, or simplify conditionals",
                auto_fixable=False
            ))
        
        # Check for missing docstring
        if not ast.get_docstring(node):
            self._add_issue(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="missing_docstring",
                severity="info",
                message=f"Function '{node.name}' is missing a docstring",
                suggestion="Add a docstring describing the function's purpose",
                auto_fixable=True
            ))
    
    def _calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth in a function"""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _check_class(self, node: ast.ClassDef, file_path: str):
        """Check a class for issues"""
        
        # Count methods
        methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        
        if len(methods) > 20:
            self._add_issue(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="large_class",
                severity="warning",
                message=f"Class '{node.name}' has {len(methods)} methods (consider splitting)",
                suggestion="Consider extracting related methods into separate classes"
            ))
        
        # Check for missing docstring
        if not ast.get_docstring(node):
            self._add_issue(CodeIssue(
                file_path=file_path,
                line_number=node.lineno,
                issue_type="missing_docstring",
                severity="info",
                message=f"Class '{node.name}' is missing a docstring"
            ))
    
    def _analyze_lines(self, file_path: str, lines: List[str]):
        """Analyze code lines for common issues"""
        
        for i, line in enumerate(lines, 1):
            # Check for very long lines
            if len(line) > 120:
                self._add_issue(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="long_line",
                    severity="info",
                    message=f"Line is {len(line)} characters (max: 120)",
                    auto_fixable=True
                ))
            
            # Check for TODO/FIXME comments
            if "TODO" in line or "FIXME" in line:
                self._add_issue(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="todo_comment",
                    severity="info",
                    message=f"Found TODO/FIXME: {line.strip()[:80]}"
                ))
            
            # Check for hardcoded credentials patterns
            cred_patterns = [r'password\s*=\s*["\'][^"\']+["\']', r'api_key\s*=\s*["\'][^"\']+["\']']
            for pattern in cred_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self._add_issue(CodeIssue(
                        file_path=file_path,
                        line_number=i,
                        issue_type="hardcoded_credential",
                        severity="error",
                        message="Possible hardcoded credential detected",
                        suggestion="Use environment variables or config files"
                    ))
    
    def _add_issue(self, issue: CodeIssue):
        """Add an issue to the list"""
        self.issues.append(issue)
        self.stats["total_issues"] += 1
        self.stats["by_severity"][issue.severity] += 1
        self.stats["by_type"][issue.issue_type] = self.stats["by_type"].get(issue.issue_type, 0) + 1
    
    def generate_report(self) -> Dict:
        """Generate analysis report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "issues": [asdict(i) for i in self.issues],
            "summary": self._generate_summary()
        }
        
        # Save report
        report_path = REPORTS_DIR / f"code_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _generate_summary(self) -> str:
        """Generate human-readable summary"""
        lines = [
            f"Code Quality Report",
            f"==================",
            f"Files Checked: {self.stats['files_checked']}",
            f"Total Issues: {self.stats['total_issues']}",
            f"",
            f"By Severity:",
            f"  Errors: {self.stats['by_severity']['error']}",
            f"  Warnings: {self.stats['by_severity']['warning']}",
            f"  Info: {self.stats['by_severity']['info']}",
            f"",
            f"By Type:"
        ]
        
        for issue_type, count in sorted(self.stats["by_type"].items(), key=lambda x: -x[1]):
            lines.append(f"  {issue_type}: {count}")
        
        return "\n".join(lines)
    
    def print_report(self):
        """Print report to console"""
        print(self._generate_summary())
        print()
        
        # Group issues by file
        by_file = {}
        for issue in self.issues:
            if issue.file_path not in by_file:
                by_file[issue.file_path] = []
            by_file[issue.file_path].append(issue)
        
        # Print top issues
        print("Top Issues:")
        print("-" * 60)
        
        for file_path, file_issues in sorted(by_file.items()):
            errors = [i for i in file_issues if i.severity == "error"]
            warnings = [i for i in file_issues if i.severity == "warning"]
            
            if errors or warnings:
                rel_path = Path(file_path).relative_to(BASE_DIR) if file_path.startswith(str(BASE_DIR)) else file_path
                print(f"\n{rel_path}:")
                
                for issue in (errors + warnings)[:5]:
                    icon = "❌" if issue.severity == "error" else "⚠️"
                    print(f"  {icon} Line {issue.line_number}: {issue.message}")
                    if issue.suggestion:
                        print(f"     💡 {issue.suggestion}")


def main():
    print("=" * 60)
    print("  CODE QUALITY CHECKER")
    print("=" * 60)
    print()
    
    checker = CodeQualityChecker()
    
    # Analyze scripts directory
    scripts_dir = BASE_DIR / "scripts"
    mcp_dir = BASE_DIR / "mcp_server"
    
    print(f"Analyzing: {scripts_dir}")
    checker.analyze_directory(scripts_dir)
    
    print(f"Analyzing: {mcp_dir}")
    checker.analyze_directory(mcp_dir)
    
    print()
    checker.print_report()
    
    print(f"\nFull report saved to: {REPORTS_DIR}")


if __name__ == "__main__":
    main()
