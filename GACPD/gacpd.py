import argparse, os, locale, pathlib, sys
from GACPD.GACPD import  GACPD


def main():
    parser = argparse.ArgumentParser(description="GACPD Command Line Call For UI Connectivity")

    # Add arguments
    parser.add_argument("-p", "--parent", type=str, required=True, help="Parent Branch Name. Ex: apache/kafka")
    parser.add_argument("-d", "--divergent", type=str, required=True, help="Divergent Branch Name. Ex: linkedin/kafka")
    parser.add_argument("-sd", "--start-date", type=str, required=True, help="ISO DateTime of Initial Check Date")
    parser.add_argument("-ed", "--end-date", type=str, required=True, help="ISO DateTime of Ending Check Date")
    parser.add_argument("-n", "--name", type=str, required=True, help="ISO DateTime of Ending Check Date")

    # Parse arguments
    args = parser.parse_args()

    token_list = []
    token_file = 'tokens.txt'

    if not os.path.exists("reports"):
        os.mkdir("reports")

    if not os.path.exists("src"):
        os.mkdir("src")

    if not os.path.exists("cmp"):
        os.mkdir("cmp")

    with open(token_file, 'r') as f:
        for line in f.readlines():
            token_list.append(line.strip('\n'))
    data = (args.name, args.parent, args.divergent, token_list, '', '')

    # Access arguments
    example = GACPD(data)
    example.get_dates()

    prs_source = example.extractPatches(args.start_date, args.end_date)
    example.dfPatches()
    example.runClassification(prs_source)

    for i in range(0, len(example.cycles)):
        print(example.cycles[i])


if __name__ == "__main__":
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception as e:
        print(e)
        exit(0)

    main()
