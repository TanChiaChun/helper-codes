setup() {
    load '../src/chiachun_rc.sh'
}

@test "source_bash_alias_loaded()" {
    run source_bash_alias '.'
    [ "$status" -eq 0 ]
    [ "$output" == 'Loaded bash_alias' ]
}

@test "source_bash_alias_not_loaded()" {
    run source_bash_alias "$BATS_TMPDIR"
    [ "$status" -eq 0 ]
    [ "$output" == 'bash_alias not loaded' ]
}

@test "source_completion_git()" {
    if [[ "$OSTYPE" == 'darwin'* ]]; then
        echo '# Run: macOS' >&3

        run source_completion_git
        [ "$status" -eq 0 ]
        [ "$output" == 'Loaded Git completion' ]
    else
        echo "# Skip: $OSTYPE" >&3
    fi
}

@test "source_completion_pip()" {
    run source_completion_pip
    [ "$status" -eq 0 ]
    [ "$output" == 'Loaded pip completion' ]
}

@test "source_git_hooks_ci_loaded()" {
    run source_git_hooks_ci
    [ "$status" -eq 0 ]
    [[ "$output" =~ .+'Loaded git-hooks ci' ]]
}

@test "source_git_hooks_ci_not_loaded()" {
    cd "$BATS_TMPDIR"
    run source_git_hooks_ci
    cd "$OLDPWD"
    [ "$status" -eq 0 ]
    [ "$output" == 'git-hooks ci not loaded' ]
}

@test "source_py_sh_not_found()" {
    run source_py_sh "$BATS_TMPDIR"
    [ "$status" -eq 1 ]
    [ "$output" == "$BATS_TMPDIR/git-hooks/src/py.sh not found" ]
}

@test "source_py_sh()" {
    run source_py_sh '.'
    [ "$status" -eq 0 ]
}
