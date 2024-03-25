{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-unstable") {} }:
# using unstable because the openai package is way too old on the stable branches... 
# could try to figure out how to selectively pull that from unstable in future...
pkgs.mkShellNoCC {
  packages = with pkgs; [
    (python3.withPackages (ps: [
	ps.openai
	ps.psycopg2
	]))
    postgresql
    sqlite
  ];

  PGHOST = "/home/jdd/jems";

  shellHook = ''
    # Create a database with the data stored in the current directory
#    initdb -D .tmp/cooldb

    # Start PostgreSQL running as the current user
    # and with the Unix socket in the current directory
#    pg_ctl -D .tmp/cooldb -l logfile -o "--unix_socket_directories='$PWD'" start

    # create a database
#    createdb cooldb
    echo "hello, nix-shell importing all packages from 'nix-unstable' with python, sqlite3, psycopg2, openai, postgresql and sqlite has begun"
    echo "run the following commands to do the stuff you usually want to do:"
    echo "initdb -D .tmp/cooldb"
    echo "pg_ctl -D .tmp/cooldb -l logfile -o \"--unix_socket_directories='$PWD'\" start"
    echo "createdb -h \"/home/jdd/jems\" cooldb"
    echo "psql -h \"/home/jdd/jems\" cooldb"
    echo "pg_ctl -D .tmp/cooldb stop"
  '';
}
