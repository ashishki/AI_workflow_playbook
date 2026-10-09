import argparse
from src.common.jsonio import read, render
from src.pipeline import replay

def main():
    parser = argparse.ArgumentParser(description='Local deterministic fulfillment replay')
    parser.add_argument('input')
    args = parser.parse_args()
    print(render(replay(read(args.input))))

if __name__ == '__main__':
    main()
