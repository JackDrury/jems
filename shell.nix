let
  nixpkgs = fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-unstable";
  # using unstable because the openai package is way too old on the stable branches... 
  # could try to figure out how to selectively pull that from unstable in future...  
  pkgs = import nixpkgs { config = {}; overlays = []; };
in

pkgs.mkShellNoCC {
  packages = with pkgs; [
    (python3.withPackages (ps: [
	    ps.openai
	  ]))
    sqlite
  ];

  IMPORTS = "python, openai, sqlite";

shellHook = ''
    echo "nix shell running with $IMPORTS all from nixos-unstable"
  '';
}
