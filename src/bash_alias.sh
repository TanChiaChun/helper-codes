#!/usr/bin/env bash

git_commit_no_verify() {
    local commit_message="$1"

    git commit -m "$commit_message" --no-verify
}

set_alias() {
    alias blackw=run_ci_python_black_write
    alias isortw=run_ci_python_isort_write
    alias markdownw=run_ci_markdown_write
    alias mdc=run_ci_markdown
    alias py=python
    alias pyc=run_ci_python
    alias shc=run_ci_bash
    alias shfmtw=run_ci_bash_shfmt_write
}

source_git_hooks_ci() {
    if [[ -f './git-hooks/src/ci.sh' ]]; then
        # shellcheck source=/dev/null
        source './git-hooks/src/ci.sh'

        echo 'Loaded git-hooks ci'
    fi
}

main() {
    echo '##################################################'

    set_alias
    source_git_hooks_ci

    echo 'Loaded bash_alias'
    echo '##################################################'
}

main
