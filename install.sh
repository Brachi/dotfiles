#!/usr/bin/bash

# https://stackoverflow.com/a/246128
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

SRC_XDG_CONFIG="$SCRIPT_DIR/config"
DST_XDG_CONFIG=$HOME/.config/

ln -fs "$SRC_XDG_CONFIG/alacritty" $DST_XDG_CONFIG
ln -fs "$SRC_XDG_CONFIG/nvim" $DST_XDG_CONFIG
ln -fs "$SRC_XDG_CONFIG/ranger" $DST_XDG_CONFIG
ln -fs "$SRC_XDG_CONFIG/tmux" $DST_XDG_CONFIG


ln -fs "$SRC_XDG_CONFIG/bash/bash_aliases" $HOME/.bash_aliases
ln -fs "$SRC_XDG_CONFIG/bash/bashrc" $HOME/.bashrc
ln -fs "$SRC_XDG_CONFIG/bash/bash_profile" $HOME/.bash_profile
