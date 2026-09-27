-- pylsp only provides hover, definitions and completion; ruff lints.
return {
    settings = {
        pylsp = {
            plugins = {
                pycodestyle = { enabled = false },
                pyflakes = { enabled = false },
                mccabe = { enabled = false },
            }
        }
    }
}
