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
    },
    -- Use the project's .venv (uv's default) so definitions resolve into its
    -- libraries without activating it first. An activated venv still wins.
    before_init = function(_, config)
        local python = (config.root_dir or "") .. "/.venv/bin/python"
        if not vim.env.VIRTUAL_ENV and vim.uv.fs_stat(python) then
            config.settings.pylsp.plugins.jedi = { environment = python }
        end
    end,
}
