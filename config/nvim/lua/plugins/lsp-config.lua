return {
    {
    "williamboman/mason.nvim",
    config = function()
        require("mason").setup()
    end
    },
    {
    "williamboman/mason-lspconfig.nvim",
    config = function()
        require("mason-lspconfig").setup({
                ensure_installed = { "lua_ls", "ts_ls", "pylsp"},
                -- Servers are enabled explicitly below.
                automatic_enable = false,
        })
    end
    },

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
        vim.lsp.config("pylsp", {
                settings = {
                    pylsp = {
                      plugins = {
                        pyflakes = { enabled = false },
                        pycodestyle = {
                          ignore = {'W391'},
                          maxLineLength = 110
                        }
                      }
                    }
                }

        })
        vim.lsp.enable({ "lua_ls", "ts_ls", "pylsp" })
        vim.keymap.set('n', 'K', vim.lsp.buf.hover, {})
        vim.keymap.set('n', 'gd', vim.lsp.buf.definition, {})
    end
    },

}
