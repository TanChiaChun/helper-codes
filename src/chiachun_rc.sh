#!/usr/bin/env bash

source_bash_alias() {
    if [[ -f ~/'repo/helper-codes/src/bash_alias.sh' ]]; then
        # shellcheck source=/dev/null
        source ~/'repo/helper-codes/src/bash_alias.sh'

        echo 'Loaded bash_alias'
    fi
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
    source_bash_alias
    source_git_hooks_ci
    echo '##################################################'
}

main
