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
    local repo_dir="$1"

    if [[ -f "$repo_dir/src/bash_alias.sh" ]]; then
        # shellcheck source=/dev/null
        source "$repo_dir/src/bash_alias.sh"

        echo 'Loaded bash_alias'
    else
        echo 'bash_alias not loaded'
    fi
}

source_completion_git() {
    local git_path
    git_path="$(which git)"
    local git_symlink_path
    git_symlink_path="$(readlink "$git_path")"
    local git_dir="${git_path%/*}/${git_symlink_path%/*}"
    local filename="${git_dir%/*}/share/zsh/site-functions/git-completion.bash"

    if [[ -f "$filename" ]]; then
        # shellcheck source=/dev/null
        source "$filename"

        echo 'Loaded Git completion'
    else
        echo 'Git completion not loaded'
    fi
}

source_completion_pip() {
    local completion

    # shellcheck source=/dev/null
    if completion="$(python -m pip completion --bash)" &&
        source <(echo "$completion"); then
        echo 'Loaded pip completion'
    else
        echo 'pip completion not loaded'
    fi
}

source_git_hooks_ci() {
    if [[ -f './git-hooks/src/ci.sh' ]]; then
        # shellcheck source=/dev/null
        source './git-hooks/src/ci.sh'

        echo 'Loaded git-hooks ci'
    else
        echo 'git-hooks ci not loaded'
    fi
}

source_py_sh() {
    local repo_dir="$1"

    if [[ ! -f "$repo_dir/git-hooks/src/py.sh" ]]; then
        echo "$repo_dir/git-hooks/src/py.sh not found"
        return 1
    fi

    # shellcheck source=/dev/null
    source "$repo_dir/git-hooks/src/py.sh"
}

main() {
    echo '##################################################'
    if ! source_py_sh ~/'repo/helper-codes'; then
        return 1
    fi

    source_bash_alias ~/'repo/helper-codes'
    source_git_hooks_ci

    source_completion_git
    source_completion_pip

    print_welcome_message
    echo ''
    run_zen_quotes
    echo '##################################################'
}

if [[ "$0" != *"bats-core"* ]]; then
    main
fi
