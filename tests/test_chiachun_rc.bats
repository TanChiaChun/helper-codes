setup() {
    load '../src/chiachun_rc.sh'
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

@test "source_completion_git_macos()" {
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
