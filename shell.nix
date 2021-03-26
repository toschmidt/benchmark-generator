with import <nixos> {};

stdenv.mkDerivation {
  name = "benchmark-generator-shell";
  buildInputs = [
    python38Packages.jinja2
    python38Packages.jsonschema
  ];
}
