return {
    "nvim-treesitter/nvim-treesitter",
    branch = "main",
    lazy = false,
    build = ":TSUpdate",
    config = function()
        local ensure_installed = {
            "c", "lua", "vim", "vimdoc", "query", "python", "yaml",
            "javascript", "html", "rust", "markdown", "markdown_inline",
        }
        require("nvim-treesitter").install(ensure_installed)

        vim.api.nvim_create_autocmd("FileType", {
            callback = function(args)
                if not pcall(vim.treesitter.start, args.buf) then
                    return
                end
                -- Only take over indenting where an indents.scm query exists;
                -- otherwise leave Nvim's native indent plugin in place.
                local lang = vim.treesitter.language.get_lang(vim.bo[args.buf].filetype)
                if lang and vim.treesitter.query.get(lang, "indents") then
                    vim.bo[args.buf].indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
                end
            end,
        })
    end,
}
