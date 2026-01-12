#!/bin/bash

. "$HOME/default-env.sh"

run_remove () {
    # conan remove "random123" --confirm
    # conan remove "gurobi" --confirm
    conan remove "ortools" --confirm

    # conan remove "hpc-utils" --confirm

    # conan remove "munge" --confirm
    # conan remove "openpmix" --confirm
    # conan remove "prrte" --confirm
    # conan remove "openucx" --confirm
    # conan remove "openucc" --confirm
    # conan remove "openmpi" --confirm
}

run_install () {
    # conan create -vverbose recipes/openmpi/all/ --version="5.0.9.pci" --options="openmpi/*:cuda=True" --build=missing
    
    # conan create -vverbose recipes/hpc-utils/all/ --version="main" --build=missing
    
    conan create -vverbose recipes/ortools/all/ --version="9.15" --build=missing
}

show_help() {
    echo "Usage: $0 (help | command)"
}

if [[ "$1" == "help" || "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
elif [[ $(type -t "run_${1}") == function ]]; then
    run_${1}
else
    echo "Unknown command: $1"
fi
