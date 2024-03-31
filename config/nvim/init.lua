

vim.o.number = true
vim.cmd("colorscheme habamax")
vim.o.statusline = "%l/%L %f"


vim.o.expandtab = true
vim.o.tabstop = 4
vim.o.list = true
vim.opt.listchars:append {
    tab = ">-",
    multispace = space,
    nbsp = ".",
    trail = "•"
}
