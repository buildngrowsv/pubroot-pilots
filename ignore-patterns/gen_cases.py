#!/usr/bin/env python3
"""Generate pattern files and a shared path universe for gitignore vs dockerignore."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "cases")
os.makedirs(CASES, exist_ok=True)

# Documented semantic differences + common agent patterns
PATTERNS = {
  "unanchored_nm": "node_modules\n",
  "anchored_nm": "/node_modules\n",
  "star_nm": "*/node_modules\n",
  "globstar_nm": "**/node_modules\n",
  "unanchored_env": ".env\n",
  "anchored_env": "/.env\n",
  "dir_only_build": "build/\n",
  "negation_under_star": "*\n!keep.txt\n!src/\n!src/**\n",
  "negation_under_dir": "dist\n!dist/keep.js\n",
  "leading_slash_foo": "/foo\n",
  "no_slash_foo": "foo\n",
  "double_star_log": "**/*.log\n",
  "star_log": "*.log\n",
  "question": "temp?\n",
  "bracket": "file[0-9].txt\n",
  "space_name": "my file.txt\n",
  "comment_and_blank": "# ignore\n\n*.tmp\n",
  "nested_git_style": "a/b\n",
  "escape_bang": "\\!important\n",
  "root_dotgit": ".git\n",
  "pycache": "__pycache__/\n",
  "venv": ".venv\n",
  "complex_js": "node_modules\ndist\n*.log\n.env\n!.env.example\ncoverage\n",
}

# Path universe (relative, forward slashes). is_dir flagged for tools that care.
PATHS = [
  ("node_modules", True),
  ("node_modules/pkg/index.js", False),
  ("src/node_modules/x.js", False),
  ("apps/web/node_modules/y.js", False),
  (".env", False),
  ("config/.env", False),
  ("build", True),
  ("build/out.js", False),
  ("src/build/out.js", False),
  ("keep.txt", False),
  ("src/keep.txt", False),
  ("src/main.py", False),
  ("dist", True),
  ("dist/keep.js", False),
  ("dist/app.js", False),
  ("foo", False),
  ("bar/foo", False),
  ("foo/bar", False),
  ("debug.log", False),
  ("logs/debug.log", False),
  ("temp1", False),
  ("temp12", False),
  ("file3.txt", False),
  ("my file.txt", False),
  ("x.tmp", False),
  ("a/b", False),
  ("a/b/c", False),
  ("!important", False),
  (".git", True),
  (".git/config", False),
  ("src/__pycache__", True),
  ("src/__pycache__/x.pyc", False),
  (".venv", True),
  (".venv/bin/python", False),
  (".env.example", False),
  ("coverage", True),
  ("coverage/lcov.info", False),
]

for name, body in PATTERNS.items():
    open(os.path.join(CASES, f"{name}.ignore"), "w").write(body)

meta = {"n_patterns": len(PATTERNS), "n_paths": len(PATHS), "paths": PATHS, "pattern_names": list(PATTERNS)}
json.dump(meta, open(os.path.join(CASES, "meta.json"), "w"), indent=2)
print(f"wrote {len(PATTERNS)} pattern files, {len(PATHS)} paths")
