vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

vim.opt.number = true
vim.opt.statusline = "%l/%L %f"
vim.opt.clipboard = 'unnamedplus'
vim.opt.expandtab = true
vim.opt.tabstop = 4
vim.opt.list = true
vim.opt.autoindent = true
vim.opt.smartindent = true
vim.opt.listchars:append {
    tab = ">-",
    nbsp = ".",
    trail = "•"
}

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
