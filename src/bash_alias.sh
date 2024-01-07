#!/usr/bin/env bash

git_commit_no_verify() {
    local commit_message="$1"

    git commit -m "$commit_message" --no-verify
}

set_alias() {
    alias py=python
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
