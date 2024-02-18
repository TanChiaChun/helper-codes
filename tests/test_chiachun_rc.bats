setup() {
    load '../src/chiachun_rc.sh'
    load '../git-hooks/src/helper.sh'
}

@test "set_django_env_var_output_check()" {
    local env_file='./.env'
    local py_dir='./mysite'
    local py_file="$py_dir/manage.py"

    cd "$BATS_TMPDIR"
    echo 'MY_DJANGO_PROJECT=./mysite' >"$env_file"
    mkdir "$py_dir"
    echo 'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")' \
        >"$py_file"
    run set_django_env_var
    rm -r "$py_dir"
    rm "$env_file"
    cd "$OLDPWD"
    [ "$status" -eq 0 ]
    [ "$output" == 'Set DJANGO_SETTINGS_MODULE to mysite.settings' ]
}

@test "set_django_env_var_export_check()" {
    local env_file='./.env'
    local py_dir='./mysite'
    local py_file="$py_dir/manage.py"

    cd "$BATS_TMPDIR"
    echo 'MY_DJANGO_PROJECT=./mysite' >"$env_file"
    mkdir "$py_dir"
    echo 'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")' \
        >"$py_file"
    set_django_env_var
    local export_p
    export_p="$(export -p | grep --max-count=1 'DJANGO_SETTINGS_MODULE')"
    rm -r "$py_dir"
    rm "$env_file"
    cd "$OLDPWD"
    [ "$export_p" == 'declare -x DJANGO_SETTINGS_MODULE="mysite.settings"' ]
}

@test "set_django_env_var_no_env_file()" {
    cd "$BATS_TMPDIR"
    run set_django_env_var
    cd "$OLDPWD"
    [ "$status" -eq 1 ]
}

@test "set_django_env_var_no_env_line()" {
    local env_file='./.env'

    cd "$BATS_TMPDIR"
    echo 'MAY_DJANGO_PROJECT=./mysite' >"$env_file"
    run set_django_env_var
    rm "$env_file"
    cd "$OLDPWD"
    [ "$status" -eq 1 ]
}

@test "set_django_env_var_no_django_env_line()" {
    local env_file='./.env'
    local py_dir='./mysite'
    local py_file="$py_dir/manage.py"

    cd "$BATS_TMPDIR"
    echo 'MY_DJANGO_PROJECT=./mysite' >"$env_file"
    mkdir "$py_dir"
    echo 'os.environ.setdefault("DAJANGO_SETTINGS_MODULE", "mysite.settings")' \
        >"$py_file"
    run set_django_env_var
    rm -r "$py_dir"
    rm "$env_file"
    cd "$OLDPWD"
    [ "$status" -eq 1 ]
}

@test "set_django_env_var_regex_mismatch()" {
    local env_file='./.env'
    local py_dir='./mysite'
    local py_file="$py_dir/manage.py"

    cd "$BATS_TMPDIR"
    echo 'MY_DJANGO_PROJECT=./mysite' >"$env_file"
    mkdir "$py_dir"
    echo 'os.environ.setdefault("DJANGO", "SETTINGS", "mysite.settings")' \
        >"$py_file"
    run set_django_env_var
    rm -r "$py_dir"
    rm "$env_file"
    cd "$OLDPWD"
    [ "$status" -eq 1 ]
}

@test "source_bash_alias_sourced()" {
    run source_bash_alias '.'
    [ "$status" -eq 0 ]
    [ "$output" == 'Sourced bash_alias' ]
}

@test "source_bash_alias_not_sourced()" {
    run source_bash_alias "$BATS_TMPDIR"
    [ "$status" -eq 0 ]
    [ "$output" == 'bash_alias not sourced' ]
}

@test "source_completion_git()" {
    if [[ "$OSTYPE" == 'darwin'* ]]; then
        echo '# Run: macOS' >&3

        run source_completion_git
        [ "$status" -eq 0 ]
        [ "$output" == 'Sourced Git completion' ]
    else
        echo "# Skip: $OSTYPE" >&3
    fi
}

# python expected to be installed by default
@test "source_completion_pip()" {
    run source_completion_pip
    [ "$status" -eq 0 ]
    [ "$output" == 'Sourced pip completion' ]
}

@test "source_git_hooks_ci_sourced()" {
    run source_git_hooks_ci
    [ "$status" -eq 0 ]
    [[ "$output" =~ .+'Sourced git-hooks ci' ]]
}

@test "source_git_hooks_ci_not_sourced()" {
    cd "$BATS_TMPDIR"
    run source_git_hooks_ci
    cd "$OLDPWD"
    [ "$status" -eq 0 ]
    [ "$output" == 'git-hooks ci not sourced' ]
}

@test "source_py_sh()" {
    run source_py_sh '.'
    [ "$status" -eq 0 ]
}

@test "source_py_sh_not_found()" {
    run source_py_sh "$BATS_TMPDIR"
    [ "$status" -eq 1 ]
    [ "$output" == "$BATS_TMPDIR/git-hooks/src/py.sh not found" ]
}
