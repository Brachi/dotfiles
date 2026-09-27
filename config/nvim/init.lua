vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

vim.opt.number = true
vim.opt.statusline = "%l/%L %f"
vim.opt.clipboard = 'unnamedplus'
vim.opt.expandtab = true
vim.opt.tabstop = 4
vim.opt.shiftwidth = 0     -- follow tabstop
vim.opt.softtabstop = -1   -- follow shiftwidth
vim.opt.list = true
vim.opt.listchars:append {
    tab = ">-",
    nbsp = ".",
    trail = "•"
}

-- Two-space indent where Nvim's own ftplugins don't already set it
-- (they do for yaml; python, markdown and rust get 4).
vim.api.nvim_create_autocmd("FileType", {
    pattern = { "css", "html", "json" },
    callback = function()
        vim.opt_local.tabstop = 2
    end,
})

-- Show diagnostic messages at the end of the line, not just a sign.
vim.diagnostic.config({ virtual_text = true })

-- Bootstrap lazy.nvim
-- https://lazy.folke.io/installation
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.uv.fs_stat(lazypath) then
  local lazyrepo = "https://github.com/folke/lazy.nvim.git"
  vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
  spec = {
    { import = "plugins" },
  },
  checker = { enabled = true, frequency = 7 * 24 * 3600 },  -- weekly
})

-- Servers come from pacman; nvim-lspconfig provides their configs, and
-- after/lsp/ holds local settings.
vim.lsp.enable({ "lua_ls", "ts_ls", "pylsp", "ruff" })
vim.keymap.set('n', 'gd', vim.lsp.buf.definition)
-- Peek at the definition in a floating window over the real file. q or
-- moving to another window closes it. on_list only runs when a definition
-- was found.
vim.keymap.set('n', '<leader>gd', function()
    vim.lsp.buf.definition({
        on_list = function(list)
            local item = list.items[1]
            local buf = vim.fn.bufadd(item.filename)
            vim.fn.bufload(buf)
            local win = vim.api.nvim_open_win(buf, true, {
                relative = 'cursor', row = 1, col = 0,
                width = math.min(100, vim.o.columns - 4),
                height = math.min(20, vim.o.lines - 6),
                border = 'rounded',
                title = ' ' .. vim.fn.fnamemodify(item.filename, ':~:.') .. ' ',
            })
            vim.api.nvim_win_set_cursor(win, { item.lnum, item.col - 1 })
            vim.cmd('normal! zt')

            -- q is buffer-local, so map it on every buffer the peek shows
            -- (gd inside it loads another) and unmap it when the peek closes.
            local mapped = {}
            local function map_q()
                local b = vim.api.nvim_get_current_buf()
                if not mapped[b] and vim.fn.maparg('q', 'n', false, true).buffer ~= 1 then
                    vim.keymap.set('n', 'q', '<cmd>close<cr>', { buffer = b })
                    mapped[b] = true
                end
            end
            map_q()
            local group = vim.api.nvim_create_augroup('peek', { clear = true })
            vim.api.nvim_create_autocmd('BufWinEnter', {
                group = group,
                callback = function()
                    if vim.api.nvim_get_current_win() == win then map_q() end
                end,
            })
            vim.api.nvim_create_autocmd('WinLeave', {
                group = group,
                callback = function()
                    if vim.api.nvim_get_current_win() ~= win then return end
                    vim.api.nvim_del_augroup_by_id(group)
                    for b in pairs(mapped) do
                        if vim.api.nvim_buf_is_valid(b) then
                            pcall(vim.keymap.del, 'n', 'q', { buffer = b })
                        end
                    end
                    vim.schedule(function() pcall(vim.api.nvim_win_close, win, true) end)
                end,
            })
        end,
    })
end)
