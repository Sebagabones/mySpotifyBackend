{
  description = "Spotify API devshell";

  inputs = { nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; };

  outputs = { self, nixpkgs }:
    let
      pkgs = import nixpkgs { system = "x86_64-linux"; };
      # Need to build one package from scratch
      falcon-limiter = pkgs.python3Packages.buildPythonPackage rec {
        pname = "falcon-limiter";
        version = "1.0.1";
        pyproject = true;

        src = pkgs.fetchFromGitHub {
          owner = "Sebagabones";
          repo = "${pname}";
          rev = "30efc9eddbdf45263bef63e829de17b28acbc1d5";
          hash = "sha256-7ZgYX5DZanb+YQZhzzksMOCj8NVXtTLHArJFsOpAHyg=";
        };

        dependencies = with pkgs.python3Packages; [ falcon limits ];
        # build-inputs = with pkgs.python3Packages; [ flit-core ];
        # do not run tests
        doCheck = false;

        # specific to buildPythonPackage, see its reference
        build-system = with pkgs.python3Packages; [
          hatch-vcs
          hatchling
        ];
      };
    in {
      devShells.x86_64-linux.default = pkgs.mkShell rec {
        nativeBuildInputs = with pkgs; [
          uv
          ruff
          (python313.withPackages (ps:
            with ps; [
              certifi
              charset-normalizer
              click
              deprecated
              falcon
              falcon-limiter
              h11
              idna
              limits
              packaging
              python-dotenv
              requests
              typing-extensions
              urllib3
              uvicorn
              wrapt
            ]))
        ];

        shellHook = ''
          export PYTHONPATH=$(pwd)
        '';
      };
    };
}
