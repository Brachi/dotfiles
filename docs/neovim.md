# Neovim maintenance

Plugins are managed by lazy.nvim and pinned in `config/nvim/lazy-lock.json`. Language servers come from pacman (`os/arch/packages.toml`), not Mason.

## After pulling lockfile changes

Plugins don't follow the lockfile on their own. Run:

```
:Lazy restore
```

Then check `git diff config/nvim/lazy-lock.json`. If lazy had to clone a missing plugin, it may have rewritten the lockfile from the old checkouts. In that case, `git checkout` the lockfile and run `:Lazy restore` again. Never commit that diff.

## Updating plugins

When the weekly update notification appears:

1. `:Lazy update`
2. Open a few files (Python, Lua, Markdown) and check for errors.
3. Commit `lazy-lock.json`.

To undo a bad update, revert the lockfile and run `:Lazy restore`.

## After a Neovim minor upgrade

When pacman moves Neovim to a new minor version (0.12 to 0.13), update plugins right away, even without a notification. Stale plugins break against new Neovim APIs.
