#!/usr/bin/env bash

git_commit_no_verify() {
    local commit_message="$1"

    git commit -m "$commit_message" --no-verify
}

set_alias() {
    alias blackw=run_ci_python_black_write
    alias eslw=run_ci_vue_eslint_write
    alias isortw=run_ci_python_isort_write
    alias markdownw=run_ci_markdown_write
    alias mdc=run_ci_markdown
    alias prettyw=run_ci_vue_prettier_write
    alias py=python
    alias pyc=run_ci_python
    alias pycov=run_ci_python_test_coverage_py
    alias shc=run_ci_bash
    alias shfmtw=run_ci_bash_shfmt_write
    alias vuec=run_ci_vue
    alias vuecov=run_ci_vue_vitest_coverage
}

main() {
    set_alias
}

main
