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
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local lazyrepo = "https://github.com/folke/lazy.nvim.git"
  vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
  spec = {
    { import = "plugins" },
  },
  checker = { enabled = true },
})
