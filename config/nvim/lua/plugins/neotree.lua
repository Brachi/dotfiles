return {
    "nvim-neo-tree/neo-tree.nvim", branch = "v3.x",
    dependencies = {
        "nvim-lua/plenary.nvim",
        "nvim-tree/nvim-web-devicons",
        "MunifTanjim/nui.nvim",
    },
    lazy = false,
    keys = {
        { "<C-n>", "<cmd>Neotree toggle<cr>" },
    },
    init = function()
        -- Show the tree when started without files (`nvim`), but not when
        -- Neovim is $EDITOR for git commit, crontab and the like. `nvim .`
        -- is covered by neo-tree replacing netrw.
        vim.api.nvim_create_autocmd("VimEnter", {
            callback = function()
                if vim.fn.argc() == 0 and not vim.g.read_from_stdin then
                    vim.cmd("Neotree show")
                end
            end,
        })
        vim.api.nvim_create_autocmd("StdinReadPre", {
            callback = function() vim.g.read_from_stdin = true end,
        })
        -- Trees are per tab; give new tabs one too. Scheduled so the file
        -- being opened lands in its window first.
        vim.api.nvim_create_autocmd("TabNewEntered", {
            callback = function()
                vim.schedule(function() vim.cmd("Neotree show") end)
            end,
        })
    end,
    opts = {
        close_if_last_window = true,
        filesystem = {
            follow_current_file = { enabled = true },
            use_libuv_file_watcher = true,
        },
    },
}
