from __future__ import annotations

from pathlib import Path

import typer


def _bash_completion() -> str:
    return '''_vibecode_completion() {
    local IFS=$'\\n'
    local response
    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD="$COMP_CWORD" _VIBECODE_COMPLETE=bash_complete vibecode)
    for completion in $response; do
        IFS=',' read type value <<< "$completion"
        if [[ $type == 'dir' ]]; then
            COMPREPLY=()
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMPREPLY=()
            compopt -o default
        else
            COMPREPLY+=("$value")
        fi
    done
    return 0
}

complete -F _vibecode_completion -o default vibecode
'''


def _zsh_completion() -> str:
    return '''#compdef vibecode

_vibecode_completion() {
    local -a completions
    local -a descriptions
    local -a response
    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD="$(($#words-1))" _VIBECODE_COMPLETE=zsh_complete vibecode)}")

    for key descr in ${(kv)response}; do
        completions+=("$key")
        descriptions+=("$descr")
    done

    compadd -d descriptions -a completions
}

compdef _vibecode_completion vibecode
'''


def _powershell_completion() -> str:
    return '''Register-ArgumentCompleter -Native -CommandName vibecode -ScriptBlock {
    param($commandName, $wordToComplete, $cursorPosition)
    $env:COMP_WORDS=$wordToComplete
    $env:COMP_CWORD=$cursorPosition
    $results = Invoke-Expression "& vibecode _complete $wordToComplete"
    $results | ForEach-Object {
        $parts = $_ -split ','
        if ($parts[0] -eq 'dir') {
            _cdExpansion $wordToComplete
        } elseif ($parts[0] -eq 'file') {
            _pathExpansion $wordToComplete
        } else {
            [System.Management.Automation.CompletionResult]::new($parts[1], $parts[1], 'ParameterValue', $parts[1])
        }
    }
}
'''


SHELL_MAP = {
    "bash": (_bash_completion, "~/.bashrc"),
    "zsh": (_zsh_completion, "~/.zshrc"),
    "powershell": (_powershell_completion, "$PROFILE"),
}


def generate_completion(shell: str) -> str:
    shell = shell.lower()
    if shell not in SHELL_MAP:
        supported = ", ".join(SHELL_MAP.keys())
        raise ValueError(f"Unsupported shell: {shell}. Supported: {supported}")
    return SHELL_MAP[shell][0]()


def install_completion(shell: str) -> Path | None:
    shell = shell.lower()
    if shell not in SHELL_MAP:
        supported = ", ".join(SHELL_MAP.keys())
        typer.echo(f"Unsupported shell: {shell}. Supported: {supported}")
        return None

    script = generate_completion(shell)
    config_hint = SHELL_MAP[shell][1]

    if shell == "powershell":
        typer.echo("PowerShell completion script:")
        typer.echo(script)
        typer.echo(f"Add the above to your PowerShell profile: {config_hint}")
        return None

    config_path = Path(config_hint).expanduser()
    marker = "# vibecode completion"
    existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    if marker in existing:
        typer.echo(f"Completion already installed in {config_path}")
        return config_path

    with open(config_path, "a", encoding="utf-8") as f:
        f.write(f"\n{marker}\n")
        f.write(script)
        f.write(f"# end vibecode completion\n")

    typer.echo(f"Completion installed in {config_path}")
    return config_path
