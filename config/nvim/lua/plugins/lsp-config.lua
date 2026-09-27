return {
    -- Language servers come from pacman (see os/arch/packages.toml).
    {
    "neovim/nvim-lspconfig",
    config = function()
        vim.lsp.config("lua_ls", {
            settings = {
                Lua = {
                    diagnostics = {
                        globals = {
                            'vim',
                            'require'
                        }
                    }
                }
            }
        })
        -- pylsp only provides hover, definitions and completion; ruff lints.
        vim.lsp.config("pylsp", {
                settings = {
                    pylsp = {
                      plugins = {
                        pycodestyle = { enabled = false },
                        pyflakes = { enabled = false },
                        mccabe = { enabled = false },
                      }
                    }
                }

        })
        vim.lsp.config("ruff", {
            init_options = {
                settings = {
                    lineLength = 110,
                    lint = { extendSelect = { "E", "W" } },
                }
            }
        })
        vim.lsp.enable({ "lua_ls", "ts_ls", "pylsp", "ruff" })
        vim.keymap.set('n', 'K', vim.lsp.buf.hover, {})
        vim.keymap.set('n', 'gd', vim.lsp.buf.definition, {})
    end
    },

}
