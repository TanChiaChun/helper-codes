#!/usr/bin/env bash

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
