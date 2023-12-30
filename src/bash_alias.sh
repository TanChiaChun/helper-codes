#!/usr/bin/env bash

git_commit_no_verify() {
    local commit_message="$1"

    git commit -m "$commit_message" --no-verify
}

set_alias() {
    alias py=python
}

main() {
    set_alias

    echo '##################################################'
    echo 'Loaded bash_alias'
    echo '##################################################'
}

main
