setup() {
    load '../src/chiachun_rc.sh'
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

@test "update_path_macos()" {
    if [[ "$OSTYPE" == 'darwin'* ]]; then
        echo '# Run: macOS' >&3

        local old_path="$PATH"
        update_path
        [ "$PATH" != "$old_path" ]
        [[ "$PATH" =~ .+'/libexec/bin' ]]
    else
        echo "# Skip: $OSTYPE" >&3
    fi
}
