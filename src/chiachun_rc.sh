#!/usr/bin/env bash

print_welcome_message() {
    cat <<"EOF"
__      __   _                     ___ _    _         ___ _             
\ \    / /__| |__ ___ _ __  ___   / __| |_ (_)__ _   / __| |_ _  _ _ _  
 \ \/\/ / -_) / _/ _ \ '  \/ -_) | (__| ' \| / _` | | (__| ' \ || | ' \ 
  \_/\_/\___|_\__\___/_|_|_\___|  \___|_||_|_\__,_|  \___|_||_\_,_|_||_|
EOF
}

run_zen_quotes() {
    local py_path
    py_path="$(get_venv_bin_path ~/'repo/_packages')/python"
    local script_path=~/'repo/helper-codes/src/zen_quotes/zen_quotes.py'

    "$py_path" "$script_path"
}

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

source_py_sh() {
    local py_sh_path=~/'repo/helper-codes/git-hooks/src/py.sh'

    if [[ ! -f "$py_sh_path" ]]; then
        echo "$py_sh_path not found"
        return 1
    fi

    # shellcheck source=/dev/null
    source "$py_sh_path"
}

main() {
    echo '##################################################'
    if ! source_py_sh; then
        return 1
    fi

    source_bash_alias
    source_git_hooks_ci

    print_welcome_message
    echo ''
    run_zen_quotes
    echo '##################################################'
}

main
