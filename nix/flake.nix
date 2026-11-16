# t2-mac-kde user CLI tools (spec nix-user-tools). The deploy copies this file, flake.lock and a
# tools.json rendered from config nix_tools to ~/.local/share/t2-mac-kde/nix/ and installs
# packages.x86_64-linux.default ("t2-tools") into the user's profile. Update: t2-nix-update.
{
  description = "t2-mac-kde user CLI tools";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs = { self, nixpkgs }:
    let
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
      tools = builtins.fromJSON (builtins.readFile ./tools.json);
    in {
      packages.x86_64-linux.default = pkgs.buildEnv {
        name = "t2-tools";
        paths = map (n: pkgs.${n}) tools;
        pathsToLink = [ "/bin" "/share" ];
        extraOutputsToInstall = [ "man" ];
      };
    };
}
