{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "inventory-dev";
  buildInputs = [
    (pkgs.python3.withPackages (ps: [ ps.tkinter ]))
    pkgs.sqlite
    pkgs.git
  ];

  # Nice-to-haves in your shell
  shellHook = ''
    echo "🐍 Inventory dev shell ready. Run: python src/app.py"
  '';
}