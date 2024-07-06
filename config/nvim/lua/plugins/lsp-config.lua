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
                ensure_installed = { "lua_ls", "tsserver", "pylsp"}

        })
    end
    },

    {
    "neovim/nvim-lspconfig",
    config = function()
        local lspconfig = require("lspconfig")
        lspconfig.lua_ls.setup{
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
        }
        lspconfig.tsserver.setup({})
        lspconfig.pylsp.setup({
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
        vim.keymap.set('n', 'K', vim.lsp.buf.hover, {})
        vim.keymap.set('n', 'gd', vim.lsp.buf.definition, {})
    end
    },

}
