{
  description = "Octelly's shell utilities";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; })
          mkPoetryApplication;
      in with pkgs; {
        packages = {
          octelly-shell-utils = mkPoetryApplication { projectDir = self; };
          default = self.packages.${system}.octelly-shell-utils;
        };
        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.octelly-shell-utils ];
          packages = [ pkgs.poetry ];
        };
      });
}
