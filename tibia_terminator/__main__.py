from argparse import ArgumentParser
import tibia_terminator.main as start

if __name__ == "__main__":
    parser = ArgumentParser(description='Main Tibia Terminator Entry-Point')
    subparsers = parser.add_subparsers(
        title="Tibia Terminator Commands", dest="command", required=True
    )
    run_terminator_parser = subparsers.add_parser("start", help="Run the Tibia Terminator")
    known, other_args = parser.parse_known_args()

    if known.command == "start":
        main_parser = start.build_parser()
        start.main(main_parser.parse_args(other_args))