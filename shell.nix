{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-unstable") {} }:
# using unstable because the openai package is way too old on the stable branches... 
# could try to figure out how to selectively pull that from unstable in future...
pkgs.mkShellNoCC {
  packages = with pkgs; [
    (python3.withPackages (ps: [
	    ps.openai
	  ]))
    sqlite
  ];

  shellHook = ''
    echo "nix shell running with python, openai and sqlite all from unstable branch"
  '';
}
